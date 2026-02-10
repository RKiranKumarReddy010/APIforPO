import axios from 'axios';

const API_BASE_URL = '/api';

export const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axios.post(`${API_BASE_URL}/upload`, formData);
};

export const validateData = async (filepath) => {
    return axios.post(`${API_BASE_URL}/validate`, { filepath });
};

export const processData = async (filepath) => {
    return axios.post(`${API_BASE_URL}/process-data`, { filepath });
};

export const calculateSafetyStock = async (params) => {
    return axios.post(`${API_BASE_URL}/calculate-safety-stock`, params);
};

export const simulateInventory = async (params) => {
    return axios.post(`${API_BASE_URL}/simulate-inventory`, params);
};

export const batchCalculate = async (params) => {
    return axios.post(`${API_BASE_URL}/batch-calculate`, params);
};

export const getCharts = async (filepath) => {
    return axios.post(`${API_BASE_URL}/get-charts`, { filepath });
};

export const getHealth = async () => {
    return axios.get(`${API_BASE_URL}/health`);
};

export const getConfig = async () => {
    return axios.get(`${API_BASE_URL}/config`);
};

