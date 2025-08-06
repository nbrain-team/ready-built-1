import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ready-built-1.onrender.com';

const salonApi = axios.create({
  baseURL: `${API_BASE_URL}/api/salon`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
salonApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class SalonApi {
  private axiosInstance;

  constructor() {
    this.axiosInstance = salonApi;
  }

  // Dashboard endpoints
  async getDashboardOverview() {
    const response = await this.axiosInstance.get('/dashboard/overview');
    return response.data;
  }

  async getPerformanceTrends(locationId?: number, months: number = 6) {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId.toString());
    params.append('months', months.toString());
    
    const response = await this.axiosInstance.get(`/dashboard/performance-trends?${params}`);
    return response.data;
  }

  async getTopPerformers(metric: string = 'sales', limit: number = 10) {
    const response = await this.axiosInstance.get('/dashboard/top-performers', {
      params: { metric, limit }
    });
    return response.data;
  }

  async getServiceBreakdown(locationId?: number) {
    const params = locationId ? { location_id: locationId } : {};
    const response = await this.axiosInstance.get('/analytics/service-breakdown', { params });
    return response.data;
  }

  async getClientInsights(locationId?: number) {
    const params = locationId ? { location_id: locationId } : {};
    const response = await this.axiosInstance.get('/analytics/client-insights', { params });
    return response.data;
  }

  async searchTransactions(params: {
    search?: string;
    location_id?: number;
    staff_id?: number;
    sale_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await this.axiosInstance.get('/transactions/search', { params });
    return response.data;
  }

  async getDailySummary(date?: string) {
    const params = date ? { target_date: date } : {};
    const response = await this.axiosInstance.get('/analytics/daily-summary', { params });
    return response.data;
  }

  // Analytics endpoints
  async getCapacityUtilization(locationId?: number) {
    const params = locationId ? { location_id: locationId } : {};
    const response = await this.axiosInstance.get('/analytics/capacity', { params });
    return response.data;
  }

  async getPrebookingImpact() {
    const response = await this.axiosInstance.get('/analytics/prebooking');
    return response.data;
  }

  async getOptimalScheduling(locationId: number) {
    const response = await this.axiosInstance.get(`/analytics/scheduling/${locationId}`);
    return response.data;
  }

  // Prediction endpoints
  async predictStaffSuccess(staffId: number, weeks: number = 6) {
    const response = await this.axiosInstance.post(`/predict/staff/${staffId}`, {
      weeks
    });
    return response.data;
  }

  // Data management endpoints
  async uploadData(file: File, type: 'staff' | 'performance') {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await this.axiosInstance.post(`/upload/${type}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Location and staff endpoints
  async getLocations() {
    const response = await this.axiosInstance.get('/locations');
    return response.data;
  }

  async getStaff(locationId?: number, status?: string) {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId.toString());
    if (status) params.append('status', status);
    
    const response = await this.axiosInstance.get(`/staff?${params}`);
    return response.data;
  }

  // AI Chat endpoint
  async processAnalyticsQuery(query: string) {
    const response = await this.axiosInstance.post('/analytics/query', {
      query
    });
    return response.data;
  }
}

export const salonApiInstance = new SalonApi(); 