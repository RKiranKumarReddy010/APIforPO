"""
Inventory Calculator Module
Implements dynamic safety stock calculation and 90-day inventory simulation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    DEFAULT_SERVICE_LEVEL, DEFAULT_LEAD_TIME_DAYS, DEFAULT_COVERAGE_DAYS,
    DEFAULT_CASE_PACK, DEFAULT_SIMULATION_DAYS
)
from utils.helpers import calculate_z_score, safe_divide, create_date_range, calculate_weekly_weights_from_daily


class SafetyStockCalculator:
    """
    Calculates dynamic safety stock using the formula:
    SS = Z × sqrt((L_avg × σ_Demand²) + (D_avg² × σ_LeadTime²))
    
    Where:
    - Z: Service level coefficient (e.g., 1.96 for 97.5%)
    - L_avg: Average lead time
    - σ_Demand: Standard deviation of demand (daily)
    - D_avg: Average daily demand
    - σ_LeadTime: Standard deviation of lead time
    """
    
    def __init__(self, 
                 service_level: float = DEFAULT_SERVICE_LEVEL,
                 lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
                 lead_time_std: float = 2.0):
        """
        Initialize calculator with parameters.
        
        Args:
            service_level: Desired service level (e.g., 0.975 for 97.5%)
            lead_time_days: Average lead time in days
            lead_time_std: Standard deviation of lead time in days
        """
        self.service_level = service_level
        self.z_score = calculate_z_score(service_level)
        self.lead_time_avg = lead_time_days
        self.lead_time_std = lead_time_std
        
    def calculate_safety_stock(self, 
                               avg_daily_demand: float,
                               sigma_demand: float,
                               debug: bool = False) -> float:
        """
        Calculate safety stock for a single SKU.
        
        Args:
            avg_daily_demand: Average daily demand (D_avg)
            sigma_demand: Standard deviation of daily demand
            debug: Print calculation details
            
        Returns:
            Safety stock quantity (units)
        """
        # Formula: SS = Z × sqrt((L_avg × σ_Demand²) + (D_avg² × σ_LeadTime²))
        
        variance_from_demand = self.lead_time_avg * (sigma_demand ** 2)
        variance_from_leadtime = (avg_daily_demand ** 2) * (self.lead_time_std ** 2)
        
        total_variance = variance_from_demand + variance_from_leadtime
        
        if total_variance < 0:
            total_variance = 0
            
        safety_stock = self.z_score * np.sqrt(total_variance)
        
        if debug:
            print(f"\n🔍 Safety Stock Calculation:")
            print(f"   Z-score (service level): {self.z_score}")
            print(f"   Lead time avg: {self.lead_time_avg} days")
            print(f"   Lead time std: {self.lead_time_std} days")
            print(f"   Avg daily demand (D_avg): {avg_daily_demand:.2f}")
            print(f"   Sigma demand (σ_Demand): {sigma_demand:.2f}")
            print(f"   Variance from demand: {self.lead_time_avg} × {sigma_demand:.2f}² = {variance_from_demand:.2f}")
            print(f"   Variance from lead time: {avg_daily_demand:.2f}² × {self.lead_time_std}² = {variance_from_leadtime:.2f}")
            print(f"   Total variance: {total_variance:.2f}")
            print(f"   Safety Stock = {self.z_score} × √{total_variance:.2f} = {safety_stock:.2f}")
        
        return max(0, safety_stock)  # Ensure non-negative
        
    def calculate_for_dataframe(self, df_sku_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate safety stock for all keys in dataframe.
        
        Args:
            df_sku_stats: DataFrame with columns ['key', 'avg_daily_demand', 'sigma_demand']
            
        Returns:
            DataFrame with added 'safety_stock' column
        """
        df = df_sku_stats.copy()
        
        # Calculate safety stock for each SKU
        safety_stocks = []
        for idx, row in df.iterrows():
            # Debug first 3 keys
            debug = idx < 3
            ss = self.calculate_safety_stock(
                row['avg_daily_demand'],
                row['sigma_demand'],
                debug=debug
            )
            safety_stocks.append(ss)
        
        df['safety_stock'] = safety_stocks
        
        # Round to whole units
        df['safety_stock'] = np.ceil(df['safety_stock']).astype(int)
        
        # Add metadata
        df['service_level'] = self.service_level
        df['z_score'] = self.z_score
        df['lead_time_avg'] = self.lead_time_avg
        df['lead_time_std'] = self.lead_time_std
        
        return df


