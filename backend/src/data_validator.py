"""
Data Validation Module
Validates schema and data quality for inventory planning.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    EXPECTED_COLUMNS, CRITICAL_COLUMNS, NUMERIC_COLUMNS,
    CATEGORICAL_COLUMNS, MAX_MISSING_PERCENTAGE, MIN_HISTORICAL_WEEKS
)


class DataQualityReport:
    """Container for data quality validation results."""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.info = []
        self.schema_issues = {}
        self.data_quality_issues = {}
        
    def add_error(self, message: str):
        """Add a critical error."""
        self.errors.append(message)
        self.is_valid = False
        
    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)
        
    def add_info(self, message: str):
        """Add informational message."""
        self.info.append(message)
        
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'schema_issues': self.schema_issues,
            'data_quality_issues': self.data_quality_issues
        }
        
    def __str__(self) -> str:
        """String representation of the report."""
        lines = []
        lines.append("=" * 60)
        lines.append("DATA QUALITY VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Status: {'✓ VALID' if self.is_valid else '✗ INVALID'}")
        lines.append("")
        
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")
            
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
            
        if self.info:
            lines.append("INFORMATION:")
            for info in self.info:
                lines.append(f"  ℹ {info}")
            lines.append("")
            
        lines.append("=" * 60)
        return "\n".join(lines)


class DataValidator:
    """Validates uploaded dataset for inventory planning."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize validator with dataset.
        
        Args:
            df: Input pandas DataFrame
        """
        self.df = df
        self.report = DataQualityReport()
        
    def validate_all(self) -> DataQualityReport:
        """
        Run all validation checks.
        
        Returns:
            DataQualityReport with validation results
        """
        self.report.add_info(f"Dataset shape: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
        
        # Schema validations
        self._validate_schema()
        self._validate_critical_columns()
        
        # Data type validations
        self._validate_date_column()
        self._validate_numeric_columns()
        
        # Data quality checks
        self._check_missing_values()
        self._check_duplicates()
        self._check_negative_values()
        self._check_data_coverage()
        
        return self.report
        
    def _validate_schema(self):
        """Check if all expected columns are present."""
        actual_columns = set(self.df.columns)
        expected_columns = EXPECTED_COLUMNS
        
        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns
        
        if missing_columns:
            self.report.schema_issues['missing_columns'] = list(missing_columns)
            self.report.add_warning(
                f"Missing {len(missing_columns)} expected columns: {', '.join(list(missing_columns)[:5])}"
                + (f" and {len(missing_columns) - 5} more..." if len(missing_columns) > 5 else "")
            )
            
        if extra_columns:
            self.report.schema_issues['extra_columns'] = list(extra_columns)
            self.report.add_info(
                f"Found {len(extra_columns)} additional columns not in expected schema"
            )
            
    def _validate_critical_columns(self):
        """Ensure critical columns are present."""
        actual_columns = set(self.df.columns)
        missing_critical = [col for col in CRITICAL_COLUMNS if col not in actual_columns]
        
        if missing_critical:
            self.report.add_error(
                f"Missing CRITICAL columns required for analysis: {', '.join(missing_critical)}"
            )
            
    def _validate_date_column(self):
        """Validate date column format and values."""
        if 'date' not in self.df.columns:
            return
            
        # Try to parse dates
        try:
            date_series = pd.to_datetime(self.df['date'], errors='coerce')
            invalid_dates = date_series.isna().sum()
            
            if invalid_dates > 0:
                pct = (invalid_dates / len(self.df)) * 100
                self.report.add_warning(
                    f"Found {invalid_dates:,} ({pct:.2f}%) rows with invalid date format"
                )
                
            valid_dates = date_series.dropna()
            if len(valid_dates) > 0:
                date_range = f"{valid_dates.min().date()} to {valid_dates.max().date()}"
                days_span = (valid_dates.max() - valid_dates.min()).days
                self.report.add_info(f"Date range: {date_range} ({days_span} days)")
                
        except Exception as e:
            self.report.add_error(f"Error parsing date column: {str(e)}")
            
    def _validate_numeric_columns(self):
        """Validate numeric columns can be converted to numbers."""
        numeric_issues = {}
        
        for col in NUMERIC_COLUMNS:
            if col not in self.df.columns:
                continue
                
            try:
                numeric_series = pd.to_numeric(self.df[col], errors='coerce')
                invalid_count = numeric_series.isna().sum() - self.df[col].isna().sum()
                
                if invalid_count > 0:
                    numeric_issues[col] = invalid_count
                    
            except Exception as e:
                self.report.add_warning(f"Error validating numeric column '{col}': {str(e)}")
                
        if numeric_issues:
            self.report.data_quality_issues['numeric_conversion_issues'] = numeric_issues
            top_issues = sorted(numeric_issues.items(), key=lambda x: x[1], reverse=True)[:3]
            msg = ", ".join([f"{col}={count}" for col, count in top_issues])
            self.report.add_warning(f"Non-numeric values found in: {msg}")
            
    def _check_missing_values(self):
        """Check for missing values in important columns."""
        missing_summary = {}
        
        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(self.df)) * 100
                missing_summary[col] = {
                    'count': int(missing_count),
                    'percentage': round(missing_pct, 2)
                }
                
                if col in CRITICAL_COLUMNS and missing_pct > MAX_MISSING_PERCENTAGE * 100:
                    self.report.add_error(
                        f"Critical column '{col}' has {missing_pct:.1f}% missing values "
                        f"(threshold: {MAX_MISSING_PERCENTAGE * 100}%)"
                    )
                elif missing_pct > MAX_MISSING_PERCENTAGE * 100:
                    self.report.add_warning(
                        f"Column '{col}' has {missing_pct:.1f}% missing values"
                    )
                    
        if missing_summary:
            self.report.data_quality_issues['missing_values'] = missing_summary
            total_cols_with_missing = len(missing_summary)
            self.report.add_info(f"{total_cols_with_missing} columns have missing values")
            
    def _check_duplicates(self):
        """Check for duplicate rows."""
        if 'date' in self.df.columns and 'key' in self.df.columns:
            # Check for duplicates based on date and key
            duplicate_mask = self.df.duplicated(subset=['date', 'key'], keep=False)
            duplicate_count = duplicate_mask.sum()
            
            if duplicate_count > 0:
                pct = (duplicate_count / len(self.df)) * 100
                self.report.add_warning(
                    f"Found {duplicate_count:,} ({pct:.2f}%) duplicate rows (date + key)"
                )
                self.report.data_quality_issues['duplicates'] = int(duplicate_count)
        else:
            # Check for complete row duplicates
            duplicate_count = self.df.duplicated().sum()
            if duplicate_count > 0:
                self.report.add_warning(f"Found {duplicate_count:,} completely duplicate rows")
                self.report.data_quality_issues['duplicates'] = int(duplicate_count)
                
    def _check_negative_values(self):
        """Check for negative values in columns that should be positive."""
        positive_columns = ['Offtake_Units', 'Offtake_Value', 'SP', 'NSV Sales']
        negative_issues = {}
        
        for col in positive_columns:
            if col not in self.df.columns:
                continue
                
            try:
                numeric_col = pd.to_numeric(self.df[col], errors='coerce')
                negative_count = (numeric_col < 0).sum()
                
                if negative_count > 0:
                    negative_issues[col] = int(negative_count)
                    pct = (negative_count / len(self.df)) * 100
                    self.report.add_warning(
                        f"Column '{col}' has {negative_count:,} ({pct:.2f}%) negative values"
                    )
            except:
                pass
                
        if negative_issues:
            self.report.data_quality_issues['negative_values'] = negative_issues
            
    def _check_data_coverage(self):
        """Check data coverage per key."""
        if 'key' not in self.df.columns or 'date' not in self.df.columns:
            return
            
        try:
            df_temp = self.df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
            df_temp = df_temp.dropna(subset=['date', 'key'])
            
            if len(df_temp) == 0:
                return
                
            # Calculate weeks of data per key
            df_temp['week'] = df_temp['date'].dt.isocalendar().week
            df_temp['year'] = df_temp['date'].dt.year
            
            key_coverage = df_temp.groupby('key').apply(
                lambda x: len(x[['year', 'week']].drop_duplicates())
            )
            
            low_coverage_keys = (key_coverage < MIN_HISTORICAL_WEEKS).sum()
            total_keys = len(key_coverage)
            
            self.report.add_info(f"Total unique keys: {total_keys:,}")
            self.report.add_info(f"Average weeks per key: {key_coverage.mean():.1f}")
            
            if low_coverage_keys > 0:
                pct = (low_coverage_keys / total_keys) * 100
                self.report.add_warning(
                    f"{low_coverage_keys:,} keys ({pct:.1f}%) have less than "
                    f"{MIN_HISTORICAL_WEEKS} weeks of historical data"
                )
                
        except Exception as e:
            self.report.add_info(f"Could not analyze data coverage: {str(e)}")


def validate_dataset(df: pd.DataFrame) -> DataQualityReport:
    """
    Convenience function to validate a dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataQualityReport with validation results
    """
    validator = DataValidator(df)
    return validator.validate_all()
