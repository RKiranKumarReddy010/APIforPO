# Inventory Planning Dashboard - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [API Endpoints](#api-endpoints)
4. [Data Upload](#data-upload)
5. [Safety Stock Calculation](#safety-stock-calculation)
6. [Inventory Simulation](#inventory-simulation)
7. [Batch Processing](#batch-processing)
8. [Configuration & Defaults](#configuration--defaults)
9. [Error Handling](#error-handling)
10. [Example Workflows](#example-workflows)

---

## Overview

The Inventory Planning Dashboard API provides REST endpoints for calculating optimal reorder points, simulating inventory levels, and processing inventory data. The server is built with Flask and supports data uploads in CSV and Excel formats.

**Server**: Flask REST API
**Base URL**: `http://localhost:5000`
**Port**: 5000
**CORS**: Enabled (cross-origin requests supported)

---

## Getting Started

### Prerequisites
- Node.js/JavaScript framework (React, Vue, Angular, etc.)
- API client (fetch API, Axios, etc.)
- CSV or Excel file with inventory data

### Health Check

Before making API calls, verify the server is running:

```http
GET /api/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "message": "Inventory Planning Server is running",
  "timestamp": "2026-02-08T10:30:45.123456"
}
```

### Get Configuration

Retrieve default configuration values:

```http
GET /api/config
```

**Response** (200 OK):
```json
{
  "default_service_level": 0.975,
  "default_lead_time_days": 7,
  "default_coverage_days": 7,
  "default_case_pack": 12,
  "available_service_levels": {
    "0.90": 1.28,
    "0.95": 1.65,
    "0.975": 1.96,
    "0.99": 2.33,
    "0.995": 2.58
  }
}
```

---

## API Endpoints

### Summary Table

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Check server status |
| GET | `/api/config` | Get default configuration |
| POST | `/api/upload` | Upload and validate data file |
| POST | `/api/validate` | Validate uploaded file |
| POST | `/api/process-data` | Process raw data |
| POST | `/api/calculate-safety-stock` | Calculate safety stock for SKU |
| POST | `/api/simulate-inventory` | Simulate inventory for 90 days |
| POST | `/api/batch-calculate` | Calculate metrics for multiple SKUs |

---

## Data Upload

### Upload File

Upload a CSV or Excel file containing inventory data.

**Endpoint**:
```http
POST /api/upload
Content-Type: multipart/form-data
```

**Request**:
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
});
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "20260208_103045_inventory_data.csv",
  "filepath": "/uploads/20260208_103045_inventory_data.csv",
  "shape": [1000, 45],
  "columns": [
    "date", "key", "SKU ID", "Units/Qty", "Offtake_Units", 
    "Chain", "Channel", "Region", "...more columns"
  ],
  "validation": {
    "is_valid": true,
    "warnings": [],
    "errors": []
  },
  "rows": 1000,
  "columns_count": 45
}
```

**Supported File Types**: `.csv`, `.xlsx`, `.xls`
**Max File Size**: 50 MB

**Error Responses**:

```json
// Missing file
{ "error": "No file provided" }  // 400

// Invalid file type
{ 
  "error": "File type not allowed. Allowed types: csv, xlsx, xls" 
}  // 400

// File too large
{ "error": "File too large (max 50MB)" }  // 413
```

---

### Validate Data

Validate an uploaded file and get detailed quality report.

**Endpoint**:
```http
POST /api/validate
Content-Type: application/json
```

**Request**:
```javascript
const response = await fetch('http://localhost:5000/api/validate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    filepath: '/uploads/20260208_103045_inventory_data.csv'
  })
});
```

**Response** (200 OK):
```json
{
  "success": true,
  "filepath": "/uploads/20260208_103045_inventory_data.csv",
  "validation": {
    "is_valid": true,
    "warnings": [],
    "errors": []
  },
  "data_summary": {
    "rows": 1000,
    "columns": 45,
    "column_names": ["date", "key", "SKU ID", ...],
    "dtypes": {
      "date": "object",
      "Units/Qty": "float64",
      "Offtake_Units": "float64",
      "SKU ID": "object"
    },
    "missing_values": {
      "date": 0,
      "Units/Qty": 5,
      "Offtake_Units": 2
    }
  }
}
```

**Error Response** (404):
```json
{ "error": "File not found" }
```

---

### Process Data

Process raw data and generate statistics.

**Endpoint**:
```http
POST /api/process-data
Content-Type: application/json
```

**Request**:
```javascript
const response = await fetch('http://localhost:5000/api/process-data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    filepath: '/uploads/20260208_103045_inventory_data.csv'
  })
});
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Data processed successfully",
  "statistics": {
    "original_rows": 1000,
    "processed_rows": 950,
    "columns": ["date", "SKU ID", "demand", "lead_time", ...],
    "summary_statistics": {
      "Units/Qty": {
        "count": 950,
        "mean": 45.67,
        "std": 12.34,
        "min": 5,
        "25%": 35,
        "50%": 45,
        "75%": 55,
        "max": 95
      },
      "Offtake_Units": {
        "count": 950,
        "mean": 42.15,
        "std": 11.89,
        "min": 3,
        "25%": 32,
        "50%": 42,
        "75%": 52,
        "max": 92
      }
    }
  }
}
```

---

## Safety Stock Calculation

### Calculate Safety Stock for Single SKU

Calculate the optimal safety stock level for a specific SKU.

**Endpoint**:
```http
POST /api/calculate-safety-stock
Content-Type: application/json
```

**Request Parameters**:
```javascript
{
  "filepath": "/uploads/20260208_103045_inventory_data.csv",
  "sku_id": "SKU12345",                    // Required
  "service_level": 0.975,                  // Optional (default: 0.975)
  "lead_time_days": 7,                     // Optional (default: 7)
  "lead_time_std": 1.5                     // Optional (default: 1.5)
}
```

**Example Request**:
```javascript
const response = await fetch('http://localhost:5000/api/calculate-safety-stock', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath: '/uploads/20260208_103045_inventory_data.csv',
    sku_id: 'SKU12345',
    service_level: 0.975,
    lead_time_days: 7,
    lead_time_std: 1.5
  })
});
```

**Response** (200 OK):
```json
{
  "success": true,
  "safety_stock": 156.78,
  "sku_id": "SKU12345",
  "service_level": 0.975,
  "lead_time_days": 7,
  "demand_mean": 45.67,
  "demand_std": 12.34,
  "demand_count": 120,
  "calculation_date": "2026-02-08T10:45:30.123456"
}
```

**Service Level Values & Z-Scores**:
| Service Level | Z-Score | Explanation |
|---------------|---------|-------------|
| 0.90 | 1.28 | 90% service level (10% stockout risk) |
| 0.95 | 1.65 | 95% service level (5% stockout risk) |
| 0.975 | 1.96 | 97.5% service level (2.5% stockout risk) - **Default** |
| 0.99 | 2.33 | 99% service level (1% stockout risk) |
| 0.995 | 2.58 | 99.5% service level (0.5% stockout risk) |

**Error Responses**:
```json
// File not found
{ "error": "File not found" }  // 404

