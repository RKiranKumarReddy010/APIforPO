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

        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'validation': validation_result,
            'rows': len(df),
            'columns_count': len(df.columns)
        }), 200

    except Exception as e:
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
            'validation': validation_result,
            'data_summary': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'dtypes': df.dtypes.astype(str).to_dict(),
                'missing_values': df.isnull().sum().to_dict()
            }
        }), 200

    except Exception as e:
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
        processed_df = processor.process()

        # Calculate statistics
        stats = {
            'original_rows': len(df),
            'processed_rows': len(processed_df),
            'columns': processed_df.columns.tolist(),
            'summary_statistics': processed_df.describe().to_dict()
        }

        return jsonify({
            'success': True,
            'message': 'Data processed successfully',
            'statistics': stats
        }), 200

    except Exception as e:
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
        processed_df = processor.process()

        # Filter by SKU
        if sku_id:
            sku_data = processed_df[processed_df.get('SKU ID') == sku_id]
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
        demand_col = 'Units/Qty' if 'Units/Qty' in sku_data.columns else 'Offtake_Units'
        demand_data = sku_data[demand_col].dropna().values

        if len(demand_data) == 0:
            return jsonify({'error': 'No demand data available'}), 400

        # Calculate metrics
        demand_mean = np.mean(demand_data)
        demand_std = np.std(demand_data)
        lead_time_mean = lead_time_days

        # Calculate safety stock
        safety_stock = calculator.calculate(
            demand_mean=demand_mean,
            demand_std=demand_std,
            lead_time_mean=lead_time_mean,
            lead_time_std=lead_time_std
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
        processed_df = processor.process()

        # Filter by SKU
        if sku_id:
            sku_data = processed_df[processed_df.get('SKU ID') == sku_id]
        else:
            sku_data = processed_df

        if sku_data.empty:
            return jsonify({'error': f'No data found for SKU: {sku_id}'}), 404

        # Extract demand data
        demand_col = 'Units/Qty' if 'Units/Qty' in sku_data.columns else 'Offtake_Units'
        demand_data = sku_data[demand_col].dropna().values

        if len(demand_data) == 0:
            return jsonify({'error': 'No demand data available'}), 400

        # Run simulation
        simulator = InventorySimulator(
            initial_inventory=initial_inventory,
            reorder_point=reorder_point,
            service_level=service_level,
            lead_time_days=lead_time_days,
            coverage_days=coverage_days,
            case_pack=case_pack
        )

        results = simulator.simulate(
            demand_data=demand_data,
            num_days=simulation_days
        )

        # Calculate metrics
        if results is not None:
            metrics = calculate_inventory_metrics(results)
        else:
            metrics = {}

        return jsonify({
            'success': True,
            'sku_id': sku_id,
            'simulation_days': simulation_days,
            'initial_inventory': initial_inventory,
            'reorder_point': reorder_point,
            'metrics': metrics,
            'results_summary': {
                'total_days': simulation_days,
                'final_inventory': float(results[-1][0]) if results else 0,
                'avg_inventory': float(np.mean([r[0] for r in results])) if results else 0,
                'stock_outs': int(np.sum([1 for r in results if r[0] < 0])) if results else 0
            },
            'simulation_date': datetime.now().isoformat()
        }), 200

    except Exception as e:
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
        service_level = data.get('service_level', DEFAULT_SERVICE_LEVEL)
        lead_time_days = data.get('lead_time_days', DEFAULT_LEAD_TIME_DAYS)

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Read and process data
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        processor = DataProcessor(df)
        processed_df = processor.process()

        results = []
        calculator = SafetyStockCalculator(
            service_level=service_level,
            lead_time_days=lead_time_days
        )

        for sku_id in sku_ids:
            try:
                sku_data = processed_df[processed_df.get('SKU ID') == sku_id]
                if sku_data.empty:
                    results.append({
                        'sku_id': sku_id,
                        'status': 'error',
                        'message': 'No data found'
                    })
                    continue

                demand_col = 'Units/Qty' if 'Units/Qty' in sku_data.columns else 'Offtake_Units'
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

                safety_stock = calculator.calculate(
                    demand_mean=demand_mean,
                    demand_std=demand_std,
                    lead_time_mean=lead_time_days,
                    lead_time_std=1.5
                )

                results.append({
                    'sku_id': sku_id,
                    'status': 'success',
                    'safety_stock': float(safety_stock),
                    'demand_mean': float(demand_mean),
                    'demand_std': float(demand_std)
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
            'results': results,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
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
        threaded=True
    )
