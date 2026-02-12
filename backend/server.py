"""
Flask Backend Server for Inventory Planning Dashboard
Provides REST API endpoints for inventory calculations and data processing
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from werkzeug.utils import secure_filename

# Add src and config directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from src.data_validator import validate_dataset
from src.data_processor import DataProcessor
from src.inventory_calculator import (
    SafetyStockCalculator,
    ReorderPointCalculator,
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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

import logging

# Configure logging
logging.basicConfig(
    filename='server_error.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_for_json(obj):
    """
    Recursively clean object for JSON serialization.
    - Handles NaN/Inf -> None
    - Handles datetime/Timestamp -> ISO string
    - Handles numpy types -> native python types
    """
    if obj is None:
        return None
    elif isinstance(obj, (pd.Timestamp, datetime, np.datetime64)):
        return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (float, int)):
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj
    elif isinstance(obj, dict):
        return {str(k): clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif hasattr(obj, 'tolist'): # Handle numpy arrays/series
        return clean_for_json(obj.tolist())
    return str(obj) if not isinstance(obj, (bool, str)) else obj


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Inventory Planning Server is running',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get default configuration values"""
    return jsonify({
        'default_service_level': DEFAULT_SERVICE_LEVEL,
        'default_lead_time_days': DEFAULT_LEAD_TIME_DAYS,
        'default_coverage_days': DEFAULT_COVERAGE_DAYS,
        'default_case_pack': DEFAULT_CASE_PACK,
        'available_service_levels': SERVICE_LEVELS
    }), 200