// SKU not found
{ "error": "No data found for SKU: SKU99999" }  // 404

// No demand data
{ "error": "No demand data available" }  // 400
```

---

## Inventory Simulation

### Simulate Inventory

Simulate inventory levels for 90 days (or custom period) with given parameters.

**Endpoint**:
```http
POST /api/simulate-inventory
Content-Type: application/json
```

**Request Parameters**:
```javascript
{
  "filepath": "/uploads/20260208_103045_inventory_data.csv",
  "sku_id": "SKU12345",                    // Required
  "initial_inventory": 100,                // Optional (default: 100)
  "reorder_point": 50,                     // Optional (default: 50)
  "service_level": 0.975,                  // Optional (default: 0.975)
  "lead_time_days": 7,                     // Optional (default: 7)
  "coverage_days": 30,                     // Optional (default: 7)
  "case_pack": 10,                         // Optional (default: 12)
  "simulation_days": 90                    // Optional (default: 90)
}
```

**Example Request**:
```javascript
const response = await fetch('http://localhost:5000/api/simulate-inventory', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath: '/uploads/20260208_103045_inventory_data.csv',
    sku_id: 'SKU12345',
    initial_inventory: 100,
    reorder_point: 50,
    service_level: 0.975,
    lead_time_days: 7,
    coverage_days: 30,
    case_pack: 10,
    simulation_days: 90
  })
});
```

**Response** (200 OK):
```json
{
  "success": true,
  "sku_id": "SKU12345",
  "simulation_days": 90,
  "initial_inventory": 100,
  "reorder_point": 50,
  "metrics": {
    "stockout_probability": 0.025,
    "service_level": 0.975,
    "reorder_frequency": 12,
    "avg_order_quantity": 120,
    "inventory_turnover": 3.5,
    "holding_cost_ratio": 0.18
  },
  "results_summary": {
    "total_days": 90,
    "final_inventory": 78,
    "avg_inventory": 65.4,
    "stock_outs": 2
  },
  "simulation_date": "2026-02-08T10:50:15.123456"
}
```

**Parameter Explanations**:
- **initial_inventory**: Starting inventory level
- **reorder_point**: Inventory level at which to trigger reorder
- **service_level**: Target service level (0.90 to 0.995)
- **lead_time_days**: Days required to receive order after reordering
- **coverage_days**: Days of demand to cover with safety stock
- **case_pack**: Quantity per case (for order quantity calculation)
- **simulation_days**: Number of days to simulate (typical: 90)

**Interpretation of Results**:
- **stockout_probability**: Probability of running out of stock (1 - service_level)
- **reorder_frequency**: Estimated number of reorders over simulation period
- **avg_order_quantity**: Average quantity per order (rounded to case pack)
- **stock_outs**: Number of days inventory dropped below zero

---

## Batch Processing

### Batch Calculate Safety Stock

Calculate safety stock for multiple SKUs in one request (optimized for bulk operations).

**Endpoint**:
```http
POST /api/batch-calculate
Content-Type: application/json
```

**Request Parameters**:
```javascript
{
  "filepath": "/uploads/20260208_103045_inventory_data.csv",
  "sku_ids": ["SKU12345", "SKU67890", "SKU11111"],
  "service_level": 0.975,                  // Optional (default: 0.975)
  "lead_time_days": 7                      // Optional (default: 7)
}
```

**Example Request**:
```javascript
const response = await fetch('http://localhost:5000/api/batch-calculate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath: '/uploads/20260208_103045_inventory_data.csv',
    sku_ids: ['SKU12345', 'SKU67890', 'SKU11111'],
    service_level: 0.975,
    lead_time_days: 7
  })
});
```

**Response** (200 OK):
```json
{
  "success": true,
  "total_skus": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "sku_id": "SKU12345",
      "status": "success",
      "safety_stock": 156.78,
      "demand_mean": 45.67,
      "demand_std": 12.34
    },
    {
      "sku_id": "SKU67890",
      "status": "success",
      "safety_stock": 203.45,
      "demand_mean": 58.92,
      "demand_std": 15.67
    },
    {
      "sku_id": "SKU11111",
      "status": "success",
      "safety_stock": 89.23,
      "demand_mean": 28.56,
      "demand_std": 8.92
    }
  ],
  "timestamp": "2026-02-08T11:00:45.123456"
}
```

**Partial Failure Response** (200 OK):
```json
{
  "success": true,
  "total_skus": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "sku_id": "SKU12345",
      "status": "success",
      "safety_stock": 156.78,
      "demand_mean": 45.67,
      "demand_std": 12.34
    },
    {
      "sku_id": "SKU67890",
      "status": "error",
      "message": "No demand data"
    },
    {
      "sku_id": "SKU11111",
      "status": "success",
      "safety_stock": 89.23,
      "demand_mean": 28.56,
      "demand_std": 8.92
    }
  ],
  "timestamp": "2026-02-08T11:00:45.123456"
}
```

**Best Practices for Batch Processing**:
- Use for processing 10+ SKUs to improve performance
- Maximum recommended batch size: 500 SKUs per request
- For larger batches, split into multiple requests
- Results include individual status for each SKU (success/error)

---

## Configuration & Defaults

### Default Configuration Values

The server uses these default values if parameters are not provided:

```javascript
{
  "service_level": 0.975,           // 97.5% (Z = 1.96)
  "lead_time_days": 7,              // 7 days average lead time
  "coverage_days": 7,               // 7 days of demand coverage
  "case_pack": 12,                  // 12 units per case
  "simulation_days": 90             // 90-day simulation
}
```

### Expected Data Schema

The uploaded CSV/Excel file should contain these key columns:

**Required Columns**:
- `date` - Transaction date
- `key` - Product key identifier
- `Offtake_Units` - Demand quantity

**Important Columns for SKU Analysis**:
- `SKU ID` - Stock Keeping Unit identifier
- `Units/Qty` - Alternative demand column
- `Chain` - Retail chain
- `Channel` - Sales channel (online/offline)
- `Region` - Geographic region
- `State` - State/Province
- `Final City` - City
- `L1 Prod Category` - Product category level 1
- `L2 Prod Brand` - Product brand level 2

**Optional Columns**:
- Event flags: `prime_day`, `black_friday`, `republic_sale`, etc.
- Seasonal indicators: `seasonal`, `period`, `seasonality`
- Forecasts: `SARIMA_pred`, `Prophet_pred`, `XGB_pred`, etc.

---

## Error Handling

### Standard Error Responses

**Client Errors (4xx)**:

```json
// 400 Bad Request
{ "error": "No file provided" }
{ "error": "No demand data available" }

