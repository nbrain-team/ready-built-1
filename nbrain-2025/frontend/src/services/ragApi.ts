import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ChatMessage {
  query: string;
  session_id?: string;
  context?: any;
}

interface ChatResponse {
  success: boolean;
  response?: string;
  error?: string;
  session_id: string;
  drill_downs?: any[];
  data_context?: any;
}

interface DataSource {
  id: number;
  name: string;
  display_name: string;
  description: string;
  config: any;
  created_at: string;
  entry_count: number;
}

class RAGApi {
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async sendChatMessage(message: ChatMessage): Promise<ChatResponse> {
    const response = await axios.post(
      `${API_BASE_URL}/api/rag/chat`,
      message,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getDataSources(): Promise<DataSource[]> {
    const response = await axios.get(
      `${API_BASE_URL}/api/rag/data-sources`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getChatHistory(sessionId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/api/rag/chat/history/${sessionId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getChatSessions() {
    const response = await axios.get(
      `${API_BASE_URL}/api/rag/chat/sessions`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async createDataSource(data: {
    name: string;
    display_name: string;
    description?: string;
    config: any;
  }): Promise<DataSource> {
    const response = await axios.post(
      `${API_BASE_URL}/api/rag/data-sources`,
      data,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async uploadData(sourceId: number, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(
      `${API_BASE_URL}/api/rag/data-sources/${sourceId}/upload`,
      formData,
      {
        headers: {
          ...this.getAuthHeaders(),
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  }

  async getConfigurations(configType?: string) {
    const params = configType ? { config_type: configType } : {};
    const response = await axios.get(
      `${API_BASE_URL}/api/rag/configurations`,
      { 
        headers: this.getAuthHeaders(),
        params
      }
    );
    return response.data;
  }

  async createConfiguration(data: {
    config_type: string;
    config_data: any;
  }) {
    const response = await axios.post(
      `${API_BASE_URL}/api/rag/configurations`,
      data,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }
}

export const ragApi = new RAGApi(); 