class ReorderPointCalculator:
    """
    Calculates Reorder Point (ROP) and related metrics.
    
    ROP = (D_avg × L_avg) + SS
    """
    
    def __init__(self, 
                 lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
                 coverage_days: int = DEFAULT_COVERAGE_DAYS):
        """
        Initialize calculator.
        
        Args:
            lead_time_days: Average lead time in days
            coverage_days: Desired inventory coverage in days
        """
        self.lead_time_days = lead_time_days
        self.coverage_days = coverage_days
        
    def calculate_reorder_point(self, 
                                avg_daily_demand: float,
                                safety_stock: float) -> float:
        """
        Calculate reorder point.
        
        Args:
            avg_daily_demand: Average daily demand
            safety_stock: Safety stock quantity
            
        Returns:
            Reorder point (units)
        """
        rop = (avg_daily_demand * self.lead_time_days) + safety_stock
        return max(0, rop)
        
    def calculate_order_quantity(self,
                                 avg_daily_demand: float,
                                 current_inventory: float,
                                 safety_stock: float,
                                 in_transit_qty: float = 0) -> float:
        """
        Calculate order quantity when ROP is triggered.
        
        Q = (D_{t→t+Coverage}) + SS - Net_Inv
        
        ROP already accounts for lead time demand, so the order only needs to 
        replenish to the Coverage level plus safety stock.
        
        Args:
            avg_daily_demand: Average daily demand
            current_inventory: Current inventory level
            safety_stock: Safety stock quantity
            in_transit_qty: Quantity in transit from previous POs
            
        Returns:
            Order quantity (units)
        """
        # Demand during coverage period only
        # ROP already ensures we have enough to cover lead time
        coverage_demand = avg_daily_demand * self.coverage_days
        
        # Net inventory (current + in-transit)
        net_inventory = current_inventory + in_transit_qty
        
        # Order quantity = Coverage demand + Safety stock - Net inventory
        order_qty = coverage_demand + safety_stock - net_inventory
        
        return max(0, order_qty)
        
    def apply_case_pack_constraint(self, 
                                   order_qty: float, 
                                   case_pack: int = DEFAULT_CASE_PACK) -> int:
        """
        Round order quantity to nearest case pack.
        
        Args:
            order_qty: Calculated order quantity
            case_pack: Units per case
            
        Returns:
            Order quantity rounded to case packs
        """
        if case_pack <= 0:
            return int(np.ceil(order_qty))
            
        # Round up to nearest case pack
        num_cases = int(np.ceil(order_qty / case_pack))
        return num_cases * case_pack


