"""
Streamlit Dashboard for Inventory Planning
Dynamic Safety Stock and 90-Day Inventory Simulation
Backtest Period: November 2025 - January 2026
Uses weekly weight-based disaggregation from typical_month.csv
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from src.data_validator import validate_dataset
from src.data_processor import DataProcessor
from src.inventory_calculator import (
    SafetyStockCalculator, 
    InventorySimulator,
    calculate_inventory_metrics
)
from src.visualizations import InventoryVisualizer
from config.config import (
    DEFAULT_SERVICE_LEVEL, 
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_COVERAGE_DAYS,
    DEFAULT_CASE_PACK,
    SERVICE_LEVELS
)

# Page configuration
st.set_page_config(
    page_title="Inventory Planning Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
    }
    .stAlert > div {
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'data_uploaded' not in st.session_state:
        st.session_state.data_uploaded = False
    if 'validation_complete' not in st.session_state:
        st.session_state.validation_complete = False
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'calculation_complete' not in st.session_state:
        st.session_state.calculation_complete = False
    if 'simulation_complete' not in st.session_state:
        st.session_state.simulation_complete = False
    # Track parameters for change detection
    if 'last_params' not in st.session_state:
        st.session_state.last_params = {}


def main():
    """Main application function."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">📦 Inventory Planning Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Dynamic Safety Stock & 90-Day Simulation</div>', unsafe_allow_html=True)
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Service Level
        service_level_pct = st.selectbox(
            "Service Level",
            options=[90.0, 95.0, 97.5, 99.0, 99.5],
            index=2,
            help="Target service level for safety stock calculation"
        )
        service_level = service_level_pct / 100
        
        # Lead Time
        lead_time_days = st.number_input(
            "Average Lead Time (days)",
            min_value=1,
            max_value=90,
            value=DEFAULT_LEAD_TIME_DAYS,
            help="Time from placing order until it arrives (used in ROP and total order quantity)"
        )
        
        lead_time_std = st.number_input(
            "Lead Time Std Dev (days)",
            min_value=0.0,
            max_value=30.0,
            value=2.0,
            step=0.5,
            help="Variability in lead time"
        )
        
        # Coverage Days
        coverage_days = st.number_input(
            "Coverage Days",
            min_value=7,
            max_value=90,
            value=DEFAULT_COVERAGE_DAYS,
            help="Additional days of demand to cover after order arrives (total order = lead time + coverage)"
        )
        
        # Case Pack
        case_pack = st.number_input(
            "Case Pack Size",
            min_value=1,
            max_value=1000,
            value=DEFAULT_CASE_PACK,
            help="Units per case (for order rounding)"
        )
        
        # Simulation Parameters
        st.header("📊 Simulation Settings")
        
        simulation_days = st.number_input(
            "Simulation Days",
            min_value=30,
            max_value=180,
            value=90,
            help="Number of days to simulate"
        )
        
        initial_inv_multiplier = st.slider(
            "Initial Inventory (× Avg Daily Demand)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.5,
            help="Starting inventory level"
        )
        
        # Check if parameters changed - invalidate calculations
        current_params = {
            'service_level': service_level,
            'lead_time_days': lead_time_days,
            'lead_time_std': lead_time_std,
            'coverage_days': coverage_days,
            'case_pack': case_pack
        }
        
        if st.session_state.last_params != current_params:
            # Parameters changed - invalidate calculations
            if st.session_state.last_params:  # Only if not first run
                st.session_state.calculation_complete = False
                st.session_state.simulation_complete = False
            st.session_state.last_params = current_params
        
        # Show warning if parameters changed
        if not st.session_state.calculation_complete and st.session_state.processing_complete:
            st.warning("⚠️ Parameters changed. Please recalculate safety stock.")
    
    # Main Content Area
    tabs = st.tabs(["📁 Data Upload", "✅ Validation", "📊 Analysis", "🎯 Safety Stock", "📈 Simulation", "� Primary Data", "�📥 Export"])
    
    # TAB 1: Data Upload
    with tabs[0]:
        st.header("Upload Dataset")
        
        uploaded_file = st.file_uploader(
            "Upload your inventory dataset (CSV or Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="Dataset should contain date, key, and Offtake_Units columns"
        )
        
        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith('.csv'):
                    df_raw = pd.read_csv(uploaded_file)
                else:
                    # Read Excel file - use Sheet1
                    df_raw = pd.read_excel(uploaded_file, sheet_name='Sheet1')
                
                st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
                st.info(f"Dataset shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
                
                # Store in session state
                st.session_state.df_raw = df_raw
                st.session_state.data_uploaded = True
                
                # Show preview
                with st.expander("📋 Data Preview"):
                    st.dataframe(df_raw.head(20), width='stretch')
                    
                # Show column info
                with st.expander("📊 Column Information"):
                    col_info = pd.DataFrame({
                        'Column': df_raw.columns,
                        'Type': df_raw.dtypes.astype(str),
                        'Non-Null Count': df_raw.count(),
                        'Null Count': df_raw.isnull().sum(),
                        'Null %': (df_raw.isnull().sum() / len(df_raw) * 100).round(2)
                    })
                    st.dataframe(col_info, width='stretch')
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
        else:
            st.info("👆 Please upload a dataset to begin")
    
    # TAB 2: Validation
    with tabs[1]:
        st.header("Data Quality Validation")
        
        if not st.session_state.data_uploaded:
            st.warning("⚠️ Please upload data in the 'Data Upload' tab first")
        else:
            if st.button("🔍 Run Validation", type="primary"):
                with st.spinner("Validating dataset..."):
                    # Run validation
                    report = validate_dataset(st.session_state.df_raw)
                    st.session_state.validation_report = report
                    st.session_state.validation_complete = True
            
            if st.session_state.validation_complete:
                report = st.session_state.validation_report
                
                # Status indicator
                if report.is_valid:
                    st.success("✅ Dataset passed validation!")
                else:
                    st.error("❌ Dataset has critical issues")
                
                # Display errors
                if report.errors:
                    st.error("**Critical Errors:**")
                    for error in report.errors:
                        st.markdown(f"- ❌ {error}")
                
                # Display warnings
                if report.warnings:
                    with st.expander("⚠️ Warnings", expanded=True):
                        for warning in report.warnings:
                            st.markdown(f"- ⚠️ {warning}")
                
                # Display info
                if report.info:
                    with st.expander("ℹ️ Information"):
                        for info in report.info:
                            st.markdown(f"- ℹ️ {info}")
                
                # Detailed issues
                if report.data_quality_issues:
                    with st.expander("🔍 Detailed Quality Issues"):
                        st.json(report.data_quality_issues)
    
    # TAB 3: Analysis
    with tabs[2]:
        st.header("Data Processing & Analysis")
        
        if not st.session_state.data_uploaded:
            st.warning("⚠️ Please upload data first")
        else:
            if st.button("🔄 Process Data", type="primary"):
                with st.spinner("Processing data..."):
                    try:
                        # Initialize processor
                        processor = DataProcessor(st.session_state.df_raw)
                        
                        # Process data: Monthly -> Weekly -> Daily statistics
                        df_clean = processor.process_all()
                        df_monthly = processor.aggregate_to_monthly()
                        df_weekly = processor.aggregate_to_weekly()
                        df_sku_stats = processor.calculate_sku_statistics()
                        
                        # Store in session state
                        st.session_state.df_clean = df_clean
                        st.session_state.df_monthly = df_monthly
                        st.session_state.df_weekly = df_weekly
                        st.session_state.df_sku_stats = df_sku_stats
                        st.session_state.processor = processor
                        st.session_state.processing_complete = True
                        
                        st.success("✅ Data processing complete! (Monthly → Weekly → Daily analysis)")
                        
                    except Exception as e:
                        st.error(f"❌ Error during processing: {str(e)}")
            
            if st.session_state.processing_complete:
                # Processing log
                with st.expander("📋 Processing Log"):
                    for log_entry in st.session_state.processor.get_processing_log():
                        st.text(log_entry)
                
                # Summary statistics
                st.subheader("📊 Summary Statistics")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Keys", f"{len(st.session_state.df_sku_stats):,}")
                
                with col2:
                    total_demand = st.session_state.df_sku_stats['total_demand'].sum()
                    st.metric("Total Demand", f"{total_demand:,.0f}")
                
                with col3:
                    avg_months = st.session_state.df_sku_stats['total_months'].mean()
                    st.metric("Avg Months/Key", f"{avg_months:.1f}")
                
                with col4:
                    avg_weeks = st.session_state.df_sku_stats['total_weeks'].mean()
                    st.metric("Avg Weeks/Key", f"{avg_weeks:.1f}")
                
                with col5:
                    avg_cv = st.session_state.df_sku_stats['cv_demand'].mean()
                    st.metric("Avg CV", f"{avg_cv:.2f}")
                
                # Visualizations
                st.subheader("📈 Demand Analysis")
                
                viz = InventoryVisualizer()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_demand = viz.plot_demand_distribution(st.session_state.df_sku_stats, top_n=20)
                    st.plotly_chart(fig_demand, width='stretch')
                
                with col2:
                    fig_cv = viz.plot_cv_distribution(st.session_state.df_sku_stats)
                    st.plotly_chart(fig_cv, width='stretch')
                
                # Offtake Trends
                st.subheader("📈 Offtake Trends by Key")
                
                # Get all unique keys
                all_keys = sorted(st.session_state.df_monthly['key'].unique())
                
                # Key selector
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_keys = st.multiselect(
                        "Select keys to display (leave empty for top 10 by demand)",
                        options=all_keys,
                        default=None,
                        help="Choose specific keys or leave empty to show top 10 by demand"
                    )
                
                with col2:
                    max_keys = st.number_input(
                        "Max keys if auto-select",
                        min_value=1,
                        max_value=50,
                        value=10,
                        help="Maximum number of keys to show when auto-selecting"
                    )
                
                # Plot offtake trends
                fig_trends = viz.plot_offtake_trends(
                    st.session_state.df_monthly,
                    selected_keys=selected_keys if selected_keys else None,
                    max_keys=max_keys
                )
                st.plotly_chart(fig_trends, width='stretch')
                
                # SKU Statistics Table
                with st.expander("📊 Key Statistics Table"):
                    # Convert any datetime columns to string to avoid Arrow serialization issues
                    display_stats = st.session_state.df_sku_stats.copy()
                    for col in display_stats.columns:
                        if display_stats[col].dtype == 'object':
                            try:
                                if pd.api.types.is_datetime64_any_dtype(pd.to_datetime(display_stats[col], errors='coerce')):
                                    display_stats[col] = display_stats[col].astype(str)
                            except:
                                pass
                    
                    st.dataframe(
                        display_stats.sort_values('total_demand', ascending=False),
                        width='stretch'
                    )
    
    # TAB 4: Safety Stock Calculation
    with tabs[3]:
        st.header("Safety Stock Calculation")
        
        if not st.session_state.processing_complete:
            st.warning("⚠️ Please process data in the 'Analysis' tab first")
        else:
            if st.button("🎯 Calculate Safety Stock", type="primary"):
                with st.spinner("Calculating safety stock..."):
                    try:
                        # Calculate safety stock and ROP
                        df_inventory = calculate_inventory_metrics(
                            st.session_state.df_sku_stats,
                            service_level=service_level,
                            lead_time_days=lead_time_days,
                            lead_time_std=lead_time_std
                        )
                        
                        st.session_state.df_inventory = df_inventory
                        st.session_state.calculation_complete = True
                        
                        st.success("✅ Safety stock calculated successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error calculating safety stock: {str(e)}")
            
            if st.session_state.calculation_complete:
                df_inv = st.session_state.df_inventory
                
                # Summary metrics
                st.subheader("📊 Safety Stock Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Service Level", f"{service_level*100:.1f}%")
                
                with col2:
                    total_ss = df_inv['safety_stock'].sum()
                    st.metric("Total Safety Stock", f"{total_ss:,.0f}")
                
                with col3:
                    avg_ss = df_inv['safety_stock'].mean()
                    st.metric("Avg Safety Stock/SKU", f"{avg_ss:.1f}")
                
                with col4:
                    avg_rop = df_inv['reorder_point'].mean()
                    st.metric("Avg Reorder Point", f"{avg_rop:.1f}")
                
                # Visualizations
                st.subheader("📊 Safety Stock Analysis")
                
                viz = InventoryVisualizer()
                fig_ss = viz.plot_safety_stock_breakdown(df_inv, top_n=20)
                st.plotly_chart(fig_ss, use_container_width=True)
                
                # Results table
                st.subheader("📋 Safety Stock & ROP Results")
                
                display_cols = [
                    'key', 'avg_daily_demand', 'std_daily_demand', 'sigma_demand',
                    'safety_stock', 'reorder_point', 'cv_demand', 'service_level'
                ]
                
                st.dataframe(
                    df_inv[display_cols].sort_values('safety_stock', ascending=False),
                    width='stretch'
                )
    
    # TAB 5: Simulation
    with tabs[4]:
        st.header("90-Day Inventory Simulation (Nov-Dec-Jan Forecast)")
        
        if not st.session_state.calculation_complete:
            st.warning("⚠️ Please calculate safety stock first")
        else:
            st.info("📅 Using actual Nov 2025, Dec 2025, Jan 2026 daily forecast data (Offtake_Units) for simulation")
            
            if st.button("🚀 Run Simulation with Nov-Dec-Jan Data", type="primary"):
                with st.spinner("Running simulation with actual forecast data..."):
                    try:
                        # Initialize simulator
                        simulator = InventorySimulator(
                            lead_time_days=lead_time_days,
                            coverage_days=coverage_days,
                            case_pack=case_pack
                        )
                        
                        # Run simulation with actual Nov-Dec-Jan forecast data
                        df_simulation = simulator.simulate_with_february_forecast(
                            df_clean=st.session_state.df_clean,
                            df_inventory=st.session_state.df_inventory,
                            initial_inventory_multiplier=initial_inv_multiplier
                        )
                        
                        st.session_state.df_simulation = df_simulation
                        st.session_state.simulation_complete = True
                        
                        # Calculate actual simulation days from results
                        actual_days = df_simulation.groupby('key')['date'].nunique().mean()
                        st.success(f"✅ Simulation complete! {len(df_simulation)} rows, {actual_days:.0f} avg days per key")
                        
                    except Exception as e:
                        st.error(f"❌ Error running simulation: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            
            if st.session_state.simulation_complete:
                df_sim = st.session_state.df_simulation
                
                # Summary metrics
                st.subheader("📊 Simulation Summary")
                
                total_stockouts = df_sim['stockout'].sum() if 'stockout' in df_sim.columns else 0
                total_orders = df_sim['reorder_point'].sum() if 'reorder_point' in df_sim.columns else 0
                avg_inventory = df_sim['inventory'].mean() if 'inventory' in df_sim.columns else 0
                skus_with_stockouts = df_sim.groupby('key')['stockout'].sum().gt(0).sum() if 'stockout' in df_sim.columns else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Stockouts", f"{total_stockouts:,}")
                
                with col2:
                    st.metric("Keys with Stockouts", f"{skus_with_stockouts:,}")
                
                with col3:
                    st.metric("Total Orders Placed", f"{total_orders:,}")
                
                with col4:
                    st.metric("Avg Inventory", f"{avg_inventory:,.0f}")
                
                # Simulation summary chart (limited to top 10 keys to avoid performance issues)
                # Use checkbox to control rendering
                show_overview = st.checkbox("📊 Show Simulation Overview Chart (Top 10 Keys)", value=False)
                
                if show_overview:
                    st.subheader("📊 Simulation Overview (Top 10 Keys by Demand)")
                    
                    # Calculate total demand per key and get top 10
                    top_keys = df_sim.groupby('key')['daily_offtake_forecast'].sum().nlargest(10).index
                    df_sim_top = df_sim[df_sim['key'].isin(top_keys)]
                    
                    viz = InventoryVisualizer()
                    fig_summary = viz.plot_simulation_summary(df_sim_top)
                    st.plotly_chart(fig_summary, width='stretch')
                    
                    with st.expander("ℹ️ Why only top 10 keys?"):
                        st.info("Displaying all keys would slow down the dashboard. Use the key-specific analysis below to view any individual key.")
                
                # SKU-specific analysis
                st.subheader("🔍 Key-Specific Simulation (Excel Format)")
                
                sku_list = sorted(df_sim['key'].unique())
                selected_sku = st.selectbox("Select Key to analyze:", sku_list, key='sim_sku_select')
                
                if selected_sku:
                    # Get SKU data first (lightweight operation)
                    sku_data = df_sim[df_sim['key'] == selected_sku].copy()
                    
                    # Detailed metrics for selected SKU
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        stockouts = sku_data['stockout'].sum() if 'stockout' in sku_data.columns else 0
                        st.metric("Stockout Days", f"{stockouts}")
                    
                    with col2:
                        orders = sku_data['reorder_point'].sum() if 'reorder_point' in sku_data.columns else 0
                        st.metric("Orders Placed", f"{orders}")
                    
                    with col3:
                        avg_inv = sku_data['inventory'].mean() if 'inventory' in sku_data.columns else 0
                        st.metric("Avg Inventory", f"{avg_inv:.1f}")
                    
                    with col4:
                        total_days = len(sku_data)
                        stockouts = sku_data['stockout'].sum() if 'stockout' in sku_data.columns else 0
                        service_level_achieved = ((total_days - stockouts) / total_days * 100) if total_days > 0 else 0
                        st.metric("Service Level Achieved", f"{service_level_achieved:.1f}%")
                    
                    # Show chart only if user wants it
                    show_chart = st.checkbox(f"📈 Show Inventory Chart for {selected_sku}", value=False)
                    if show_chart:
                        viz = InventoryVisualizer()
                        fig_sim = viz.plot_inventory_simulation(df_sim, selected_sku)
                        st.plotly_chart(fig_sim, width='stretch')
                    
                    # Simulation detail table (Excel format - EXACT columns only)
                    st.subheader("📋 Detailed Simulation Log")
                    
                    # Excel column order
                    excel_cols = ['date', 's_no', 'inventory', 'inventory_received', 
                                 'daily_offtake_forecast', 'net_inventory', 
                                 'reorder_point', 'reorder_quantity']
                    
                    # Check which columns exist
                    available_cols = [col for col in excel_cols if col in sku_data.columns]
                    
                    if len(available_cols) > 0:
                        display_df = sku_data[available_cols].copy()
                        # Format date
                        if 'date' in display_df.columns:
                            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%m/%d/%Y')
                        
                        # Limit display to avoid freezing (show all rows but with pagination)
                        st.dataframe(display_df, width='stretch', height=400, hide_index=True)
                        
                        # Download option for full data
                        csv_sku = display_df.to_csv(index=False)
                        st.download_button(
                            label=f"📥 Download {selected_sku} Simulation Data",
                            data=csv_sku,
                            file_name=f"simulation_{selected_sku}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("⚠️ No simulation data columns found")
                        st.write("Available columns:", list(sku_data.columns))
                        st.dataframe(sku_data.head(10), width='stretch')
    
    # TAB 6: Primary Data
    with tabs[5]:
        st.header("Primary Data - Monthly View & Alerts")
        
        if not st.session_state.simulation_complete:
            st.warning("⚠️ Please run the simulation in the 'Simulation' tab first")
        else:
            df_sim = st.session_state.df_simulation
            df_inv = st.session_state.df_inventory
            
            # Create monthly aggregation for reorder quantities and offtake
            df_sim['date'] = pd.to_datetime(df_sim['date'])
            df_sim['year_month'] = df_sim['date'].dt.to_period('M')
            
            # Monthly reorder quantities (Primary)
            # Use 'reorder_quantity' or 'order_qty' (both exist in simulation output)
            monthly_reorder = df_sim.groupby(['year_month', 'key']).agg({
                'reorder_quantity': 'sum',
                'daily_forecast': 'sum'
            }).reset_index()
            monthly_reorder.columns = ['Month', 'Key', 'Primary_Units', 'Offtake_Units']
            monthly_reorder['Month'] = monthly_reorder['Month'].astype(str)
            
            # Pivot for display
            pivot_reorder = monthly_reorder.pivot(index='Month', columns='Key', values='Primary_Units').fillna(0)
            pivot_offtake = monthly_reorder.pivot(index='Month', columns='Key', values='Offtake_Units').fillna(0)
            
            # Chart: Offtake vs Primary - Always show, with key filter
            st.subheader("📊 Monthly Offtake vs Primary Comparison")
            
            with st.spinner("Loading chart data..."):
                # Optimization: Use monthly aggregated data instead of df_clean to avoid processing 8,780+ rows
                if hasattr(st.session_state, 'df_monthly') and st.session_state.df_monthly is not None:
                    # Use pre-aggregated monthly data (much faster!)
                    df_monthly = st.session_state.df_monthly.copy()
                    df_monthly['year_month'] = df_monthly['month_start'].dt.to_period('M').astype(str)
                    
                    # Get unique keys for filter
                    all_keys = sorted(df_monthly['key'].unique())
                    
                    # Key filter dropdown
                    selected_keys = st.multiselect(
                        "Filter by Key (leave empty for all keys aggregated)",
                        options=all_keys,
                        default=None,
                        help="Select specific keys to view individually, or leave empty to see total across all keys"
                    )
                    
                    # Filter by selected keys if any
                    if selected_keys and len(selected_keys) > 0:
                        df_monthly_filtered = df_monthly[df_monthly['key'].isin(selected_keys)]
                        filter_label = f" ({len(selected_keys)} key(s))"
                    else:
                        df_monthly_filtered = df_monthly
                        filter_label = " (All Keys)"
                    
                    # Aggregate historical offtake by month (use all available history)
                    historical_offtake = df_monthly_filtered.groupby('year_month').agg({
                        'Offtake_Units': 'sum'
                    }).reset_index()
                    historical_offtake.columns = ['Month', 'Offtake_Units']
                else:
                    # Fallback to simulation data only
                    selected_keys = []
                    filter_label = ""
                    historical_offtake = monthly_reorder.groupby('Month').agg({
                        'Offtake_Units': 'sum'
                    }).reset_index()
                
                # Aggregate primary (reorders) by month from simulation
                if selected_keys and len(selected_keys) > 0:
                    primary_monthly = monthly_reorder[monthly_reorder['Key'].isin(selected_keys)].groupby('Month').agg({
                        'Primary_Units': 'sum'
                    }).reset_index()
                else:
                    primary_monthly = monthly_reorder.groupby('Month').agg({
                        'Primary_Units': 'sum'
                    }).reset_index()
                
                # Merge offtake and primary
                monthly_comparison = historical_offtake.merge(
                    primary_monthly, 
                    on='Month', 
                    how='outer'
                ).fillna(0)
                
                # Sort by month
                monthly_comparison = monthly_comparison.sort_values('Month')
                
                # Show info about data range
                st.info(f"ℹ️ Showing data from {monthly_comparison['Month'].min()} to {monthly_comparison['Month'].max()} ({len(monthly_comparison)} months){filter_label}")
                
                # Convert month strings to more readable format (MMM YYYY)
                try:
                    monthly_comparison['Month_Label'] = pd.to_datetime(monthly_comparison['Month'] + '-01').dt.strftime('%b %Y')
                except:
                    monthly_comparison['Month_Label'] = monthly_comparison['Month']
                
                # Filter Primary data to only show Nov 2025, Dec 2025, Jan 2026
                simulation_months = ['2025-11', '2025-12', '2026-01']
                primary_data = monthly_comparison[monthly_comparison['Month'].isin(simulation_months)].copy()
                
                import plotly.graph_objects as go
                fig_monthly = go.Figure()
                
                # Add Offtake line (all months - full history)
                fig_monthly.add_trace(go.Scatter(
                    x=monthly_comparison['Month_Label'],
                    y=monthly_comparison['Offtake_Units'],
                    mode='lines+markers',
                    name='Offtake (Historical)',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Offtake: %{y:,.0f}<extra></extra>'
                ))
                
                # Add Primary line (only simulation months: Nov, Dec, Jan)
                if len(primary_data) > 0:
                    fig_monthly.add_trace(go.Scatter(
                        x=primary_data['Month_Label'],
                        y=primary_data['Primary_Units'],
                        mode='lines+markers',
                        name='Primary (Reorders)',
                        line=dict(color='#e74c3c', width=3),
                        marker=dict(size=10, symbol='diamond'),
                        hovertemplate='<b>%{x}</b><br>Primary: %{y:,.0f}<extra></extra>'
                    ))
                
                # Determine tick spacing based on number of months
                num_months = len(monthly_comparison)
                dtick = 2 if num_months > 8 else 1
                
                fig_monthly.update_layout(
                    title=f"Monthly Offtake vs Primary Units{filter_label}",
                    xaxis_title="Month",
                    yaxis_title="Units",
                    hovermode='x unified',
                    height=500,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis=dict(
                        tickangle=-60,
                        dtick=dtick,
                        showgrid=True,
                        automargin=True
                    ),
                    yaxis=dict(
                        tickformat=',.0f',
                        separatethousands=True,
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='LightGray'
                    ),
                    plot_bgcolor='white',
                    margin=dict(b=120, l=80, r=40, t=60)
                )
                st.plotly_chart(fig_monthly, width='stretch')
            
            # Monthly Reorder Table
            st.subheader("📋 Monthly Reorder Quantities by Key")
            
            # Show summary first
            total_keys = pivot_reorder.shape[1]
            st.info(f"📊 Total: {pivot_reorder.shape[0]} months × {total_keys} keys")
            
            # Limit display if too many columns
            if total_keys > 20:
                st.warning(f"⚠️ Large dataset ({total_keys} keys). Showing first 20 keys. Download full data below.")
                display_pivot = pivot_reorder.iloc[:, :20]
            else:
                display_pivot = pivot_reorder
            
            st.dataframe(display_pivot, width='stretch', height=300)
            
            # Download full table
            csv_reorder = pivot_reorder.to_csv()
            st.download_button(
                label="📥 Download Full Monthly Reorder Table",
                data=csv_reorder,
                file_name="monthly_reorder_quantities.csv",
                mime="text/csv"
            )
            
            # Alerts System
            st.subheader("🚨 Inventory Alerts - Next Critical Points")
            
            # The simulation output already contains 'safety_stock' column
            # No need to merge - it's already in df_sim
            df_alerts = df_sim.copy()
            df_alerts['date'] = pd.to_datetime(df_alerts['date'])
            
            # Get current date for filtering future alerts
            from datetime import datetime
            current_date = datetime.now()
            
            # Calculate alert conditions
            df_alerts['alert_type'] = 'Normal'
            df_alerts.loc[df_alerts['net_inventory'] < (0.5 * df_alerts['safety_stock']), 'alert_type'] = '🔴 Critical'
            df_alerts.loc[
                (df_alerts['net_inventory'] >= (0.5 * df_alerts['safety_stock'])) & 
                (df_alerts['net_inventory'] < (0.75 * df_alerts['safety_stock'])),
                'alert_type'
            ] = '🟡 Warning'
            df_alerts.loc[df_alerts['net_inventory'] > (2.0 * df_alerts['safety_stock']), 'alert_type'] = '🔵 Over-Inventory'
            
            # Filter for future dates only and non-normal alerts
            future_alerts = df_alerts[
                (df_alerts['date'] >= current_date) & 
                (df_alerts['alert_type'] != 'Normal')
            ].copy()
            
            # For each key and alert type, get only the FIRST (next) occurrence
            next_alerts = []
            for key_id in future_alerts['key'].unique():
                key_data = future_alerts[future_alerts['key'] == key_id].sort_values('date')
                
                # Get next critical alert
                critical = key_data[key_data['alert_type'] == '🔴 Critical']
                if len(critical) > 0:
                    next_alerts.append(critical.iloc[0])
                
                # Get next warning alert
                warning = key_data[key_data['alert_type'] == '🟡 Warning']
                if len(warning) > 0:
                    next_alerts.append(warning.iloc[0])
                
                # Get next over-inventory alert
                over_inv = key_data[key_data['alert_type'] == '🔵 Over-Inventory']
                if len(over_inv) > 0:
                    next_alerts.append(over_inv.iloc[0])
            
            if len(next_alerts) > 0:
                alerts_only = pd.DataFrame(next_alerts)
            else:
                alerts_only = pd.DataFrame()
            
            if len(alerts_only) > 0:
                # Group by alert type
                alert_summary = alerts_only.groupby('alert_type').agg({
                    'key': 'count'
                }).reset_index()
                alert_summary.columns = ['Alert Type', 'Count']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    critical_count = len(alerts_only[alerts_only['alert_type'] == '🔴 Critical'])
                    st.metric("Critical Alerts", critical_count, 
                             delta=f"< 50% Safety Stock", delta_color="inverse")
                
                with col2:
                    warning_count = len(alerts_only[alerts_only['alert_type'] == '🟡 Warning'])
                    st.metric("Warning Alerts", warning_count,
                             delta=f"< 75% Safety Stock", delta_color="inverse")
                
                with col3:
                    over_inv_count = len(alerts_only[alerts_only['alert_type'] == '🔵 Over-Inventory'])
                    st.metric("Over-Inventory", over_inv_count,
                             delta=f"> 200% Safety Stock", delta_color="normal")
                
                with col4:
                    keys_monitored = alerts_only['key'].nunique()
                    total_keys = df_sim['key'].nunique()
                    st.metric("Keys at Risk", keys_monitored,
                             delta=f"out of {total_keys} total", delta_color="off")
                
                # Detailed alert table
                st.subheader("📋 Next Alert Points by Key")
                st.info("ℹ️ Showing the NEXT occurrence of each alert type for each key (future dates only)")
                
                # Format alert details
                alert_details = alerts_only[[
                    'date', 'key', 'net_inventory', 'safety_stock', 'alert_type'
                ]].copy()
                
                # Ensure date is datetime type for calculations
                alert_details['date'] = pd.to_datetime(alert_details['date'])
                alert_details['net_inventory'] = alert_details['net_inventory'].round(0)
                alert_details['safety_stock'] = alert_details['safety_stock'].round(0)
                
                # Calculate % of Safety Stock with better handling for negative inventory
                def calculate_ss_percentage(row):
                    net_inv = row['net_inventory']
                    ss = row['safety_stock']
                    if ss == 0:
                        return 0
                    pct = (net_inv / ss) * 100
                    # For negative inventory (stockout), show as shortage
                    if net_inv < 0:
                        return pct  # Keep negative to show severity
                    return pct
                
                alert_details['% of SS'] = alert_details.apply(calculate_ss_percentage, axis=1).round(1)
                
                # Add shortage column for clarity
                alert_details['Shortage'] = alert_details.apply(
                    lambda row: abs(row['net_inventory']) if row['net_inventory'] < 0 else 0, 
                    axis=1
                )
                
                # Add days until alert column (before converting date to string)
                alert_details['Days Until'] = (alert_details['date'] - current_date).dt.days
                
                # Now convert date to string for display
                alert_details['date'] = alert_details['date'].dt.strftime('%Y-%m-%d')
                
                # Sort by date (nearest first) then alert type
                alert_details = alert_details.sort_values(['date', 'alert_type'])
                alert_details.columns = ['Date', 'Key', 'Net Inventory', 'Safety Stock', 'Alert Type', '% of SS', 'Units Short', 'Days Until Alert']
                
                # Show warning if too many alerts
                st.info(f"📊 Found {len(alert_details)} upcoming alert points across {alert_details['Key'].nunique()} keys")
                
                # Limit display to top 100 most imminent alerts
                if len(alert_details) > 100:
                    st.warning(f"⚠️ Showing 100 most imminent alerts (out of {len(alert_details):,} total). Download CSV for full data.")
                    display_alerts = alert_details.head(100)
                else:
                    display_alerts = alert_details
                
                st.dataframe(display_alerts, width='stretch', height=400, hide_index=True)
                
                # Export alerts
                csv_alerts = alert_details.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Alert Report",
                    data=csv_alerts,
                    file_name="upcoming_inventory_alerts.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ No upcoming alerts - all inventory levels projected to remain within normal range")
    
    # TAB 7: Export
    with tabs[6]:
        st.header("Export Results")
        
        if st.session_state.processing_complete:
            st.subheader("📥 Download Processed Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Weekly demand
                csv_weekly = st.session_state.df_weekly.to_csv(index=False)
                st.download_button(
                    label="📊 Weekly Demand Data",
                    data=csv_weekly,
                    file_name="weekly_demand.csv",
                    mime="text/csv"
                )
            
            with col2:
                # SKU statistics
                csv_stats = st.session_state.df_sku_stats.to_csv(index=False)
                st.download_button(
                    label="📈 Key Statistics",
                    data=csv_stats,
                    file_name="key_statistics.csv",
                    mime="text/csv"
                )
            
            if st.session_state.calculation_complete:
                with col3:
                    # Safety stock results
                    csv_inventory = st.session_state.df_inventory.to_csv(index=False)
                    st.download_button(
                        label="🎯 Safety Stock & ROP",
                        data=csv_inventory,
                        file_name="safety_stock_results.csv",
                        mime="text/csv"
                    )
            
            if st.session_state.simulation_complete:
                st.subheader("📥 Download Simulation Results")
                
                csv_simulation = st.session_state.df_simulation.to_csv(index=False)
                st.download_button(
                    label="📈 90-Day Simulation Results",
                    data=csv_simulation,
                    file_name="simulation_results.csv",
                    mime="text/csv"
                )
        else:
            st.info("ℹ️ Process data to enable exports")


if __name__ == "__main__":
    main()