// 404 Not Found
{ "error": "File not found" }
{ "error": "No data found for SKU: SKU99999" }
{ "error": "Endpoint not found" }

// 413 Payload Too Large
{ "error": "File too large (max 50MB)" }
```

**Server Errors (5xx)**:

```json
// 500 Internal Server Error
{ "error": "Internal server error" }
{ "error": "Error message with details" }
```

### Error Handling Best Practices

```javascript
// Example error handling in JavaScript
async function uploadAndProcess(file) {
  try {
    // Step 1: Upload file
    const uploadResponse = await fetch('http://localhost:5000/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!uploadResponse.ok) {
      const error = await uploadResponse.json();
      console.error('Upload failed:', error.error);
      return;
    }

    const uploadData = await uploadResponse.json();
    const filepath = uploadData.filepath;

    // Step 2: Validate data
    const validateResponse = await fetch(
      'http://localhost:5000/api/validate',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath })
      }
    );

    if (!validateResponse.ok) {
      const error = await validateResponse.json();
      console.error('Validation failed:', error.error);
      return;
    }

    const validationData = await validateResponse.json();
    if (!validationData.validation.is_valid) {
      console.error('Data validation warnings:', 
        validationData.validation.warnings);
    }

    // Step 3: Calculate safety stock
    const calcResponse = await fetch(
      'http://localhost:5000/api/calculate-safety-stock',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filepath,
          sku_id: 'SKU12345',
          service_level: 0.975
        })
      }
    );

    if (!calcResponse.ok) {
      const error = await calcResponse.json();
      console.error('Calculation failed:', error.error);
      return;
    }

    const result = await calcResponse.json();
    console.log('Safety stock:', result.safety_stock);

  } catch (error) {
    console.error('Network error:', error.message);
  }
}
```

---

## Example Workflows

### Workflow 1: Single SKU Analysis

Complete workflow for analyzing a single SKU.

```javascript
// Step 1: Upload file
const formData = new FormData();
formData.append('file', inventoryFile);