# ============================================================================
# DATA UPLOAD & VALIDATION ENDPOINTS
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload and process data file
    Expected: CSV or Excel file with inventory data
    Returns: Data summary and validation status
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read file
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        # Validate dataset
        validation_result = validate_dataset(df)

        # Prepare preview data (first 20 rows)
        preview_df = df.head(20)
        preview_data = preview_df.to_dict('records')

        # Prepare column information
        column_info = []
        for col in df.columns:
            column_info.append({
                'name': col,
                'type': str(df[col].dtype),
                'non_null_count': int(df[col].count()),
                'null_count': int(df[col].isnull().sum()),
                'null_percentage': round(df[col].isnull().sum() / len(df) * 100, 2)
            })

        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'columns': df.columns.tolist(),
            'preview_data': clean_for_json(preview_data),
            'column_info': clean_for_json(column_info),
            'validation': clean_for_json(validation_result.to_dict() if hasattr(validation_result, 'to_dict') else validation_result),
            'rows': len(df),
            'columns_count': len(df.columns)
        }), 200

    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def validate_data():
    """
    Validate uploaded data file
    Expected JSON: {'filepath': 'path/to/file.csv'}
    Returns: Validation report
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read and validate
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        validation_result = validate_dataset(df)

        return jsonify({
            'success': True,
            'filepath': filepath,
            'validation': validation_result.to_dict() if hasattr(validation_result, 'to_dict') else validation_result,
            'data_summary': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'dtypes': df.dtypes.astype(str).to_dict(),
                'missing_values': df.isnull().sum().to_dict()
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Internal Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DATA PROCESSING ENDPOINTS
# ============================================================================

@app.route('/api/process-data', methods=['POST'])
def process_data():
    """
    Process raw data file
    Expected JSON: {'filepath': 'path/to/file.csv'}
    Returns: Processed data statistics
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read file
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        # Process data
        processor = DataProcessor(df)
        processed_df = processor.process_all()

        # Calculate statistics
        # Use simplejson or manual cleaning to handle NaNs
        desc = processed_df.describe().to_dict()

        stats = {
            'original_rows': len(df),
            'processed_rows': len(processed_df),
            'columns': processed_df.columns.tolist(),
            'summary_statistics': clean_for_json(desc),
            'sku_ids': processed_df['key'].unique().tolist() if 'key' in processed_df.columns else []
        }

        return jsonify({
            'success': True,
            'message': 'Data processed successfully',
            'statistics': clean_for_json(stats)
        }), 200

    except Exception as e:
        app.logger.error(f"Internal Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-charts', methods=['POST'])
def get_charts():
    """
    Get chart data for visualizations
    Expected JSON: {'filepath': 'path/to/file.csv'}
    Returns: Chart data for Plotly
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read file
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        # Process data
        processor = DataProcessor(df)
        processed_df = processor.process_all()
        df_monthly = processor.aggregate_to_monthly()
        df_weekly = processor.aggregate_to_weekly()
        df_sku_stats = processor.calculate_sku_statistics()

        # Create visualizer
        viz = InventoryVisualizer()

        # Calculate default SS/ROP for immediate display
        ss_calc = SafetyStockCalculator(service_level=0.95)
        rop_calc = ReorderPointCalculator()
        
        default_ss = []
        default_rop = []
        current_stock = []
        
        for _, row in df_sku_stats.iterrows():
            try:
                mean = row.get('avg_daily_demand', 0)
                std = row.get('std_dev_demand', 0)
                
                ss = ss_calc.calculate_safety_stock(mean, std, lead_time_days=7)
                rop = rop_calc.calculate_reorder_point(mean, ss, lead_time_days=7)
                
                default_ss.append(ss)
                default_rop.append(rop)
                
                # Mock Current Stock for Alerts Demo (since real stock column isn't standardized yet)
                # Create a distribution: some critical (<50% ROP), some warning (50-100%), some healthy (>100%)
                # We use random factors to simulate this variance for the UI demonstration
                stock_factor = np.random.uniform(0.1, 2.5) 
                sim_stock = rop * stock_factor
                current_stock.append(int(sim_stock))
            except:
                default_ss.append(0)
                default_rop.append(0)
                current_stock.append(0)
                
        df_sku_stats['safety_stock'] = default_ss
        df_sku_stats['reorder_point'] = default_rop
        df_sku_stats['current_stock'] = current_stock

        # Generate charts
        fig_demand = viz.plot_demand_distribution(df_sku_stats, top_n=20)
        fig_cv = viz.plot_cv_distribution(df_sku_stats)
        fig_trends = viz.plot_offtake_trends(df_monthly, max_keys=10)

        # Convert figures to JSON
        charts = {
            'demand_distribution': fig_demand.to_json(),
            'cv_distribution': fig_cv.to_json(),
            'offtake_trends': fig_trends.to_json(),
            'sku_stats': df_sku_stats.head(2000).to_dict('records'),
            'monthly_data': df_monthly.to_dict('records') # Send full monthly data for client-side filtering
        }

        return jsonify({
            'success': True,
            'charts': clean_for_json(charts)
        }), 200

    except Exception as e:
        app.logger.error(f"Chart generation error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500



# ============================================================================
# SAFETY STOCK CALCULATION ENDPOINTS
# ============================================================================

@app.route('/api/calculate-safety-stock', methods=['POST'])
def calculate_safety_stock():
    """
    Calculate safety stock for given parameters
    Expected JSON:
    {
        'filepath': 'path/to/file.csv',
        'sku_id': 'SKU123',
        'service_level': 0.975,
        'lead_time_days': 7,
        'lead_time_std': 1.5
    }
    Returns: Safety stock value and related metrics
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        sku_id = data.get('sku_id')
        service_level = data.get('service_level', DEFAULT_SERVICE_LEVEL)
        lead_time_days = data.get('lead_time_days', DEFAULT_LEAD_TIME_DAYS)
        lead_time_std = data.get('lead_time_std', 1.5)

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read and process data
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        processor = DataProcessor(df)
        processed_df = processor.process_all()

        # Filter by SKU
        if sku_id:
            sku_data = processed_df[processed_df['key'] == sku_id] if 'key' in processed_df.columns else (processed_df[processed_df['SKU ID'] == sku_id] if 'SKU ID' in processed_df.columns else pd.DataFrame())
        else:
            sku_data = processed_df

        if sku_data.empty:
            return jsonify({'error': f'No data found for SKU: {sku_id}'}), 404

        # Calculate safety stock
        calculator = SafetyStockCalculator(
            service_level=service_level,
            lead_time_days=lead_time_days,
            lead_time_std=lead_time_std
        )

        # Extract demand data
        # Find demand column
        demand_cols = ['Units/Qty', 'Offtake_Units', 'Offtake Units', 'Sales', 'Demand', 'Qty']
        demand_col = next((c for c in demand_cols if c in sku_data.columns), None)

        if not demand_col:
            # Filter for any numeric column as fallback
            numeric_cols = sku_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                demand_col = numeric_cols[0]

        if not demand_col:
            return jsonify({'error': 'No numeric demand column found'}), 400
        demand_data = sku_data[demand_col].dropna().values

        if len(demand_data) == 0:
            return jsonify({'error': 'No demand data available'}), 400

        # Calculate metrics
        demand_mean = np.mean(demand_data)
        demand_std = np.std(demand_data)

        # Calculate safety stock
        safety_stock = calculator.calculate_safety_stock(
            avg_daily_demand=demand_mean,
            sigma_demand=demand_std
        )

        return jsonify({
            'success': True,
            'safety_stock': float(safety_stock),
            'sku_id': sku_id,
            'service_level': service_level,
            'lead_time_days': lead_time_days,
            'demand_mean': float(demand_mean),
            'demand_std': float(demand_std),
            'demand_count': len(demand_data),
            'calculation_date': datetime.now().isoformat()
        }), 200

    except Exception as e:
        app.logger.error(f"Internal Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# INVENTORY SIMULATION ENDPOINTS
# ============================================================================

@app.route('/api/simulate-inventory', methods=['POST'])
def simulate_inventory():
    """
    Simulate inventory for 90 days
    Expected JSON:
    {
        'filepath': 'path/to/file.csv',
        'sku_id': 'SKU123',
        'initial_inventory': 100,
        'reorder_point': 50,
        'service_level': 0.975,
        'lead_time_days': 7,
        'coverage_days': 30,
        'case_pack': 10,
        'simulation_days': 90
    }
    Returns: Simulation results and metrics
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        sku_id = data.get('sku_id')
        initial_inventory = data.get('initial_inventory', 100)
        reorder_point = data.get('reorder_point', 50)
        safety_stock_param = data.get('safety_stock') # Added safety_stock support
        service_level = data.get('service_level', DEFAULT_SERVICE_LEVEL)
        lead_time_days = data.get('lead_time_days', DEFAULT_LEAD_TIME_DAYS)
        coverage_days = data.get('coverage_days', DEFAULT_COVERAGE_DAYS)
        case_pack = data.get('case_pack', DEFAULT_CASE_PACK)
        simulation_days = data.get('simulation_days', 90)

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read and process data
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        processor = DataProcessor(df)
        processed_df = processor.process_all()

        # Filter by SKU
        if sku_id:
            sku_data = processed_df[processed_df['key'] == sku_id] if 'key' in processed_df.columns else (processed_df[processed_df['SKU ID'] == sku_id] if 'SKU ID' in processed_df.columns else pd.DataFrame())
        else:
            sku_data = processed_df

        if sku_data.empty:
            return jsonify({'error': f'No data found for SKU: {sku_id}'}), 404

        # Extract demand data
        # Find demand column
        demand_cols = ['Units/Qty', 'Offtake_Units', 'Offtake Units', 'Sales', 'Demand', 'Qty']
        demand_col = next((c for c in demand_cols if c in sku_data.columns), None)

        if not demand_col:
            # Filter for any numeric column as fallback
            numeric_cols = sku_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                demand_col = numeric_cols[0]

        if not demand_col:
            return jsonify({'error': 'No numeric demand column found'}), 400
        demand_data = sku_data[demand_col].dropna().values

        if len(demand_data) == 0:
            return jsonify({'error': 'No demand data available'}), 400

        # Run simulation
        simulator = InventorySimulator(
            lead_time_days=lead_time_days,
            coverage_days=coverage_days,
            case_pack=case_pack
        )

        # Use the single SKU simulation method
        # Start date for simulation
        start_date = datetime.now()

        # Calculate daily demand mean for simulation
        demand_mean = np.mean(demand_data)

        # Calculate safety stock for simulation
        # Use provided safety_stock if available, else derive from ROP
        if safety_stock_param is not None:
            sim_safety_stock = safety_stock_param
        else:
            sim_safety_stock = reorder_point - (demand_mean * lead_time_days)

        results_df = simulator.simulate_sku(
            sku_id=sku_id,
            avg_daily_demand=demand_mean,
            safety_stock=sim_safety_stock,
            initial_inventory=initial_inventory,
            start_date=start_date,
            days=simulation_days
        )

        # Stockout check
        stockouts = int(results_df['stockout'].sum())
        avg_inventory = float(results_df['ending_inventory'].mean())
        final_inventory = float(results_df['ending_inventory'].iloc[-1])

        return jsonify({
            'success': True,
            'sku_id': sku_id,
            'simulation_days': simulation_days,
            'initial_inventory': initial_inventory,
            'reorder_point': reorder_point,
            'metrics': results_df.to_dict('records'),
            'results_summary': {
                'total_days': simulation_days,
                'final_inventory': final_inventory,
                'avg_inventory': avg_inventory,
                'stock_outs': stockouts
            },
            'simulation_date': datetime.now().isoformat()
        }), 200

    except Exception as e:
        app.logger.error(f"Internal Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# BATCH CALCULATION ENDPOINTS
# ============================================================================


@app.route('/api/batch-calculate', methods=['POST'])
def batch_calculate():
    """
    Calculate safety stock and metrics for multiple SKUs
    Expected JSON:
    {
        'filepath': 'path/to/file.csv',
        'sku_ids': ['SKU123', 'SKU456'],
        'service_level': 0.975,
        'lead_time_days': 7
    }
    Returns: Results for all SKUs
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        sku_ids = data.get('sku_ids', [])
        service_level = float(data.get('service_level', DEFAULT_SERVICE_LEVEL))
        lead_time_days = int(data.get('lead_time_days', DEFAULT_LEAD_TIME_DAYS))

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read and process data
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        processor = DataProcessor(df)
        processed_df = processor.process_all()

        results = []
        calculator = SafetyStockCalculator(
            service_level=service_level,
            lead_time_days=lead_time_days
        )
        rop_calculator = ReorderPointCalculator(lead_time_days=lead_time_days)

        for sku_id in sku_ids:
            try:
                if 'key' in processed_df.columns:
                    sku_data = processed_df[processed_df['key'] == sku_id]
                elif 'SKU ID' in processed_df.columns:
                    sku_data = processed_df[processed_df['SKU ID'] == sku_id]
                else:
                    sku_cols = [c for c in processed_df.columns if 'sku' in c.lower() or 'id' in c.lower()]
                    if sku_cols:
                        sku_data = processed_df[processed_df[sku_cols[0]] == sku_id]
                    else:
                        sku_data = pd.DataFrame()

                if sku_data.empty:
                    results.append({
                        'sku_id': sku_id,
                        'status': 'error',
                        'message': 'No data found'
                    })
                    continue

                # Find demand column
                demand_cols = ['Units/Qty', 'Offtake_Units', 'Offtake Units', 'Sales', 'Demand', 'Qty']
                demand_col = next((c for c in demand_cols if c in sku_data.columns), None)

                if not demand_col:
                    # Filter for any numeric column as fallback
                    numeric_cols = sku_data.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        demand_col = numeric_cols[0]

                if not demand_col:
                    results.append({'sku_id': sku_id, 'status': 'error', 'message': 'No numeric demand column found'})
                    continue
                demand_data = sku_data[demand_col].dropna().values

                if len(demand_data) == 0:
                    results.append({
                        'sku_id': sku_id,
                        'status': 'error',
                        'message': 'No demand data'
                    })
                    continue

                demand_mean = np.mean(demand_data)
                demand_std = np.std(demand_data)
                cv = demand_std / demand_mean if demand_mean > 0 else 0

                safety_stock = calculator.calculate_safety_stock(
                    avg_daily_demand=demand_mean,
                    sigma_demand=demand_std
                )
                
                reorder_point = rop_calculator.calculate_reorder_point(
                    avg_daily_demand=demand_mean,
                    safety_stock=safety_stock
                )

                results.append({
                    'sku_id': sku_id,
                    'status': 'success',
                    'safety_stock': float(safety_stock),
                    'reorder_point': float(reorder_point),
                    'demand_mean': float(demand_mean),
                    'demand_std': float(demand_std),
                    'cv_demand': float(cv),
                    'service_level': float(service_level),
                    'Chain': str(sku_data['Chain'].iloc[0]) if 'Chain' in sku_data.columns else 'Unknown',
                    'Category': str(sku_data['L1 Prod Category'].iloc[0]) if 'L1 Prod Category' in sku_data.columns else 'Unknown',
                    'DT_Code': str(sku_data['DT Code'].iloc[0]) if 'DT Code' in sku_data.columns else 'Unknown',
                    'Brand': str(sku_data['Brand_Name'].iloc[0]) if 'Brand_Name' in sku_data.columns else 'Unknown'
                })

            except Exception as e:
                results.append({
                    'sku_id': sku_id,
                    'status': 'error',
                    'message': str(e)
                })

        return jsonify({
            'success': True,
            'total_skus': len(sku_ids),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'results': clean_for_json(results),
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/export-to-nowcast', methods=['POST'])
def export_to_nowcast():
    """
    Export alerts to Nowcast AI application
    Expected JSON: {'filepath': 'path/to/file.csv'}
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # 1. Read and process data
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        processor = DataProcessor(df)
        processor.process_all()
        processor.aggregate_to_monthly()
        processor.aggregate_to_weekly()
        df_sku_stats = processor.calculate_sku_statistics()

        # 2. Add SS, ROP and Simulated Stock (using same logic as get_charts)
        ss_calc = SafetyStockCalculator(service_level=0.975)
        rop_calc = ReorderPointCalculator()
        
        default_ss = []
        default_rop = []
        current_stock = []
        
        for _, row in df_sku_stats.iterrows():
            try:
                mean = row.get('avg_daily_demand', 0)
                std = row.get('std_dev_demand', 0)
                ss = ss_calc.calculate_safety_stock(mean, std, lead_time_days=7)
                rop = rop_calc.calculate_reorder_point(mean, ss, lead_time_days=7)
                
                # Use a deterministic/seeded factor or reasonable mock for export
                # Here we use a hash of the key to keep it consistent if re-run
                import hashlib
                h = int(hashlib.md5(str(row['key']).encode()).hexdigest(), 16)
                stock_factor = (h % 200) / 100.0 # 0.0 to 2.0
                
                sim_stock = rop * stock_factor
                
                default_ss.append(ss)
                default_rop.append(rop)
                current_stock.append(int(sim_stock))
            except:
                default_ss.append(0)
                default_rop.append(0)
                current_stock.append(0)
                
        df_sku_stats['safety_stock'] = default_ss
        df_sku_stats['reorder_point'] = default_rop
        df_sku_stats['current_stock'] = current_stock

        # 3. Aggregate for Map (Group by State)
        map_data = []
        oos_alerts = []
        over_alerts = []
        
        if 'State' in df_sku_stats.columns:
            # Generate Alert lists first
            # OOS: stock < ROP
            oos_df = df_sku_stats[df_sku_stats['current_stock'] < df_sku_stats['reorder_point']].copy()
            oos_df['doh'] = (oos_df['current_stock'] / oos_df['avg_daily_demand'].replace(0, 1)).fillna(0)
            
            for _, row in oos_df.sort_values('doh').head(20).iterrows():
                oos_alerts.append({
                    "state": str(row.get('State', 'NA')),
                    "item": str(row['key']),
                    "currentStock": int(row['current_stock']),
                    "weeksOnHand": round(float(row['doh'] / 7.0), 2)
                })

            # Over Inventory: stock > 2 * ROP (mock criteria)
            over_df = df_sku_stats[df_sku_stats['current_stock'] > df_sku_stats['reorder_point'] * 1.5].copy()
            over_df['doh'] = (over_df['current_stock'] / over_df['avg_daily_demand'].replace(0, 1)).fillna(0)
            
            for _, row in over_df.sort_values('doh', ascending=False).head(20).iterrows():
                over_alerts.append({
                    "state": str(row.get('State', 'NA')),
                    "item": str(row['key']),
                    "currentStock": int(row['current_stock']),
                    "weeksOnHand": round(float(row['doh'] / 7.0), 2)
                })

            for state, group in df_sku_stats.groupby('State'):
                if not state or state == 'Unknown' or str(state).lower() == 'nan':
                    continue
                
                # Define alerts: Stockout risk if current_stock < reorder_point
                alerts_df = group[group['current_stock'] < group['reorder_point']].copy()
                
                # Sort alerts by severity (lowest stock relative to ROP)
                alerts_df['severity'] = (alerts_df['current_stock'] / alerts_df['reorder_point']).fillna(0)
                alerts_df = alerts_df.sort_values('severity')
                
                state_entry = {
                    "State": str(state),
                    "Total_Alerts": int(len(alerts_df)),
                    "Item": alerts_df['key'].head(10).tolist(),
                    "Days_on_Hand": [round(float(s), 1) for s in (alerts_df['current_stock'] / alerts_df['avg_daily_demand'].replace(0, 1)).head(10).tolist()],
                    "Inventory_Alert": ["CRITICAL" if s < 0.5 else "WARNING" for s in alerts_df['severity'].head(10).tolist()]
                }
                map_data.append(state_entry)

        # 4. Write to Nowcast AI project directory
        export_payload = {
            "record": map_data,
            "oos_alerts": oos_alerts,
            "over_alerts": over_alerts
        }

        nowcast_path = r"c:\Users\Acer\Downloads\myTask\NowcastAI\src\jsons\supplychaintower\map_data.json"
        
        try:
            import json
            os.makedirs(os.path.dirname(nowcast_path), exist_ok=True)
            with open(nowcast_path, 'w') as f:
                json.dump(export_payload, f, indent=2)
            export_status = f"Saved to Nowcast AI at {nowcast_path}"
        except Exception as write_error:
            export_status = f"Error writing file: {str(write_error)}"

        return jsonify({
            'success': True,
            'message': export_status,
            'export_data': clean_for_json(export_payload)
        }), 200

    except Exception as e:
        app.logger.error(f"Export error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': 'File too large (max 50MB)'}), 413


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        threaded=True
    )
