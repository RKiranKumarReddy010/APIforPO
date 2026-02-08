# Inventory Planning Dashboard

A fully automated Streamlit dashboard for dynamic safety stock calculation and 90-day inventory simulation.

## Overview

This application helps inventory planners:
- Calculate dynamic safety stock using statistical methods
- Simulate inventory levels over 90 days
- Optimize reorder points and quantities
- Minimize stockouts while controlling inventory costs

## Features

### 1. Data Validation
- Schema validation against expected columns
- Data quality checks (missing values, duplicates, outliers)
- Detailed quality reports with actionable insights

### 2. Data Processing
- Automatic data type standardization
- Missing value handling
- Weekly demand aggregation
- SKU-level statistical analysis

### 3. Safety Stock Calculation
Uses the industry-standard formula:

$$SS = Z \times \sqrt{(L_{avg} \times \sigma_{Demand}^2) + (D_{avg}^2 \times \sigma_{LeadTime}^2)}$$

Where:
- **Z**: Service level coefficient (e.g., 1.96 for 97.5%)
- **L_avg**: Average lead time
- **σ_Demand**: Standard deviation of demand
- **D_avg**: Average daily demand
- **σ_LeadTime**: Standard deviation of lead time

### 4. 90-Day Simulation
Deterministic simulation following this algorithm:

For each day t ∈ [1, 90]:
1. **Inventory Update**: I_t = I_{t-1} - D_t + R_t
2. **Net Requirement**: Net_Inv = I_t + Σ(In-Transit POs)
3. **Replenishment Trigger**: if Net_Inv ≤ ROP:
   - Calculate Order Quantity (Q)
   - Apply Case Pack Constraint
   - Set Delivery Date: R_{t+LeadTime}

### 5. Interactive Visualizations
- Demand distribution analysis
- Safety stock breakdown
- Inventory level trends
- Stockout tracking
- Order placement visualization

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the dashboard:
```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## Usage

### 1. Upload Dataset
Upload a CSV or Excel file with the following required columns:
- `date`: Transaction date
- `SKU ID`: Product identifier
- `Offtake_Units`: Demand/sales quantity

Optional columns for enhanced analysis:
- Categorical: Chain, Channel, Region, Brand, etc.
- Promotional events: prime_day, bbd, eoss, etc.
- Lag features and moving averages

### 2. Validate Data
- Review validation report
- Check for critical errors
- Review warnings and data quality metrics

### 3. Configure Parameters
In the sidebar, set:
- **Service Level**: Target availability (90%, 95%, 97.5%, 99%, 99.5%)
- **Lead Time**: Average and standard deviation
- **Coverage Days**: Inventory coverage when ordering
- **Case Pack Size**: Units per case for rounding

### 4. Process & Analyze
- Process data to clean and aggregate
- Review demand statistics
- Analyze demand variability (CV)

### 5. Calculate Safety Stock
- Calculate safety stock for all SKUs
- Review reorder points
- Export results

### 6. Run Simulation
- Execute 90-day simulation
- Analyze stockout patterns
- Review order frequency
- Drill down into specific SKUs

### 7. Export Results
Download processed data:
- Weekly demand aggregation
- SKU statistics
- Safety stock calculations
- Simulation results

## File Structure

```
Reorder point/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── config/
│   └── config.py              # Configuration constants
│
├── src/
│   ├── data_validator.py      # Schema and quality validation
│   ├── data_processor.py      # Data cleaning and aggregation
│   ├── inventory_calculator.py # Safety stock and simulation
│   └── visualizations.py      # Chart creation
│
├── utils/
│   └── helpers.py             # Utility functions
│
├── data/                       # Place input datasets here
└── outputs/                    # Exported results
```

## Business Logic

### Safety Stock Calculation
The calculator considers two sources of variability:
1. **Demand variability** during lead time
2. **Lead time variability** with average demand

This approach ensures buffer stock accounts for uncertainty in both forecasts and supplier reliability.

### Reorder Point (ROP)
```
ROP = (Average Daily Demand × Lead Time) + Safety Stock
```

### Order Quantity
```
Q = (Daily Demand × Coverage Days) + Safety Stock - Net Inventory
```

Net Inventory = Current Inventory + In-Transit Orders

### Case Pack Rounding
Order quantities are rounded up to the nearest case pack to comply with supplier constraints.

## Key Metrics

### Coefficient of Variation (CV)
Measures demand volatility:
- **CV < 0.25**: Low variability (predictable demand)
- **0.25 ≤ CV < 0.5**: Moderate variability
- **CV ≥ 0.5**: High variability (erratic demand)

### Service Level Achieved
Percentage of days without stockouts during simulation:
```
Service Level = (Total Days - Stockout Days) / Total Days × 100%
```

## Troubleshooting

### Data Upload Issues
- Ensure file is CSV or Excel format
- Check column names match expected schema
- Verify date column can be parsed

### Validation Errors
- Review critical column requirements
- Check for excessive missing values (>20%)
- Ensure SKU ID and date are present

### Calculation Issues
- Verify SKUs have sufficient historical data (≥12 weeks)
- Check for negative or zero demand values
- Review lead time and coverage parameters

## Customization

### Adding New Event Columns
Update `config/config.py`:
```python
EVENT_COLUMNS = [
    'gif', 'prime_day', 'your_new_event', ...
]
```

### Changing Service Levels
Modify `SERVICE_LEVELS` in `config/config.py` or use the sidebar dropdown.

### Adjusting Simulation Logic
Edit `InventorySimulator` class in [src/inventory_calculator.py](src/inventory_calculator.py)

## Performance Notes

- Dashboard handles datasets with 100K+ rows efficiently
- Processing time depends on number of unique SKUs
- Simulation time scales linearly with SKUs × Days

## Data Privacy

- All processing happens locally
- No data is sent to external servers
- Uploaded files are only stored in browser session

## Support

For issues or questions:
1. Review this README
2. Check validation and processing logs
3. Verify input data format
4. Review error messages in the dashboard

## Version History

**v1.0.0** - Initial release
- Complete data validation pipeline
- Dynamic safety stock calculation
- 90-day inventory simulation
- Interactive visualizations
- Export functionality

## License

Proprietary - Intellimark Internal Use

---

**Built with:** Python, Streamlit, Pandas, NumPy, Plotly, SciPy