const uploadRes = await fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
});
const uploadData = await uploadRes.json();
const filepath = uploadData.filepath;

// Step 2: Validate data
const validateRes = await fetch('http://localhost:5000/api/validate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ filepath })
});
const validation = await validateRes.json();
console.log('Data valid:', validation.validation.is_valid);

// Step 3: Calculate safety stock
const ssRes = await fetch(
  'http://localhost:5000/api/calculate-safety-stock',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filepath,
      sku_id: 'SKU12345',
      service_level: 0.975,
      lead_time_days: 7
    })
  }
);
const safetyStock = await ssRes.json();
console.log('Recommended safety stock:', safetyStock.safety_stock);

// Step 4: Simulate inventory
const simRes = await fetch('http://localhost:5000/api/simulate-inventory', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath,
    sku_id: 'SKU12345',
    initial_inventory: 100,
    reorder_point: safetyStock.safety_stock,
    service_level: 0.975,
    simulation_days: 90
  })
});
const simulation = await simRes.json();
console.log('Stock outs projected:', simulation.results_summary.stock_outs);
```

### Workflow 2: Batch Processing Multiple SKUs

```javascript
// Upload file
const uploadRes = await fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
});
const uploadData = await uploadRes.json();
const filepath = uploadData.filepath;

// Get list of SKUs from your application
const skuList = ['SKU12345', 'SKU67890', 'SKU11111', 'SKU99999'];

