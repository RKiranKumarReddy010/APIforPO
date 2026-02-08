# Frontend Integration Guide

This guide demonstrates how to integrate the Inventory Planning API with popular frontend frameworks.

## Table of Contents
1. [Vanilla JavaScript](#vanilla-javascript)
2. [React Integration](#react-integration)
3. [Vue.js Integration](#vuejs-integration)
4. [Angular Integration](#angular-integration)

---

## Vanilla JavaScript

### Service Module
```javascript
// inventoryService.js
class InventoryService {
  constructor(baseURL = 'http://localhost:5000') {
    this.baseURL = baseURL;
  }

  async checkHealth() {
    const res = await fetch(`${this.baseURL}/api/health`);
    return res.json();
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch(`${this.baseURL}/api/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) {
      throw new Error(`Upload failed: ${res.statusText}`);
    }
    return res.json();
  }

  async validateData(filepath) {
    const res = await fetch(`${this.baseURL}/api/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath })
    });
    
    if (!res.ok) {
      throw new Error(`Validation failed: ${res.statusText}`);
    }
    return res.json();
  }

  async calculateSafetyStock(filepath, skuId, params = {}) {
    const body = {
      filepath,
      sku_id: skuId,
      service_level: params.serviceLevel || 0.975,
      lead_time_days: params.leadTimeDays || 7,
      lead_time_std: params.leadTimeStd || 1.5
    };

    const res = await fetch(
      `${this.baseURL}/api/calculate-safety-stock`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }
    );

    if (!res.ok) {
      throw new Error(`Calculation failed: ${res.statusText}`);
    }
    return res.json();
  }

  async simulateInventory(filepath, skuId, params = {}) {
    const body = {
      filepath,
      sku_id: skuId,
      initial_inventory: params.initialInventory || 100,
      reorder_point: params.reorderPoint || 50,
      service_level: params.serviceLevel || 0.975,
      lead_time_days: params.leadTimeDays || 7,
      coverage_days: params.coverageDays || 30,
      case_pack: params.casePack || 10,
      simulation_days: params.simulationDays || 90
    };

    const res = await fetch(`${this.baseURL}/api/simulate-inventory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      throw new Error(`Simulation failed: ${res.statusText}`);
    }
    return res.json();
  }

  async batchCalculate(filepath, skuIds, params = {}) {
    const body = {
      filepath,
      sku_ids: skuIds,
      service_level: params.serviceLevel || 0.975,
      lead_time_days: params.leadTimeDays || 7
    };

    const res = await fetch(`${this.baseURL}/api/batch-calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      throw new Error(`Batch calculation failed: ${res.statusText}`);
    }
    return res.json();
  }
}

export default InventoryService;
```

### Usage Example
```javascript
// main.js
import InventoryService from './inventoryService.js';

const service = new InventoryService();

// Upload file
document.getElementById('uploadBtn').addEventListener('click', async () => {
  const file = document.getElementById('fileInput').files[0];
  try {
    const result = await service.uploadFile(file);
    console.log('File uploaded:', result.filename);
    localStorage.setItem('filepath', result.filepath);
  } catch (error) {
    console.error('Upload failed:', error);
  }
});

// Calculate safety stock
document.getElementById('calculateBtn').addEventListener('click', async () => {
  const filepath = localStorage.getItem('filepath');
  const skuId = document.getElementById('skuInput').value;
  
  try {
    const result = await service.calculateSafetyStock(filepath, skuId);
    document.getElementById('results').innerHTML = 
      `<p>Safety Stock: ${result.safety_stock}</p>`;
  } catch (error) {
    console.error('Calculation failed:', error);
  }
});
```

---

## React Integration

### Custom Hook
```javascript
// useInventoryAPI.js
import { useState } from 'react';

const API_BASE = 'http://localhost:5000';

export function useInventoryAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const uploadFile = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        throw new Error('Upload failed');
      }

      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const calculateSafetyStock = async (filepath, skuId, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/calculate-safety-stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filepath,
          sku_id: skuId,
          service_level: params.serviceLevel || 0.975,
          lead_time_days: params.leadTimeDays || 7
        })
      });

      if (!res.ok) {
        throw new Error('Calculation failed');
      }

      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const simulateInventory = async (filepath, skuId, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/simulate-inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filepath,
          sku_id: skuId,
          initial_inventory: params.initialInventory || 100,
          reorder_point: params.reorderPoint || 50,
          service_level: params.serviceLevel || 0.975,
          simulation_days: params.simulationDays || 90
        })
      });

      if (!res.ok) {
        throw new Error('Simulation failed');
      }

      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const batchCalculate = async (filepath, skuIds, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/batch-calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filepath,
          sku_ids: skuIds,
          service_level: params.serviceLevel || 0.975,
          lead_time_days: params.leadTimeDays || 7
        })
      });

      if (!res.ok) {
        throw new Error('Batch calculation failed');
      }

      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    uploadFile,
    calculateSafetyStock,
    simulateInventory,
    batchCalculate
  };
}
```

### Component Example
```javascript
// InventoryAnalyzer.jsx
import React, { useState } from 'react';
import { useInventoryAPI } from './useInventoryAPI';

function InventoryAnalyzer() {
  const [filepath, setFilepath] = useState(null);
  const [skuId, setSkuId] = useState('');
  const [results, setResults] = useState(null);
  const { loading, error, uploadFile, calculateSafetyStock } = 
    useInventoryAPI();

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const data = await uploadFile(file);
      setFilepath(data.filepath);
      alert('File uploaded successfully!');
    } catch (err) {
      alert('Upload failed: ' + err.message);
    }
  };

  const handleCalculate = async () => {
    if (!filepath || !skuId) {
      alert('Please upload file and enter SKU ID');
      return;
    }

    try {
      const data = await calculateSafetyStock(filepath, skuId);
      setResults(data);
    } catch (err) {
      alert('Calculation failed: ' + err.message);
    }
  };

  return (
    <div className="container">
      <h1>Inventory Analyzer</h1>

      <div className="upload-section">
        <input
          type="file"
          onChange={handleFileUpload}
          accept=".csv,.xlsx,.xls"
          disabled={loading}
        />
        {filepath && <p className="success">✓ File loaded: {filepath}</p>}
      </div>

      <div className="input-section">
        <input
          type="text"
          placeholder="Enter SKU ID"
          value={skuId}
          onChange={(e) => setSkuId(e.target.value)}
        />
        <button onClick={handleCalculate} disabled={loading}>
          {loading ? 'Calculating...' : 'Calculate Safety Stock'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {results && (
        <div className="results">
          <h3>Results for {results.sku_id}</h3>
          <p>
            <strong>Safety Stock:</strong> {results.safety_stock.toFixed(2)}
          </p>
          <p>
            <strong>Demand Mean:</strong> {results.demand_mean.toFixed(2)}
          </p>
          <p>
            <strong>Demand Std Dev:</strong> {results.demand_std.toFixed(2)}
          </p>
          <p>
            <strong>Service Level:</strong>{' '}
            {(results.service_level * 100).toFixed(1)}%
          </p>
        </div>
      )}
    </div>
  );
}

export default InventoryAnalyzer;
```

---

## Vue.js Integration

### Composable
```javascript
// useInventoryAPI.js (Vue 3 Composition API)
import { ref } from 'vue';

const API_BASE = 'http://localhost:5000';

export function useInventoryAPI() {
  const loading = ref(false);
  const error = ref(null);

  const uploadFile = async (file) => {
    loading.value = true;
    error.value = null;
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      return await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const calculateSafetyStock = async (filepath, skuId, params = {}) => {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(
        `${API_BASE}/api/calculate-safety-stock`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filepath,
            sku_id: skuId,
            service_level: params.serviceLevel || 0.975,
            lead_time_days: params.leadTimeDays || 7
          })
        }
      );

      if (!response.ok) {
        throw new Error('Calculation failed');
      }

      return await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const batchCalculate = async (filepath, skuIds, params = {}) => {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(`${API_BASE}/api/batch-calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filepath,
          sku_ids: skuIds,
          service_level: params.serviceLevel || 0.975,
          lead_time_days: params.leadTimeDays || 7
        })
      });

      if (!response.ok) {
        throw new Error('Batch calculation failed');
      }

      return await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    uploadFile,
    calculateSafetyStock,
    batchCalculate
  };
}
```

### Component Example
```vue
<!-- InventoryAnalyzer.vue -->
<template>
  <div class="container">
    <h1>Inventory Analyzer</h1>

    <div class="upload-section">
      <input
        type="file"
        @change="handleFileUpload"
        accept=".csv,.xlsx,.xls"
        :disabled="loading"
      />
      <p v-if="filepath" class="success">✓ File loaded: {{ filepath }}</p>
    </div>

    <div class="input-section">
      <input
        v-model="skuId"
        type="text"
        placeholder="Enter SKU ID"
      />
      <button @click="handleCalculate" :disabled="loading">
        {{ loading ? 'Calculating...' : 'Calculate Safety Stock' }}
      </button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="results" class="results">
      <h3>Results for {{ results.sku_id }}</h3>
      <p>
        <strong>Safety Stock:</strong> {{ results.safety_stock.toFixed(2) }}
      </p>
      <p>
        <strong>Demand Mean:</strong> {{ results.demand_mean.toFixed(2) }}
      </p>
      <p>
        <strong>Service Level:</strong>
        {{ (results.service_level * 100).toFixed(1) }}%
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useInventoryAPI } from './useInventoryAPI';

