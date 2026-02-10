"""
Configuration settings for Inventory Planning Dashboard
"""

# Expected dataset schema (from Final_table.xlsx Sheet1)
EXPECTED_COLUMNS = {
    'date', 'key', 'seasonal', 'hist_range', 'actual_value', 'SARIMA_pred', 
    'SARIMA_adj_pred', 'HoltWinters_pred', 'HoltWinters_adj_pred', 
    'Prophet_pred', 'Prophet_adj_pred', 'L3M_pred', 'L3M_adj_pred', 
    'L6M_pred', 'L6M_adj_pred', 'RF_pred', 'RF_adj_pred', 'XGB_pred', 
    'XGB_adj_pred', 'LY_trend_pred', 'LY_trend_adj_pred', 'TBF_pred', 
    'TBF_adj_pred', 'Naive_pred', 'Naive_adj_pred', 'LGBM_pred', 
    'LGBM_adj_pred', 'RF_default_pred', 'RF_default_adj_pred', 
    'XGB_default_pred', 'XGB_default_adj_pred', 'LGBM_default_pred', 
    'LGBM_default_adj_pred', 'fcst_best_raw_model_unadjusted', 
    'fcst_best_raw_model_adjusted', 'fcst_best_adj_model_adjusted', 
    'best_model_raw', 'best_model_bias_adj', 'period', 'trend', 
    'seasonality', 'lag1', 'lag2', 'lag3', 'rolling_mean_3m', 
    'rolling_mean_6m', 'rolling_std_3m', 'year', 'month', 'quarter', 
    'monthly_ratio', 'P1', 'P2', 'P3', 'gif', 'prime_day', 'freedom_fest', 
    'republic_sale', 'wardrobe_refresh', 'bbd', 'big_saving_days', 
    'big_freedom_sale', 'republic_day_sale', 'eoss', 'summer_sale', 
    'black_friday', 'Units/Qty', 'Offtake_Units', 'MRP Sales', 
    'Offtake_Value', 'SP', 'NSV Sales', 'NSV in Lacs', 'Chain', 
    'Grouped Chain', 'Channel', 'Final City', 'State', 'Region', 
    'SKU ID', 'DT Code', 'L1 Prod Category', 'L2 Prod Brand', 
    'Brand_Name', 'Sub brands'
}

# Critical columns required for the analysis
CRITICAL_COLUMNS = ['date', 'key', 'Offtake_Units']

# Numeric columns
NUMERIC_COLUMNS = [
    'Offtake_Units', 'Units/Qty', 'Offtake_Value', 'MRP Sales', 'SP', 
    'NSV Sales', 'NSV in Lacs', 'actual_value', 'lag1', 'lag2', 'lag3',
    'rolling_mean_3m', 'rolling_mean_6m', 'rolling_std_3m', 
    'year', 'month', 'quarter', 'monthly_ratio', 'P1', 'P2', 'P3',
    'SARIMA_pred', 'SARIMA_adj_pred', 'HoltWinters_pred', 
    'HoltWinters_adj_pred', 'Prophet_pred', 'Prophet_adj_pred',
    'L3M_pred', 'L3M_adj_pred', 'L6M_pred', 'L6M_adj_pred',
    'RF_pred', 'RF_adj_pred', 'XGB_pred', 'XGB_adj_pred'
]

# Categorical columns
CATEGORICAL_COLUMNS = [
    'Chain', 'Grouped Chain', 'Channel', 'Final City', 'State', 'Region',
    'key', 'SKU ID', 'DT Code', 'L1 Prod Category', 'L2 Prod Brand', 
    'Brand_Name', 'Sub brands', 'seasonal', 'hist_range', 'period',
    'best_model_raw', 'best_model_bias_adj'
]

# Event columns (binary flags)
EVENT_COLUMNS = [
    'gif', 'prime_day', 'freedom_fest', 'republic_sale', 
    'wardrobe_refresh', 'bbd', 'big_saving_days', 'big_freedom_sale', 
    'republic_day_sale', 'eoss', 'summer_sale', 'black_friday'
]

# Default simulation parameters
DEFAULT_SERVICE_LEVEL = 0.975  # 97.5% service level (Z = 1.96)
DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_COVERAGE_DAYS = 7
DEFAULT_CASE_PACK = 12
DEFAULT_SIMULATION_DAYS = 90

# Service level to Z-score mapping
SERVICE_LEVELS = {
    0.90: 1.28,
    0.95: 1.65,
    0.975: 1.96,
    0.99: 2.33,
    0.995: 2.58
}

# Data quality thresholds
MAX_MISSING_PERCENTAGE = 0.20  # 20% missing data threshold
MIN_HISTORICAL_WEEKS = 12  # Minimum weeks of data required per SKU

# Output paths
OUTPUT_DIR = "outputs"
DATA_DIR = "data"