// Batch calculate safety stock
const batchRes = await fetch('http://localhost:5000/api/batch-calculate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath,
    sku_ids: skuList,
    service_level: 0.975,
    lead_time_days: 7
  })
});

const results = await batchRes.json();
console.log(`Processed ${results.successful}/${results.total_skus} SKUs`);

// Process results
results.results.forEach(result => {
  if (result.status === 'success') {
    console.log(`${result.sku_id}: Safety Stock = ${result.safety_stock}`);
  } else {
    console.error(`${result.sku_id}: ${result.message}`);
  }
});
```

### Workflow 3: Dashboard with Real-time Updates

```javascript
class InventoryDashboard {
  constructor(apiBaseUrl = 'http://localhost:5000') {
    this.apiBaseUrl = apiBaseUrl;
    this.filepath = null;
  }

  async initialize(file) {
    // Upload file
    const formData = new FormData();
    formData.append('file', file);

    const uploadRes = await fetch(`${this.apiBaseUrl}/api/upload`, {
      method: 'POST',
      body: formData
    });
    const uploadData = await uploadRes.json();
    this.filepath = uploadData.filepath;
  }

  async getConfig() {
    const res = await fetch(`${this.apiBaseUrl}/api/config`);
    return await res.json();
  }

  async analyzeSKU(skuId) {
    // Calculate safety stock
    const ssRes = await fetch(
      `${this.apiBaseUrl}/api/calculate-safety-stock`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filepath: this.filepath,
          sku_id: skuId,
          service_level: 0.975
        })
      }
    );
    const safetyStock = await ssRes.json();

    // Simulate inventory
    const simRes = await fetch(`${this.apiBaseUrl}/api/simulate-inventory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filepath: this.filepath,
        sku_id: skuId,
        initial_inventory: 100,
        reorder_point: safetyStock.safety_stock,
        simulation_days: 90
      })
    });
    const simulation = await simRes.json();

    return {
      skuId,
      safetyStock: safetyStock.safety_stock,
      simulation: simulation.results_summary,
      metrics: simulation.metrics
    };
  }

  async analyzeMultipleSKUs(skuIds) {
    const results = [];
    for (const skuId of skuIds) {
      try {
        const analysis = await this.analyzeSKU(skuId);
        results.push(analysis);
      } catch (error) {
        console.error(`Error analyzing ${skuId}:`, error);
      }
    }
    return results;
  }
}

// Usage
const dashboard = new InventoryDashboard();
await dashboard.initialize(fileInput.files[0]);

const config = await dashboard.getConfig();
console.log('Default service level:', config.default_service_level);

const analysis = await dashboard.analyzeSKU('SKU12345');
console.log('Analysis complete:', analysis);
```

---

## Response Status Codes

| Status | Code | Meaning |
|--------|------|---------|
| Success | 200 | Request successful, check response.success |
| Bad Request | 400 | Invalid parameters or missing required fields |
| Not Found | 404 | File not found or SKU not found |
| Payload Too Large | 413 | File exceeds 50MB limit |
| Server Error | 500 | Internal server error |

---

## Performance Tips

1. **Batch Operations**: Use `/api/batch-calculate` for 10+ SKUs
2. **File Size**: Keep CSV files under 50MB for best performance
3. **Error Handling**: Always check response status before processing data
4. **Caching**: Cache validated file paths to avoid re-uploading
5. **Parallel Requests**: Use Promise.all() for independent calculations
6. **Service Level**: Higher service levels require more safety stock

---

## Support & Troubleshooting

**Server not responding?**
- Check if server is running: `GET /api/health`
- Verify URL and port (default: `http://localhost:5000`)
- Check network connectivity

**File upload fails?**
- Verify file format (CSV, XLSX, XLS only)
- Check file size (max 50MB)
- Ensure file has required columns

**No data found for SKU?**
- Verify SKU ID matches exactly (case-sensitive)
- Check if data was uploaded and validated
- Ensure SKU column name is "SKU ID"

**Invalid calculations?**
- Verify demand data is present in file
- Check service level is between 0.90-0.995
- Ensure lead_time_days > 0

---

*Document Version: 1.0*
*Last Updated: February 8, 2026*
*API Server Version: Flask*