const filepath = ref(null);
const skuId = ref('');
const results = ref(null);
const { loading, error, uploadFile, calculateSafetyStock } = 
  useInventoryAPI();

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const data = await uploadFile(file);
    filepath.value = data.filepath;
    alert('File uploaded successfully!');
  } catch (err) {
    alert('Upload failed: ' + err.message);
  }
};

const handleCalculate = async () => {
  if (!filepath.value || !skuId.value) {
    alert('Please upload file and enter SKU ID');
    return;
  }

  try {
    const data = await calculateSafetyStock(
      filepath.value,
      skuId.value
    );
    results.value = data;
  } catch (err) {
    alert('Calculation failed: ' + err.message);
  }
};
</script>

<style scoped>
.container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.upload-section,
.input-section {
  margin: 20px 0;
}

input {
  padding: 10px;
  margin-right: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 10px 20px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.success {
  color: #4caf50;
}

.error {
  color: #f44336;
}

.results {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}
</style>
```

---

## Angular Integration

### Service
```typescript
// inventory.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

interface UploadResponse {
  success: boolean;
  filepath: string;
  filename: string;
  validation: any;
}

interface SafetyStockResponse {
  success: boolean;
  safety_stock: number;
  sku_id: string;
  demand_mean: number;
  demand_std: number;
}

@Injectable({
  providedIn: 'root'
})
export class InventoryService {
  private apiUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) {}

  uploadFile(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<UploadResponse>(
      `${this.apiUrl}/upload`,
      formData
    ).pipe(
      catchError(this.handleError)
    );
  }

  validateData(filepath: string): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/validate`,
      { filepath }
    ).pipe(
      catchError(this.handleError)
    );
  }

  calculateSafetyStock(
    filepath: string,
    skuId: string,
    params?: {
      serviceLevel?: number;
      leadTimeDays?: number;
      leadTimeStd?: number;
    }
  ): Observable<SafetyStockResponse> {
    const body = {
      filepath,
      sku_id: skuId,
      service_level: params?.serviceLevel || 0.975,
      lead_time_days: params?.leadTimeDays || 7,
      lead_time_std: params?.leadTimeStd || 1.5
    };

    return this.http.post<SafetyStockResponse>(
      `${this.apiUrl}/calculate-safety-stock`,
      body
    ).pipe(
      catchError(this.handleError)
    );
  }

  simulateInventory(
    filepath: string,
    skuId: string,
    params?: {
      initialInventory?: number;
      reorderPoint?: number;
      serviceLevel?: number;
      leadTimeDays?: number;
      coverageDays?: number;
      casePack?: number;
      simulationDays?: number;
    }
  ): Observable<any> {
    const body = {
      filepath,
      sku_id: skuId,
      initial_inventory: params?.initialInventory || 100,
      reorder_point: params?.reorderPoint || 50,
      service_level: params?.serviceLevel || 0.975,
      lead_time_days: params?.leadTimeDays || 7,
      coverage_days: params?.coverageDays || 30,
      case_pack: params?.casePack || 10,
      simulation_days: params?.simulationDays || 90
    };

    return this.http.post(
      `${this.apiUrl}/simulate-inventory`,
      body
    ).pipe(
      catchError(this.handleError)
    );
  }

  batchCalculate(
    filepath: string,
    skuIds: string[],
    params?: {
      serviceLevel?: number;
      leadTimeDays?: number;
    }
  ): Observable<any> {
    const body = {
      filepath,
      sku_ids: skuIds,
      service_level: params?.serviceLevel || 0.975,
      lead_time_days: params?.leadTimeDays || 7
    };

    return this.http.post(
      `${this.apiUrl}/batch-calculate`,
      body
    ).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred';
    
    if (error.error instanceof ErrorEvent) {
      errorMessage = `Network error: ${error.error.message}`;
    } else {
      errorMessage = error.error?.error || 
        `Server error: ${error.status} ${error.statusText}`;
    }
    
    return throwError(() => new Error(errorMessage));
  }
}
```

### Component Example
```typescript
// inventory-analyzer.component.ts
import { Component } from '@angular/core';
import { InventoryService } from './inventory.service';

@Component({
  selector: 'app-inventory-analyzer',
  templateUrl: './inventory-analyzer.component.html',
  styleUrls: ['./inventory-analyzer.component.css']
})
export class InventoryAnalyzerComponent {
  filepath: string | null = null;
  skuId: string = '';
  results: any = null;
  loading: boolean = false;
  error: string | null = null;

  constructor(private inventoryService: InventoryService) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) return;

    this.loading = true;
    this.error = null;

    this.inventoryService.uploadFile(file).subscribe({
      next: (response) => {
        this.filepath = response.filepath;
        this.loading = false;
        alert('File uploaded successfully!');
      },
      error: (error) => {
        this.error = error.message;
        this.loading = false;
      }
    });
  }

  calculateSafetyStock(): void {
    if (!this.filepath || !this.skuId) {
      alert('Please upload file and enter SKU ID');
      return;
    }

    this.loading = true;
    this.error = null;

    this.inventoryService.calculateSafetyStock(
      this.filepath,
      this.skuId
    ).subscribe({
      next: (response) => {
        this.results = response;
        this.loading = false;
      },
      error: (error) => {
        this.error = error.message;
        this.loading = false;
      }
    });
  }
}
```

```html
<!-- inventory-analyzer.component.html -->
<div class="container">
  <h1>Inventory Analyzer</h1>

  <div class="upload-section">
    <input
      type="file"
      #fileInput
      (change)="onFileSelected($event)"
      accept=".csv,.xlsx,.xls"
      [disabled]="loading"
    />
    <p *ngIf="filepath" class="success">✓ File loaded: {{ filepath }}</p>
  </div>

  <div class="input-section">
    <input
      [(ngModel)]="skuId"
      type="text"
      placeholder="Enter SKU ID"
    />
    <button
      (click)="calculateSafetyStock()"
      [disabled]="loading"
    >
      {{ loading ? 'Calculating...' : 'Calculate Safety Stock' }}
    </button>
  </div>

  <div *ngIf="error" class="error">{{ error }}</div>

  <div *ngIf="results" class="results">
    <h3>Results for {{ results.sku_id }}</h3>
    <p>
      <strong>Safety Stock:</strong>
      {{ results.safety_stock | number: '1.2-2' }}
    </p>
    <p>
      <strong>Demand Mean:</strong>
      {{ results.demand_mean | number: '1.2-2' }}
    </p>
    <p>
      <strong>Service Level:</strong>
      {{ results.service_level * 100 | number: '1.1-1' }}%
    </p>
  </div>
</div>
```

---

## Common Setup Steps

### 1. CORS Configuration
If using a different domain, ensure CORS is enabled on the server (already done in server.py).

### 2. Environment Variables
Create `.env` file:
```
REACT_APP_API_BASE_URL=http://localhost:5000
VUE_APP_API_BASE_URL=http://localhost:5000
```

### 3. Proxy Configuration (Development)
In `package.json`:
```json
{
  "proxy": "http://localhost:5000"
}
```

### 4. Install HTTP Client Library
```bash
npm install axios
# or
npm install @angular/common/http
```

---

## Testing with Mock Data

```javascript
// Mock service for development
const mockResults = {
  safety_stock: 156.78,
  sku_id: 'SKU12345',
  demand_mean: 45.67,
  demand_std: 12.34,
  service_level: 0.975
};

// Use in development
if (process.env.NODE_ENV === 'development' && !useRealAPI) {
  setTimeout(() => resolve(mockResults), 1000);
}
```

---

## Error Handling Best Practices

```javascript
// Common error handling pattern
async function apiCall() {
  try {
    // API call here
  } catch (error) {
    if (error.status === 404) {
      // Handle not found
    } else if (error.status === 400) {
      // Handle bad request
    } else if (error.status === 500) {
      // Handle server error
    } else {
      // Handle network error
    }
  }
}
```

---

*Last Updated: February 8, 2026*
