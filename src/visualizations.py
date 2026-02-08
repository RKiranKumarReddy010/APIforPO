"""
Visualization Module
Creates charts and visualizations for the Streamlit dashboard.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Optional, Dict


class InventoryVisualizer:
    """Creates interactive visualizations for inventory analysis."""
    
    @staticmethod
    def plot_demand_distribution(df_sku_stats: pd.DataFrame, 
                                 top_n: int = 20) -> go.Figure:
        """
        Plot demand distribution for top N keys.
        
        Args:
            df_sku_stats: DataFrame with key statistics
            top_n: Number of top keys to display
            
        Returns:
            Plotly figure
        """
        # Get top N keys by total demand
        df_top = df_sku_stats.nlargest(top_n, 'total_demand').copy()
        df_top = df_top.sort_values('avg_daily_demand', ascending=True)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_top['key'].astype(str),
            x=df_top['avg_daily_demand'],
            orientation='h',
            marker=dict(
                color=df_top['cv_demand'],
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="CV")
            ),
            text=df_top['avg_daily_demand'].round(1),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>' +
                         'Avg Daily Demand: %{x:.1f}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Top {top_n} Keys by Average Daily Demand",
            xaxis_title="Average Daily Demand (Units)",
            yaxis_title="Key",
            height=max(400, top_n * 25),
            showlegend=False,
            template='plotly_white'
        )
        
        return fig
        
    @staticmethod
    def plot_safety_stock_breakdown(df_sku_stats: pd.DataFrame,
                                    top_n: int = 20) -> go.Figure:
        """
        Plot safety stock vs average demand for top keys.
        
        Args:
            df_sku_stats: DataFrame with safety stock calculations
            top_n: Number of keys to display
            
        Returns:
            Plotly figure
        """
        df_top = df_sku_stats.nlargest(top_n, 'total_demand').copy()
        df_top = df_top.sort_values('safety_stock', ascending=True)
        
        fig = go.Figure()
        
        # Average daily demand
        fig.add_trace(go.Bar(
            name='Avg Daily Demand',
            y=df_top['key'].astype(str),
            x=df_top['avg_daily_demand'],
            orientation='h',
            marker=dict(color='#3498db')
        ))
        
        # Safety stock
        fig.add_trace(go.Bar(
            name='Safety Stock',
            y=df_top['key'].astype(str),
            x=df_top['safety_stock'],
            orientation='h',
            marker=dict(color='#e74c3c')
        ))
        
        fig.update_layout(
            title=f"Safety Stock vs Average Demand (Top {top_n} Keys)",
            xaxis_title="Units",
            yaxis_title="Key",
            barmode='group',
            height=max(400, top_n * 30),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            template='plotly_white'
        )
        
        return fig
        
    @staticmethod
    def plot_inventory_simulation(df_simulation: pd.DataFrame,
                                  sku_id: str) -> go.Figure:
        """
        Plot inventory simulation for a single key.
        
        Args:
            df_simulation: Simulation results DataFrame
            sku_id: Key to visualize
            
        Returns:
            Plotly figure
        """
        df_sku = df_simulation[df_simulation['key'] == sku_id].copy()
        
        fig = go.Figure()
        
        # Ending inventory
        fig.add_trace(go.Scatter(
            x=df_sku['date'],
            y=df_sku['ending_inventory'],
            mode='lines',
            name='Inventory Level',
            line=dict(color='#2ecc71', width=2),
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.1)'
        ))
        
        # Net inventory (for forecast-based simulation)
        if 'net_inventory' in df_sku.columns:
            fig.add_trace(go.Scatter(
                x=df_sku['date'],
                y=df_sku['net_inventory'],
                mode='lines',
                name='Net Inventory',
                line=dict(color='#3498db', width=1.5, dash='dashdot'),
                opacity=0.7
            ))
        
        # Safety stock line
        if 'safety_stock' in df_sku.columns:
            fig.add_trace(go.Scatter(
                x=df_sku['date'],
                y=df_sku['safety_stock'],
                mode='lines',
                name='Safety Stock',
                line=dict(color='#f39c12', width=2, dash='dash')
            ))
        
        # ROP line
        if 'rop' in df_sku.columns:
            fig.add_trace(go.Scatter(
                x=df_sku['date'],
                y=df_sku['rop'],
                mode='lines',
                name='Reorder Point',
                line=dict(color='#e74c3c', width=2, dash='dot')
            ))
        elif 'reorder_point' in df_sku.columns:
            fig.add_trace(go.Scatter(
                x=df_sku['date'],
                y=df_sku['reorder_point'],
                mode='lines',
                name='Reorder Point',
                line=dict(color='#e74c3c', width=2, dash='dot')
            ))
        
        # Mark order placements
        df_orders = df_sku[df_sku['order_placed'] == True]
        if len(df_orders) > 0:
            fig.add_trace(go.Scatter(
                x=df_orders['date'],
                y=df_orders['ending_inventory'],
                mode='markers',
                name='Order Placed',
                marker=dict(color='#9b59b6', size=10, symbol='diamond')
            ))
        
        # Mark stockouts
        df_stockouts = df_sku[df_sku['stockout'] == 1]
        if len(df_stockouts) > 0:
            fig.add_trace(go.Scatter(
                x=df_stockouts['date'],
                y=df_stockouts['ending_inventory'],
                mode='markers',
                name='Stockout',
                marker=dict(color='#c0392b', size=12, symbol='x')
            ))
        
        fig.update_layout(
            title=f"90-Day Inventory Simulation: {sku_id}",
            xaxis_title="Date",
            yaxis_title="Units",
            hovermode='x unified',
            height=500,
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        return fig
        
    @staticmethod
    def plot_simulation_summary(df_simulation: pd.DataFrame) -> go.Figure:
        """
        Plot summary metrics across all keys.
        
        Args:
            df_simulation: Combined simulation results
            
        Returns:
            Plotly figure
        """
        # Calculate metrics per key
        metrics = df_simulation.groupby('key').agg({
            'stockout': 'sum',
            'order_placed': 'sum',
            'ending_inventory': 'mean'
        }).reset_index()
        
        metrics.columns = ['key', 'Total Stockouts', 'Total Orders', 'Avg Inventory']
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('Stockout Frequency', 'Order Frequency', 'Average Inventory'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Stockouts
        df_stockouts = metrics.nlargest(10, 'Total Stockouts')
        fig.add_trace(
            go.Bar(x=df_stockouts['key'].astype(str), 
                  y=df_stockouts['Total Stockouts'],
                  marker=dict(color='#e74c3c'),
                  name='Stockouts'),
            row=1, col=1
        )
        
        # Orders
        df_orders = metrics.nlargest(10, 'Total Orders')
        fig.add_trace(
            go.Bar(x=df_orders['key'].astype(str), 
                  y=df_orders['Total Orders'],
                  marker=dict(color='#3498db'),
                  name='Orders'),
            row=1, col=2
        )
        
        # Average inventory
        df_inv = metrics.nlargest(10, 'Avg Inventory')
        fig.add_trace(
            go.Bar(x=df_inv['key'].astype(str), 
                  y=df_inv['Avg Inventory'],
                  marker=dict(color='#2ecc71'),
                  name='Avg Inventory'),
            row=1, col=3
        )
        
        fig.update_xaxes(tickangle=-45)
        fig.update_layout(
            height=400,
            showlegend=False,
            template='plotly_white',
            title_text="Simulation Summary (Top 10 Keys)"
        )
        
        return fig
        
    @staticmethod
    def plot_weekly_demand_trend(df_weekly: pd.DataFrame, 
                                 sku_id: str) -> go.Figure:
        """
        Plot weekly demand trend for a key.
        
        Args:
            df_weekly: Weekly aggregated data
            sku_id: Key to visualize
            
        Returns:
            Plotly figure
        """
        df_sku = df_weekly[df_weekly['key'] == sku_id].copy()
        df_sku = df_sku.sort_values('week_start')
        
        fig = go.Figure()
        
        # Weekly demand
        fig.add_trace(go.Scatter(
            x=df_sku['week_start'],
            y=df_sku['Offtake_Units'],
            mode='lines+markers',
            name='Weekly Demand',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6)
        ))
        
        # Add mean line
        mean_demand = df_sku['Offtake_Units'].mean()
        fig.add_hline(
            y=mean_demand,
            line_dash="dash",
            line_color="#e74c3c",
            annotation_text=f"Mean: {mean_demand:.1f}",
            annotation_position="right"
        )
        
        fig.update_layout(
            title=f"Weekly Demand Trend: {sku_id}",
            xaxis_title="Week",
            yaxis_title="Offtake Units",
            hovermode='x unified',
            height=400,
            template='plotly_white'
        )
        
        return fig
        
    @staticmethod
    def create_metrics_cards(df_sku_stats: pd.DataFrame,
                            df_simulation: Optional[pd.DataFrame] = None) -> Dict:
        """
        Create summary metrics for dashboard cards.
        
        Args:
            df_sku_stats: Key statistics DataFrame
            df_simulation: Optional simulation results
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'total_skus': len(df_sku_stats),
            'total_weekly_demand': df_sku_stats['total_demand'].sum(),
            'avg_safety_stock': df_sku_stats['safety_stock'].mean(),
            'total_safety_stock': df_sku_stats['safety_stock'].sum(),
            'high_variability_skus': (df_sku_stats['cv_demand'] > 0.5).sum(),
            'avg_cv': df_sku_stats['cv_demand'].mean()
        }
        
        if df_simulation is not None:
            sim_metrics = df_simulation.groupby('key').agg({
                'stockout': 'sum',
                'order_placed': 'sum'
            })
            
            metrics['total_stockouts'] = sim_metrics['stockout'].sum()
            metrics['skus_with_stockouts'] = (sim_metrics['stockout'] > 0).sum()
            metrics['total_orders'] = sim_metrics['order_placed'].sum()
            metrics['avg_orders_per_sku'] = sim_metrics['order_placed'].mean()
        
        return metrics
        
    @staticmethod
    def plot_cv_distribution(df_sku_stats: pd.DataFrame) -> go.Figure:
        """
        Plot coefficient of variation distribution.
        
        Args:
            df_sku_stats: Key statistics DataFrame
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df_sku_stats['cv_demand'],
            nbinsx=30,
            marker=dict(color='#3498db', line=dict(color='white', width=1)),
            hovertemplate='CV Range: %{x}<br>Count: %{y}<extra></extra>'
        ))
        
        # Add vertical lines for interpretation
        fig.add_vline(x=0.25, line_dash="dash", line_color="green", 
                     annotation_text="Low variability", annotation_position="top")
        fig.add_vline(x=0.5, line_dash="dash", line_color="orange",
                     annotation_text="Moderate", annotation_position="top")
        fig.add_vline(x=0.75, line_dash="dash", line_color="red",
                     annotation_text="High variability", annotation_position="top")
        
        fig.update_layout(
            title="Coefficient of Variation Distribution",
            xaxis_title="CV (σ/μ)",
            yaxis_title="Number of SKUs",
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def plot_offtake_trends(df_monthly: pd.DataFrame,
                           selected_keys: Optional[List[str]] = None,
                           max_keys: int = 10) -> go.Figure:
        """
        Plot offtake trends over time for selected keys.
        
        Args:
            df_monthly: DataFrame with monthly data (must have 'month_start', 'key', 'Offtake_Units')
            selected_keys: List of keys to display (None for top keys by demand)
            max_keys: Maximum number of keys to display if selected_keys is None
            
        Returns:
            Plotly figure
        """
        df = df_monthly.copy()
        
        # Use month_start column (or date if it exists)
        date_col = 'month_start' if 'month_start' in df.columns else 'date'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # If no keys selected, get top keys by total demand
        if selected_keys is None or len(selected_keys) == 0:
            top_keys = df.groupby('key')['Offtake_Units'].sum().nlargest(max_keys).index.tolist()
            selected_keys = top_keys
        
        # Filter to selected keys only
        df_filtered = df[df['key'].isin(selected_keys)].copy()
        
        if len(df_filtered) == 0:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for selected keys",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(height=500, template='plotly_white')
            return fig
        
        # Create line chart
        fig = go.Figure()
        
        # Get unique color for each key
        colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set2
        
        for idx, key in enumerate(sorted(selected_keys)):
            key_data = df_filtered[df_filtered['key'] == key].sort_values(date_col)
            
            if len(key_data) > 0:
                fig.add_trace(go.Scatter(
                    x=key_data[date_col],
                    y=key_data['Offtake_Units'],
                    mode='lines+markers',
                    name=str(key),
                    line=dict(width=2, color=colors[idx % len(colors)]),
                    marker=dict(size=6),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Date: %{x|%b %Y}<br>' +
                                 'Offtake: %{y:,.0f} units<br>' +
                                 '<extra></extra>'
                ))
        
        fig.update_layout(
            title=f"Offtake Trends - {len(selected_keys)} Key(s)",
            xaxis_title="Month",
            yaxis_title="Offtake Units",
            height=500,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            margin=dict(r=150)  # More space for legend
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