class InventorySimulator:
    """
    Runs deterministic 90-day daily inventory simulation.
    
    The Algorithm (from pseudo-code):
    For each day t in [1, 90]:
      1. Inventory State Update: I_t = I_{t-1} - D_t + R_t
      2. Net Requirement Check: Net_Inv = I_t + Σ(In-Transit POs)
      3. Replenishment Trigger: if Net_Inv ≤ ROP:
         - Calculate Order Quantity (Q)
         - Apply Constraints: Q_final = ⌈Q/CasePack⌉ × CasePack
         - Set Delivery Date: R_{t+LeadTime} = Q_final
    """
    
    # Class-level cache for weekly weights
    _weekly_weights_cache = None
    
    def __init__(self,
                 lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
                 coverage_days: int = DEFAULT_COVERAGE_DAYS,
                 case_pack: int = DEFAULT_CASE_PACK):
        """
        Initialize simulator.
        
        Args:
            lead_time_days: Lead time for replenishment
            coverage_days: Desired inventory coverage
            case_pack: Units per case pack
        """
        self.lead_time_days = lead_time_days
        self.coverage_days = coverage_days
        self.case_pack = case_pack
        self.rop_calculator = ReorderPointCalculator(lead_time_days, coverage_days)
        
    def simulate_with_actual_forecast(self,
                                      key_id: str,
                                      df_daily_forecast: pd.DataFrame,
                                      reorder_point: float,
                                      safety_stock: float,
                                      initial_inventory: float,
                                      case_pack: int = None) -> pd.DataFrame:
        """
        Run simulation using EXACT Excel formulas:
        
        1. Net Inventory = C5 - E5 (Inventory - Daily Offtake Forecast)
        2. Reorder Point = IF(F5 < SS, 1, 0) (IF Net Inventory < SS, 1, 0)
        3. Reorder Quantity = IF(G5=1, SUM(E6:E13), 0) (IF flag=1, SUM next 7 days, 0)
        
        Excel Logic Flow:
        - Row 1: Starting inventory (e.g., 5000)
        - Each row: Inventory = Previous Net Inventory + Received
        - Net Inventory = Inventory - Daily Forecast
        - Order if Net < SS
        
        Args:
            key_id: Key identifier
            df_daily_forecast: DataFrame with 'date' and 'Offtake_Units' columns
            reorder_point: Not used (only SS matters)
            safety_stock: Safety stock level (SS, e.g., 1500)
            initial_inventory: Starting inventory (e.g., 5000)
            case_pack: Ignored per user request
            
        Returns:
            DataFrame with daily simulation results matching Excel format
        """
        # Sort by date and reset index
        df_forecast = df_daily_forecast.sort_values('date').reset_index(drop=True)
        
        simulation_log = []
        in_transit_orders = {}  # {delivery_date: quantity}
        
        for idx, row in df_forecast.iterrows():
            current_date = row['date']
            daily_offtake_forecast = row['Offtake_Units']  # E column
            
            # C column: Inventory (beginning inventory for the day)
            if idx == 0:
                # First day: use initial inventory
                inventory = initial_inventory
                inventory_received = 0
            else:
                # Subsequent days: Previous net inventory + any received orders
                inventory = simulation_log[-1]['net_inventory']
                
                # Check for order delivery today
                inventory_received = in_transit_orders.pop(current_date, 0)
                inventory += inventory_received
            
            # F column: Net Inventory = C - E (Inventory - Daily Offtake Forecast)
            net_inventory = inventory - daily_offtake_forecast
            
            # Check if there are any orders in transit
            has_orders_in_transit = len(in_transit_orders) > 0
            
            # G column: Reorder Point flag = IF(F < SS AND no orders in transit, 1, 0)
            # Only flag for reorder if we're actually going to place an order
            reorder_flag = 1 if (net_inventory < safety_stock and not has_orders_in_transit) else 0
            
            # H column: Reorder Quantity = IF(G=1, SUM(next 7 days), 0)
            order_qty = 0
            if reorder_flag == 1:
                # Sum next lead_time days of forecast
                start_idx = idx + 1
                end_idx = min(start_idx + self.lead_time_days, len(df_forecast))
                if start_idx < len(df_forecast):
                    order_qty = df_forecast.loc[start_idx:end_idx-1, 'Offtake_Units'].sum()
                
                # Schedule delivery after lead time
                if order_qty > 0:
                    delivery_date = current_date + timedelta(days=self.lead_time_days)
                    in_transit_orders[delivery_date] = order_qty
            
            # Log daily state (Excel column format)
            simulation_log.append({
                'date': current_date,
                'key': key_id,
                's_no': idx + 1,
                'inventory': inventory,  # C column
                'inventory_received': inventory_received,  # D column
                'daily_offtake_forecast': daily_offtake_forecast,  # E column
                'net_inventory': net_inventory,  # F column = C - E
                'reorder_point': reorder_flag,  # G column = IF(F<SS, 1, 0)
                'reorder_quantity': order_qty,  # H column = IF(G=1, SUM(...), 0)
                # Additional columns for compatibility
                'rop': safety_stock,
                'safety_stock': safety_stock,
                'order_placed': reorder_flag,
                'stockout': 1 if net_inventory < 0 else 0,
                'ending_inventory': net_inventory,
                'received_qty': inventory_received,
                'daily_forecast': daily_offtake_forecast,
                'reorder_flag': reorder_flag,
                'order_qty': order_qty
            })
        
        return pd.DataFrame(simulation_log)
    
    def _disaggregate_to_daily(self, df_monthly: pd.DataFrame) -> pd.DataFrame:
        """
        Disaggregate monthly data to daily using weekly weights from typical_month.csv.
        
        Args:
            df_monthly: DataFrame with monthly data (dates are 1st of month)
            
        Returns:
            DataFrame with daily data
        """
        # Load weekly weights (cached at class level)
        if InventorySimulator._weekly_weights_cache is None:
            typical_month_path = 'typical_month.csv'
            
            try:
                InventorySimulator._weekly_weights_cache = calculate_weekly_weights_from_daily(typical_month_path)
                print(f"   ✓ Loaded weekly weights for {InventorySimulator._weekly_weights_cache['key'].nunique()} keys (cached)")
                use_weekly_weights = True
            except Exception as e:
                print(f"   ⚠️ Could not load weekly weights: {e}")
                print(f"   Falling back to simple daily average")
                InventorySimulator._weekly_weights_cache = pd.DataFrame()  # Empty cache
                use_weekly_weights = False
        else:
            # Use cached weights
            use_weekly_weights = len(InventorySimulator._weekly_weights_cache) > 0
        
        weekly_weights_df = InventorySimulator._weekly_weights_cache
        
        daily_records = []
        
        for _, row in df_monthly.iterrows():
            month_start = pd.to_datetime(row['date'])
            year = month_start.year
            month = month_start.month
            key = row['key']
            monthly_offtake = row['Offtake_Units']
            
            # Get number of days in this month
            if month == 12:
                next_month = month_start.replace(year=year+1, month=1, day=1)
            else:
                next_month = month_start.replace(month=month+1, day=1)
            
            days_in_month = (next_month - month_start).days
            
            if use_weekly_weights:
                # Get weekly weights for this key
                key_weights = weekly_weights_df[weekly_weights_df['key'] == key]
                
                if len(key_weights) == 0:
                    # Fallback: simple average for keys not in typical_month.csv
                    daily_offtake = monthly_offtake / days_in_month
                    
                    for day_offset in range(days_in_month):
                        daily_date = month_start + timedelta(days=day_offset)
                        daily_records.append({
                            'date': daily_date,
                            'key': key,
                            'Offtake_Units': daily_offtake
                        })
                else:
                    # Use weekly weights to distribute monthly offtake
                    # Create mapping: day_of_month -> week_of_month
                    def get_week_of_month(day):
                        if day <= 7:
                            return 1
                        elif day <= 14:
                            return 2
                        elif day <= 21:
                            return 3
                        elif day <= 28:
                            return 4
                        else:
                            return 5
                    
                    # For each day, assign to week and distribute accordingly
                    for day_offset in range(days_in_month):
                        daily_date = month_start + timedelta(days=day_offset)
                        day_of_month = daily_date.day
                        week_num = get_week_of_month(day_of_month)
                        
                        # Get weight for this week
                        week_weight_row = key_weights[key_weights['week_of_month'] == week_num]
                        
                        if len(week_weight_row) > 0:
                            week_weight = week_weight_row.iloc[0]['weight']
                            
                            # Calculate how many days are in this week for this month
                            days_in_week = sum(1 for d in range(days_in_month) 
                                             if get_week_of_month((month_start + timedelta(days=d)).day) == week_num)
                            
                            # Daily offtake = (monthly_total * week_weight) / days_in_that_week
                            daily_offtake = (monthly_offtake * week_weight) / days_in_week
                        else:
                            # Fallback if week not found
                            daily_offtake = monthly_offtake / days_in_month
                        
                        daily_records.append({
                            'date': daily_date,
                            'key': key,
                            'Offtake_Units': daily_offtake
                        })
            else:
                # Simple average fallback
                daily_offtake = monthly_offtake / days_in_month
                
                for day_offset in range(days_in_month):
                    daily_date = month_start + timedelta(days=day_offset)
                    
                    daily_record = {
                        'date': daily_date,
                        'key': key,
                        'Offtake_Units': daily_offtake
                    }
                    
                    daily_records.append(daily_record)
        
        df_daily = pd.DataFrame(daily_records)
        print(f"   Disaggregated {len(df_monthly)} monthly records to {len(df_daily)} daily records")
        
        return df_daily
    
    def simulate_sku(self,
                     sku_id: str,
                     avg_daily_demand: float,
                     safety_stock: float,
                     initial_inventory: float,
                     start_date: datetime,
                     days: int = DEFAULT_SIMULATION_DAYS) -> pd.DataFrame:
        """
        Run simulation for a single key.
        
        Args:
            sku_id: Key identifier
            avg_daily_demand: Average daily demand
            safety_stock: Safety stock quantity
            initial_inventory: Starting inventory level
            start_date: Simulation start date
            days: Number of days to simulate
            
        Returns:
            DataFrame with daily simulation results
        """
        # Calculate ROP
        rop = self.rop_calculator.calculate_reorder_point(avg_daily_demand, safety_stock)
        
        # Initialize tracking
        simulation_log = []
        in_transit_orders = {}  # {delivery_date: quantity}
        
        current_inventory = initial_inventory
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Step 1: Receive incoming stock
            received_qty = in_transit_orders.get(current_date, 0)
            current_inventory += received_qty
            
            # Step 2: Subtract demand
            daily_demand = avg_daily_demand  # Could add variability here
            current_inventory -= daily_demand
            
            # Step 3: Calculate net inventory (current + in-transit)
            in_transit_qty = sum(in_transit_orders.values())
            net_inventory = current_inventory + in_transit_qty
            
            # Step 4: Check replenishment trigger
            # Only place order if net inventory hits ROP AND no orders are currently in transit
            order_placed = False
            order_qty = 0
            
            if net_inventory <= rop and in_transit_qty == 0:
                # Calculate order quantity
                order_qty_raw = self.rop_calculator.calculate_order_quantity(
                    avg_daily_demand,
                    current_inventory,
                    safety_stock,
                    in_transit_qty
                )
                
                # Apply case pack constraint
                order_qty = self.rop_calculator.apply_case_pack_constraint(
                    order_qty_raw,
                    self.case_pack
                )
                
                if order_qty > 0:
                    order_placed = True
                    delivery_date = current_date + timedelta(days=self.lead_time_days)
                    
                    # Add to in-transit orders
                    if delivery_date in in_transit_orders:
                        in_transit_orders[delivery_date] += order_qty
                    else:
                        in_transit_orders[delivery_date] = order_qty
            
            # Clean up delivered orders
            if current_date in in_transit_orders:
                del in_transit_orders[current_date]
            
            # Log daily state
            simulation_log.append({
                'date': current_date,
                'day': day + 1,
                'beginning_inventory': current_inventory + daily_demand - received_qty,
                'received_qty': received_qty,
                'demand': daily_demand,
                'ending_inventory': current_inventory,
                'in_transit_qty': in_transit_qty,
                'net_inventory': net_inventory,
                'rop': rop,
                'safety_stock': safety_stock,
                'order_placed': order_placed,
                'order_qty': order_qty if order_placed else 0,
                'stockout': 1 if current_inventory < 0 else 0
            })
        
        # Convert to DataFrame
        df_simulation = pd.DataFrame(simulation_log)
        df_simulation['key'] = sku_id
        
        return df_simulation
        
    def simulate_multiple_skus(self,
                               df_sku_stats: pd.DataFrame,
                               start_date: datetime,
                               initial_inventory_multiplier: float = 2.0,
                               days: int = DEFAULT_SIMULATION_DAYS) -> pd.DataFrame:
        """
        Run simulation for multiple keys.
        
        Args:
            df_sku_stats: DataFrame with key statistics and safety stock
            start_date: Simulation start date
            initial_inventory_multiplier: Multiplier for initial inventory (× avg daily demand)
            days: Number of days to simulate
            
        Returns:
            Combined DataFrame with all SKU simulations
        """
        all_simulations = []
        
        for _, row in df_sku_stats.iterrows():
            # Set initial inventory
            initial_inv = row['avg_daily_demand'] * initial_inventory_multiplier
            
            # Run simulation
            df_sim = self.simulate_sku(
                sku_id=row['key'],
                avg_daily_demand=row['avg_daily_demand'],
                safety_stock=row['safety_stock'],
                initial_inventory=initial_inv,
                start_date=start_date,
                days=days
            )
            
            all_simulations.append(df_sim)
        
        # Combine all simulations
        df_combined = pd.concat(all_simulations, ignore_index=True)
        
        return df_combined
    
    def simulate_with_february_forecast(self,
                                        df_clean: pd.DataFrame,
                                        df_inventory: pd.DataFrame,
                                        initial_inventory_multiplier: float = 1.5) -> pd.DataFrame:
        """
        Run simulation using actual December 2025, January 2026, and February 2026 forecast data.
        
        Filters data for Dec 2025 - Feb 2026, uses actual Offtake_Units as daily forecast.
        
        Args:
            df_clean: Cleaned daily data with date, key, Offtake_Units
            df_inventory: DataFrame with safety_stock and reorder_point per key
            initial_inventory_multiplier: Multiplier for initial inventory
            
        Returns:
            Combined DataFrame with all key simulations
        """
        # Filter for December 2025, January 2026, and February 2026
        df_work = df_clean.copy()
        df_work['date'] = pd.to_datetime(df_work['date'])
        
        # Debug: Check source data
        print(f"\n📊 Source Data Analysis:")
        print(f"   Total rows: {len(df_work)}")
        print(f"   Total unique dates: {df_work['date'].nunique()}")
        print(f"   Date range: {df_work['date'].min()} to {df_work['date'].max()}")
        
        # Check if data is monthly (all dates are 1st of month)
        is_monthly = (df_work['date'].dt.day == 1).all()
        
        if is_monthly:
            print(f"   ⚠️ Data is MONTHLY - disaggregating to daily...")
            df_daily = self._disaggregate_to_daily(df_work)
        else:
            print(f"   ✓ Data is already daily")
            df_daily = df_work
        
        # Filter for November 2025, December 2025, January 2026
        df_sim_months = df_daily[
            ((df_daily['date'].dt.year == 2025) & (df_daily['date'].dt.month.isin([11, 12]))) |
            ((df_daily['date'].dt.year == 2026) & (df_daily['date'].dt.month == 1))
        ].copy()
        
        if len(df_sim_months) == 0:
            print("⚠️ No Nov 2025 - Jan 2026 data found. Trying any Nov-Jan...")
            df_sim_months = df_daily[df_daily['date'].dt.month.isin([11, 12, 1])].copy()
        
        if len(df_sim_months) == 0:
            print("⚠️ No Dec-Feb data found. Using all available data...")
            df_sim_months = df_daily.copy()
        
        unique_dates = df_sim_months['date'].dt.date.nunique()
        print(f"📅 Using {len(df_sim_months)} records spanning {unique_dates} unique dates")
        print(f"   Date range: {df_sim_months['date'].min()} to {df_sim_months['date'].max()}")
        
        all_simulations = []
        
        keys_processed = 0
        for key_id in df_inventory['key'].unique():
            # Get forecast data for this key
            df_key_forecast = df_sim_months[df_sim_months['key'] == key_id][['date', 'Offtake_Units']].copy()
            
            if len(df_key_forecast) == 0:
                print(f"⚠️ No forecast data for key: {key_id}")
                continue
            
            # Debug: Show what data we have for first few keys
            if keys_processed < 3:
                print(f"\n🔑 Key: {key_id}")
                print(f"  - Forecast records: {len(df_key_forecast)}")
                print(f"  - Unique dates: {df_key_forecast['date'].nunique()}")
                print(f"  - Date range: {df_key_forecast['date'].min()} to {df_key_forecast['date'].max()}")
                print(f"  - Demand range: {df_key_forecast['Offtake_Units'].min():.1f} to {df_key_forecast['Offtake_Units'].max():.1f}")
                print(f"  - First 5 rows:")
                print(df_key_forecast.head().to_string())
            
            # Get safety stock and ROP for this key
            key_data = df_inventory[df_inventory['key'] == key_id].iloc[0]
            safety_stock = key_data['safety_stock']
            reorder_point = key_data['reorder_point']
            avg_daily_demand = key_data.get('avg_daily_demand', 100)
            
            # Calculate actual daily demand from the forecast data (Dec 2025 - Feb 2026)
            actual_daily_demand = df_key_forecast['Offtake_Units'].mean()
            
            # Set initial inventory: Use actual daily demand
            # Formula: max(actual_daily_demand * 7, safety_stock * 2)
            initial_inventory = max(actual_daily_demand * 7, safety_stock * 2)
            
            if keys_processed < 3:
                print(f"  - Avg Daily Demand (from stats): {avg_daily_demand:.1f}")
                print(f"  - Actual Daily Demand (Dec-Feb): {actual_daily_demand:.1f}")
                print(f"  - Safety Stock: {safety_stock:.1f}")
                print(f"  - ROP: {reorder_point:.1f}")
                print(f"  - Initial Inventory Calc: max({actual_daily_demand:.1f} * 7, {safety_stock:.1f} * 2)")
                print(f"                          = max({actual_daily_demand * 7:.1f}, {safety_stock * 2:.1f})")
                print(f"                          = {initial_inventory:.1f}")
            
            # Run simulation with actual forecast
            df_sim = self.simulate_with_actual_forecast(
                key_id=key_id,
                df_daily_forecast=df_key_forecast,
                reorder_point=reorder_point,
                safety_stock=safety_stock,
                initial_inventory=initial_inventory,
                case_pack=self.case_pack
            )
            
            all_simulations.append(df_sim)
            keys_processed += 1
        
        # Combine all simulations
        if all_simulations:
            df_combined = pd.concat(all_simulations, ignore_index=True)
            print(f"\n✅ Simulation complete: {keys_processed} keys processed")
            print(f"   Total simulation records: {len(df_combined)}")
            return df_combined
        else:
            raise ValueError("No simulations generated. Check if keys match between datasets.")


def calculate_inventory_metrics(df_sku_stats: pd.DataFrame,
                                service_level: float = DEFAULT_SERVICE_LEVEL,
                                lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
                                lead_time_std: float = 2.0) -> pd.DataFrame:
    """
    Calculate safety stock and ROP for all keys.
    
    Args:
        df_sku_stats: DataFrame with key statistics
        service_level: Desired service level
        lead_time_days: Average lead time
        lead_time_std: Standard deviation of lead time
        
    Returns:
        DataFrame with safety stock and ROP
    """
    # Calculate safety stock
    ss_calculator = SafetyStockCalculator(service_level, lead_time_days, lead_time_std)
    df_with_ss = ss_calculator.calculate_for_dataframe(df_sku_stats)
    
    # Calculate ROP
    rop_calculator = ReorderPointCalculator(lead_time_days)
    df_with_ss['reorder_point'] = df_with_ss.apply(
        lambda row: rop_calculator.calculate_reorder_point(
            row['avg_daily_demand'],
            row['safety_stock']
        ),
        axis=1
    )
    
    df_with_ss['reorder_point'] = np.ceil(df_with_ss['reorder_point']).astype(int)
    
    return df_with_ss
