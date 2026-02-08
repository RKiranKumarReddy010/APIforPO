# API Quick Reference Guide

## Base URL
```
http://localhost:5000
```

## Common Headers
```
Content-Type: application/json
Origin: your-frontend-domain
```

---

## Quick Endpoints Reference

### Health & Config
```bash
# Check server status
GET /api/health

# Get default configuration
GET /api/config
```

### File Operations
```bash
# Upload file (multipart/form-data)
POST /api/upload
Body: form-data with 'file' field

# Validate file
POST /api/validate
Body: { "filepath": "/uploads/..." }

# Process data
POST /api/process-data
Body: { "filepath": "/uploads/..." }
```

### Single SKU Analysis
```bash
# Calculate safety stock
POST /api/calculate-safety-stock
Body: {
  "filepath": "/uploads/...",
  "sku_id": "SKU12345",
  "service_level": 0.975,
  "lead_time_days": 7,
  "lead_time_std": 1.5
}

# Simulate inventory
POST /api/simulate-inventory
Body: {
  "filepath": "/uploads/...",
  "sku_id": "SKU12345",
  "initial_inventory": 100,
  "reorder_point": 50,
  "service_level": 0.975,
  "lead_time_days": 7,
  "coverage_days": 30,
  "case_pack": 10,
  "simulation_days": 90
}
```

### Batch Operations
```bash
# Calculate for multiple SKUs
POST /api/batch-calculate
Body: {
  "filepath": "/uploads/...",
  "sku_ids": ["SKU1", "SKU2", "SKU3"],
  "service_level": 0.975,
  "lead_time_days": 7
}
```

---

## Default Parameter Values

| Parameter | Default | Range |
|-----------|---------|-------|
| service_level | 0.975 | 0.90 - 0.995 |
| lead_time_days | 7 | Any positive number |
| lead_time_std | 1.5 | Any positive number |
| coverage_days | 7 | Any positive number |
| case_pack | 12 | Any positive integer |
| simulation_days | 90 | Any positive integer |
| initial_inventory | 100 | Any non-negative number |
| reorder_point | 50 | Any non-negative number |

---

## Service Level Quick Lookup

| Level | Z-Score | Stockout Risk | Use Case |
|-------|---------|---------------|----------|
| 0.90 | 1.28 | 10% | Low-priority items |
| 0.95 | 1.65 | 5% | Standard items |
| **0.975** | **1.96** | **2.5%** | **Default** |
| 0.99 | 2.33 | 1% | High-demand items |
| 0.995 | 2.58 | 0.5% | Critical items |

---

## JavaScript Fetch Examples

### Simple Upload
```javascript
const formData = new FormData();
formData.append('file', file);

const res = await fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
});
const data = await res.json();
```

### Safety Stock Calculation
```javascript
const res = await fetch(
  'http://localhost:5000/api/calculate-safety-stock',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filepath: '/uploads/file.csv',
      sku_id: 'SKU12345',
      service_level: 0.975
    })
  }
);
const result = await res.json();
console.log(result.safety_stock);
```

### Batch Calculate
```javascript
const res = await fetch('http://localhost:5000/api/batch-calculate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filepath: '/uploads/file.csv',
    sku_ids: ['SKU1', 'SKU2', 'SKU3'],
    service_level: 0.975
  })
});
const results = await res.json();
results.results.forEach(r => {
  console.log(`${r.sku_id}: ${r.safety_stock}`);
});
```

---

## Common Error Codes & Fixes

| Error | Status | Fix |
|-------|--------|-----|
| No file provided | 400 | Add 'file' to multipart form |
| File type not allowed | 400 | Use .csv, .xlsx, or .xls |
| File too large | 413 | Upload file < 50MB |
| File not found | 404 | Check filepath is correct |
| No data found for SKU | 404 | Verify SKU ID exists in data |
| No demand data | 400 | Ensure Units/Qty column exists |

---

## Response JSON Structure

### Success Response
```json
{
  "success": true,
  "message": "...",
  "data": { ... },
  "timestamp": "2026-02-08T10:30:45.123456"
}
```

### Error Response
```json
{
  "error": "Error message here",
  "status": 400
}
```

---

## File Upload Workflow

```
1. User selects file
2. POST /api/upload → Get filepath
3. POST /api/validate → Confirm data quality
4. POST /api/process-data → Get statistics
5. Save filepath for calculations
```

---

## Performance Tips

- **Batch processing** for 10+ SKUs
- **Cache filepath** after upload
- **Parallel requests** with Promise.all()
- **Check health** (`/api/health`) before operations
- **Monitor file size** (keep < 50MB)

---

## Testing Checklist

- [ ] Server health check passes
- [ ] File uploads successfully
- [ ] Data validates without errors
- [ ] Safety stock calculated correctly
- [ ] Simulation completes without errors
- [ ] Batch operations handle errors gracefully
- [ ] Error messages are helpful and accurate

---

## Required Data Columns

### Minimum Required
- `date`
- `key`
- `Offtake_Units` (or `Units/Qty`)

### For SKU Analysis
- `SKU ID`
- `Units/Qty` or `Offtake_Units` (demand)
- `Chain`, `Channel`, `Region` (optional)

---

## Common Calculations

### Safety Stock Formula
```
SS = Z × σd × √(L + σl²)

Where:
  Z = Z-score for service level
  σd = Standard deviation of demand
  L = Lead time (days)
  σl = Lead time standard deviation
```

### Reorder Point Formula
```
ROP = (d × L) + SS

Where:
  d = Average daily demand
  L = Lead time (days)
  SS = Safety stock
```

---

*Last Updated: February 8, 2026*
