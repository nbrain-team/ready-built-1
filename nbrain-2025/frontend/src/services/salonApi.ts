import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ready-built-1.onrender.com';

class SalonApi {
  private api: AxiosInstance;

  constructor() {
    // Use the full URL path for the salon API
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/salon`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for debugging
    this.api.interceptors.request.use(
      (config) => {
        console.log('API Request:', config.method?.toUpperCase(), config.url);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Response Error:', error.response?.status, error.response?.data);
        return Promise.reject(error);
      }
    );
  }

  async getDashboardOverview(startDate?: string, endDate?: string) {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await this.api.get('/dashboard/overview', { params });
    return response.data;
  }

  async getPerformanceTrends(startDate?: string, endDate?: string, locationId?: number) {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (locationId) params.location_id = locationId;
    const response = await this.api.get('/dashboard/performance-trends', { params });
    return response.data;
  }

  async getTopPerformers(metric: string = 'sales', limit: number = 10) {
    const response = await this.api.get('/dashboard/top-performers', {
      params: { metric, limit }
    });
    return response.data;
  }

  async getServiceBreakdown(locationId?: number) {
    const params = locationId ? { location_id: locationId } : {};
    const response = await this.api.get('/analytics/service-breakdown', { params });
    return response.data;
  }

  async getClientInsights(locationId?: number) {
    const params = locationId ? { location_id: locationId } : {};
    const response = await this.api.get('/analytics/client-insights', { params });
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
    const response = await this.api.get('/transactions/search', { params });
    return response.data;
  }

  async getDailySummary(date?: string) {
    const params = date ? { target_date: date } : {};
    const response = await this.api.get('/analytics/daily-summary', { params });
    return response.data;
  }

  // Analytics endpoints
  async getCapacityUtilization(locationId?: number) {
    const params = locationId ? { location_id: locationId } : {};
    const response = await this.api.get('/analytics/capacity', { params });
    return response.data;
  }

  async getPrebookingImpact() {
    const response = await this.api.get('/analytics/prebooking');
    return response.data;
  }

  async getOptimalScheduling(locationId: number) {
    const response = await this.api.get(`/analytics/scheduling/${locationId}`);
    return response.data;
  }

  // Prediction endpoints
  async predictStaffSuccess(staffId: number, weeks: number = 6) {
    const response = await this.api.post(`/predict/staff/${staffId}`, {
      weeks
    });
    return response.data;
  }

  // Data management endpoints
  async uploadData(file: File, type: 'staff' | 'performance') {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await this.api.post(`/upload/${type}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Location and staff endpoints
  async getLocations() {
    const response = await this.api.get('/locations');
    return response.data;
  }

  async getStaff(locationId?: number, status?: string) {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId.toString());
    if (status) params.append('status', status);
    
    const response = await this.api.get(`/staff?${params}`);
    return response.data;
  }

  // AI Chat endpoint
  async processAnalyticsQuery(query: string) {
    const response = await this.api.post('/analytics/query', {
      query
    });
    return response.data;
  }
}

export { SalonApi };
export const salonApi = new SalonApi(); 