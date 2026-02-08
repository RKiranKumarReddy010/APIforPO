"""
Utility helper functions for the Inventory Planning Dashboard
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


def calculate_z_score(service_level: float) -> float:
    """
    Calculate Z-score for a given service level using interpolation.
    
    Args:
        service_level: Desired service level (e.g., 0.975 for 97.5%)
        
    Returns:
        Z-score corresponding to the service level
    """
    from scipy.stats import norm
    return norm.ppf(service_level)


def format_number(value: float, decimals: int = 2) -> str:
    """
    Format number with thousands separator.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted string
    """
    return f"{value:,.{decimals}f}"


def calculate_weeks_from_date(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Add week number column to dataframe.
    
    Args:
        df: Input dataframe
        date_col: Name of date column
        
    Returns:
        DataFrame with added 'week' column and 'week_start' column
    """
    df = df.copy()
    df['week'] = df[date_col].dt.isocalendar().week
    df['year'] = df[date_col].dt.year
    df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
    # Add week_start (Monday of each week)
    df['week_start'] = df[date_col] - pd.to_timedelta(df[date_col].dt.dayofweek, unit='d')
    return df


def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """
    Detect outliers using IQR method.
    
    Args:
        series: Data series
        multiplier: IQR multiplier (default 1.5 for standard outliers)
        
    Returns:
        Boolean series indicating outliers
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    return (series < lower_bound) | (series > upper_bound)


def safe_divide(numerator: np.ndarray, denominator: np.ndarray, 
                fill_value: float = 0.0) -> np.ndarray:
    """
    Safely divide arrays, handling division by zero.
    
    Args:
        numerator: Numerator array
        denominator: Denominator array
        fill_value: Value to use when denominator is zero
        
    Returns:
        Result of division with safe handling
    """
    result = np.full_like(numerator, fill_value, dtype=float)
    mask = denominator != 0
    result[mask] = numerator[mask] / denominator[mask]
    return result


def create_date_range(start_date: datetime, days: int) -> List[datetime]:
    """
    Create a list of consecutive dates.
    
    Args:
        start_date: Starting date
        days: Number of days
        
    Returns:
        List of datetime objects
    """
    return [start_date + timedelta(days=i) for i in range(days)]


def aggregate_to_weekly(df: pd.DataFrame, date_col: str, 
                       group_cols: List[str], agg_cols: Dict[str, str]) -> pd.DataFrame:
    """
    Aggregate daily data to weekly level.
    
    Args:
        df: Input dataframe
        date_col: Date column name
        group_cols: Columns to group by (e.g., ['SKU ID'])
        agg_cols: Dictionary of {column: aggregation_method}
        
    Returns:
        Weekly aggregated dataframe
    """
    df = df.copy()
    df['week_start'] = df[date_col] - pd.to_timedelta(df[date_col].dt.dayofweek, unit='d')
    
    group_keys = group_cols + ['week_start']
    weekly_df = df.groupby(group_keys).agg(agg_cols).reset_index()
    
    return weekly_df


def calculate_coefficient_of_variation(series: pd.Series) -> float:
    """
    Calculate coefficient of variation (CV = std / mean).
    
    Args:
        series: Data series
        
    Returns:
        Coefficient of variation
    """
    mean_val = series.mean()
    if mean_val == 0:
        return 0.0
    return series.std() / mean_val


def generate_summary_stats(df: pd.DataFrame, 
                          numeric_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Generate summary statistics for numeric columns.
    
    Args:
        df: Input dataframe
        numeric_cols: List of numeric columns (if None, auto-detect)
        
    Returns:
        DataFrame with summary statistics
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    summary = df[numeric_cols].describe().T
    summary['missing'] = df[numeric_cols].isnull().sum()
    summary['missing_pct'] = (summary['missing'] / len(df) * 100).round(2)
    
    return summary


def calculate_weekly_weights_from_daily(typical_month_path: str) -> pd.DataFrame:
    """
    Calculate weekly weights from typical_month.csv daily patterns.
    
    Args:
        typical_month_path: Path to typical_month.csv file
        
    Returns:
        DataFrame with columns: key, week_of_month (1-5), weight (percentage 0-1)
    """
    # Load typical month daily data
    df = pd.read_csv(typical_month_path)
    
    # Assign each day to a week (1-5)
    # Assuming week 1 = days 1-7, week 2 = days 8-14, etc.
    def assign_week(day):
        if day <= 7:
            return 1
        elif day <= 14:
            return 2
        elif day <= 21:
            return 3
        elif day <= 28:
            return 4
        else:
            return 5  # Days 29-31
    
    df['week_of_month'] = df['day_of_month'].apply(assign_week)
    
    # Aggregate to weekly level
    weekly_agg = df.groupby(['key', 'week_of_month'])['avg_units'].sum().reset_index()
    weekly_agg.rename(columns={'avg_units': 'week_units'}, inplace=True)
    
    # Calculate total monthly units per key
    monthly_totals = weekly_agg.groupby('key')['week_units'].sum().reset_index()
    monthly_totals.rename(columns={'week_units': 'monthly_total'}, inplace=True)
    
    # Merge and calculate weights
    weekly_weights = weekly_agg.merge(monthly_totals, on='key')
    weekly_weights['weight'] = weekly_weights['week_units'] / weekly_weights['monthly_total']
    
    # Keep only necessary columns
    weekly_weights = weekly_weights[['key', 'week_of_month', 'weight']].copy()
    
    return weekly_weights
