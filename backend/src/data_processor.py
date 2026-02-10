"""
Data Processing Module
Handles data standardization, cleaning, and aggregation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import NUMERIC_COLUMNS, CATEGORICAL_COLUMNS, EVENT_COLUMNS
from utils.helpers import calculate_weeks_from_date, aggregate_to_weekly


class DataProcessor:
    """Processes and prepares data for inventory analysis."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize processor with raw dataset.
        
        Args:
            df: Raw input DataFrame
        """
        self.df_raw = df.copy()
        self.df_clean = None
        self.df_monthly = None
        self.df_weekly = None
        self.df_sku_stats = None
        self.processing_log = []
        
    def process_all(self) -> pd.DataFrame:
        """
        Execute complete data processing pipeline.
        
        Returns:
            Cleaned and processed DataFrame
        """
        self._log("Starting data processing pipeline")
        
        # Step 1: Standardize data types
        self.df_clean = self._standardize_data_types(self.df_raw)
        
        # Step 2: Handle missing values
        self.df_clean = self._handle_missing_values(self.df_clean)
        
        # Step 3: Remove duplicates
        self.df_clean = self._remove_duplicates(self.df_clean)
        
        # Step 4: Clean and validate numeric fields
        self.df_clean = self._clean_numeric_fields(self.df_clean)
        
        # Step 5: Add derived features
        self.df_clean = self._add_derived_features(self.df_clean)
        
        self._log(f"Processing complete. Final shape: {self.df_clean.shape}")
        
        return self.df_clean
    
    def aggregate_to_monthly(self) -> pd.DataFrame:
        """
        Aggregate daily data to monthly SKU-level demand.
        First level of aggregation for analysis.
        
        Returns:
            Monthly aggregated DataFrame
        """
        if self.df_clean is None:
            raise ValueError("Must run process_all() before aggregating to monthly")
            
        self._log("Aggregating to monthly SKU-level data")
        
        df_monthly = self.df_clean.copy()
        df_monthly['year_month'] = pd.to_datetime(df_monthly['date']).dt.to_period('M')
        df_monthly['month_start'] = pd.to_datetime(df_monthly['date']).dt.to_period('M').dt.to_timestamp()
        
        # Aggregate to monthly level
        agg_dict = {
            'Offtake_Units': 'sum',
            'Offtake_Value': 'sum',
        }
        
        # Add NSV Sales if it exists
        if 'NSV Sales' in df_monthly.columns:
            agg_dict['NSV Sales'] = 'sum'
        
        # Add event flags (max to capture if event occurred during month)
        for event_col in EVENT_COLUMNS:
            if event_col in df_monthly.columns:
                agg_dict[event_col] = 'max'
        
        self.df_monthly = df_monthly.groupby(['key', 'year_month', 'month_start']).agg(agg_dict).reset_index()
        
        # Sort by key and month
        self.df_monthly = self.df_monthly.sort_values(['key', 'month_start']).reset_index(drop=True)
        
        self._log(f"Monthly aggregation complete. Shape: {self.df_monthly.shape}")
        
        return self.df_monthly
        
    def aggregate_to_weekly(self) -> pd.DataFrame:
        """
        Aggregate daily data to weekly SKU-level demand.
        
        Returns:
            Weekly aggregated DataFrame
        """
        if self.df_clean is None:
            raise ValueError("Must run process_all() before aggregating to weekly")
            
        self._log("Aggregating to weekly SKU-level data")
        
        # Add week identifier and week_start
        df_with_weeks = calculate_weeks_from_date(self.df_clean, 'date')
        
        # Aggregate to weekly level
        agg_dict = {
            'Offtake_Units': 'sum',
            'Offtake_Value': 'sum',
        }
        
        # Add NSV Sales if it exists
        if 'NSV Sales' in df_with_weeks.columns:
            agg_dict['NSV Sales'] = 'sum'
        
        # Add event flags (max to capture if event occurred during week)
        for event_col in EVENT_COLUMNS:
            if event_col in df_with_weeks.columns:
                agg_dict[event_col] = 'max'
        
        self.df_weekly = df_with_weeks.groupby(['key', 'year_week', 'week_start']).agg(agg_dict).reset_index()
        
        # Sort by key and week
        self.df_weekly = self.df_weekly.sort_values(['key', 'week_start']).reset_index(drop=True)
        
        self._log(f"Weekly aggregation complete. Shape: {self.df_weekly.shape}")
        
        return self.df_weekly
        
    def calculate_sku_statistics(self) -> pd.DataFrame:
        """
        Calculate demand statistics per key.
        
        For MONTHLY data: Uses disaggregated daily values for calculations.
        Analysis: Disaggregate monthly -> calculate daily statistics
        
        Returns:
            DataFrame with key-level statistics including volatility metrics
        """
        if not hasattr(self, 'df_monthly') or self.df_monthly is None:
            raise ValueError("Must run aggregate_to_monthly() before calculating key stats")
        
        if self.df_weekly is None:
            raise ValueError("Must run aggregate_to_weekly() before calculating key stats")
        
        if self.df_clean is None:
            raise ValueError("Must run process_all() before calculating key stats")
            
        self._log("Calculating key-level statistics from monthly data")
        
        # Check if source data is monthly (all dates are 1st of month)
        is_monthly = (pd.to_datetime(self.df_clean['date']).dt.day == 1).all()
        
        if is_monthly:
            self._log("Source data is MONTHLY - using disaggregated daily values for statistics")
        
        stats_list = []
        
        for key_id in self.df_monthly['key'].unique():
            # Get monthly data for this key
            monthly_data = self.df_monthly[self.df_monthly['key'] == key_id]['Offtake_Units']
            weekly_data = self.df_weekly[self.df_weekly['key'] == key_id]['Offtake_Units']
            
            # Calculate daily demand by dividing monthly by avg days per month
            # Typical month = 30.4 days, but we'll use actual days
            total_months = len(monthly_data)
            avg_monthly_demand = monthly_data.mean()
            std_monthly_demand = monthly_data.std()
            
            # For disaggregation: assume 30 days per month on average
            avg_days_per_month = 30.0
            
            # Calculate daily demand statistics
            # For simulation: Use a more conservative sigma based on monthly CV
            # rather than direct scaling which amplifies variance
            avg_daily_demand = avg_monthly_demand / avg_days_per_month
            
            # Calculate coefficient of variation from monthly data
            cv_monthly = std_monthly_demand / avg_monthly_demand if avg_monthly_demand > 0 else 0
            
            # Apply CV to daily demand for more reasonable daily variance
            # This assumes relative variability is similar at daily and monthly levels
            std_daily_demand = avg_daily_demand * cv_monthly
            
            # Sigma_Demand for safety stock (capped at reasonable level)
            # Cap at 100% of daily demand to avoid extreme safety stocks
            sigma_demand = min(std_daily_demand, avg_daily_demand)
            
            # Basic statistics
            stats = {
                'key': key_id,
                # Monthly level
                'total_months': total_months,
                'avg_monthly_demand': avg_monthly_demand,
                'std_monthly_demand': std_monthly_demand,
                'avg_days_per_month': avg_days_per_month,
                # Weekly level
                'total_weeks': len(weekly_data),
                'avg_weekly_demand': weekly_data.mean(),
                'median_weekly_demand': weekly_data.median(),
                'std_weekly_demand': weekly_data.std(),
                'min_weekly_demand': weekly_data.min(),
                'max_weekly_demand': weekly_data.max(),
                # Daily level (calculated from monthly)
                'total_days': int(total_months * avg_days_per_month),
                'total_demand': monthly_data.sum(),
                'avg_daily_demand': avg_daily_demand,
                'std_daily_demand': std_daily_demand,
            }
            
            # Coefficient of variation (from weekly)
            if stats['avg_weekly_demand'] > 0:
                stats['cv_demand'] = stats['std_weekly_demand'] / stats['avg_weekly_demand']
            else:
                stats['cv_demand'] = 0
            
            # Sigma_Demand = RMSE scaled from monthly variance (primary metric for safety stock)
            stats['sigma_demand'] = sigma_demand
            
            stats_list.append(stats)
            
        self.df_sku_stats = pd.DataFrame(stats_list)
        
        self._log(f"Key statistics calculated for {len(self.df_sku_stats)} keys")
        
        return self.df_sku_stats
        
    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column data types."""
        df = df.copy()
        self._log("Standardizing data types")
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                self._log(f"⚠ Converted date column: {invalid_dates} invalid dates set to NaT")
                
        # Convert numeric columns
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if original_type != df[col].dtype:
                    self._log(f"Converted '{col}' to numeric")
                    
        # Ensure categorical columns are strings
        for col in CATEGORICAL_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype(str)
                
        # Ensure event columns are binary (0/1)
        for col in EVENT_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
        return df
        
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with appropriate strategies."""
        df = df.copy()
        self._log("Handling missing values")
        
        # Fill numeric columns with 0 (representing no sales/demand)
        numeric_fill_cols = ['Offtake_Units', 'Offtake_Value', 'NSV Sales']
        for col in numeric_fill_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    df[col] = df[col].fillna(0)
                    self._log(f"Filled {missing_count} missing values in '{col}' with 0")
                    
        # Fill categorical columns with 'Unknown'
        for col in CATEGORICAL_COLUMNS:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    df[col] = df[col].fillna('Unknown')
                    self._log(f"Filled {missing_count} missing values in '{col}' with 'Unknown'")
                    
        # Fill event columns with 0 (no event)
        for col in EVENT_COLUMNS:
            if col in df.columns:
                df[col] = df[col].fillna(0)
                
        return df
        
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows."""
        df = df.copy()
        initial_count = len(df)
        
        # Remove duplicates based on date and key
        if 'date' in df.columns and 'key' in df.columns:
            df = df.drop_duplicates(subset=['date', 'key'], keep='first')
            removed = initial_count - len(df)
            if removed > 0:
                self._log(f"Removed {removed} duplicate rows (date + key)")
        else:
            df = df.drop_duplicates()
            removed = initial_count - len(df)
            if removed > 0:
                self._log(f"Removed {removed} completely duplicate rows")
                
        return df
        
    def _clean_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate numeric fields."""
        df = df.copy()
        self._log("Cleaning numeric fields")
        
        # Replace negative values in positive-only columns with 0
        positive_columns = ['Offtake_Units', 'Offtake_Value', 'SP', 'NSV Sales']
        for col in positive_columns:
            if col in df.columns:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    df.loc[df[col] < 0, col] = 0
                    self._log(f"Replaced {negative_count} negative values in '{col}' with 0")
                    
        return df
        
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for analysis."""
        df = df.copy()
        self._log("Adding derived features")
        
        # Add time-based features
        if 'date' in df.columns:
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_name'] = df['date'].dt.day_name()
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
        # Flag if any promotional event
        event_cols_present = [col for col in EVENT_COLUMNS if col in df.columns]
        if event_cols_present:
            df['has_event'] = df[event_cols_present].max(axis=1)
            
        return df
        
    def _log(self, message: str):
        """Add message to processing log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.processing_log.append(log_entry)
        
    def get_processing_log(self) -> List[str]:
        """Return processing log."""
        return self.processing_log


def process_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Convenience function to process dataset through complete pipeline.
    
    Args:
        df: Raw input DataFrame
        
    Returns:
        Tuple of (cleaned_df, weekly_df, sku_stats_df)
    """
    processor = DataProcessor(df)
    df_clean = processor.process_all()
    df_weekly = processor.aggregate_to_weekly()
    df_sku_stats = processor.calculate_sku_statistics()
    
    return df_clean, df_weekly, df_sku_stats
