// API Service for Medical Triage-BOTS Frontend
// Handles all communication with the FastAPI backend

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import {
  TriageCase,
  TriageCaseResponse,
  SystemHealth,
  SystemMetrics,
  DatabaseCase,
  ChatMessage,
  ProcessingRecord,
  ApiResponse,
  PaginatedResponse,
  ApiError
} from '../types/medical';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp for tracking
        config.metadata = { startTime: Date.now() };

        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        const duration = Date.now() - response.config.metadata.startTime;
        console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} (${duration}ms)`);
        return response;
      },
      (error: AxiosError) => {
        const duration = error.config?.metadata ? Date.now() - error.config.metadata.startTime : 0;
        console.error(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url} (${duration}ms)`, error);

        // Transform error to our standard format
        throw this.handleApiError(error);
      }
    );
  }

  private handleApiError(error: AxiosError): ApiError {
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      timestamp: new Date().toISOString(),
    };

    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      apiError.message = data?.message || data?.detail || `HTTP ${status} Error`;
      apiError.code = data?.code || status.toString();
      apiError.details = data;
    } else if (error.request) {
      // Request was made but no response received
      apiError.message = 'Network error - unable to reach server';
      apiError.code = 'NETWORK_ERROR';
    } else {
      // Something else happened
      apiError.message = error.message || 'Request configuration error';
      apiError.code = 'REQUEST_ERROR';
    }

    return apiError;
  }

  // System endpoints
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.client.get<SystemHealth>('/health');
    return response.data;
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await this.client.get<SystemMetrics>('/metrics');
    return response.data;
  }

  // Triage endpoints
  async submitTriageCase(triageCase: TriageCase): Promise<TriageCaseResponse> {
    const response = await this.client.post<TriageCaseResponse>('/triage', triageCase);
    return response.data;
  }

  async submitTriageCaseMultipart(formData: FormData): Promise<TriageCaseResponse> {
    const response = await this.client.post<TriageCaseResponse>('/triage/multipart', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Database endpoints (custom endpoints for frontend)
  async getCases(params?: {
    page?: number;
    limit?: number;
    urgency_level?: string;
    department?: string;
    search?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<PaginatedResponse<DatabaseCase>> {
    const response = await this.client.get<PaginatedResponse<DatabaseCase>>('/database/cases', {
      params,
    });
    return response.data;
  }

  async getCase(caseId: string): Promise<DatabaseCase> {
    const response = await this.client.get<DatabaseCase>(`/database/cases/${caseId}`);
    return response.data;
  }

  async getCaseProcessingHistory(caseId: string): Promise<ProcessingRecord[]> {
    const response = await this.client.get<ProcessingRecord[]>(`/database/cases/${caseId}/processing`);
    return response.data;
  }

  // Chat/LLM endpoints
  async sendChatMessage(message: string, caseId?: string): Promise<ChatMessage> {
    const response = await this.client.post<ChatMessage>('/chat', {
      message,
      case_id: caseId,
      include_context: !!caseId,
    });
    return response.data;
  }

  async getChatHistory(caseId?: string): Promise<ChatMessage[]> {
    const params = caseId ? { case_id: caseId } : {};
    const response = await this.client.get<ChatMessage[]>('/chat/history', { params });
    return response.data;
  }

  // Analytics endpoints
  async getDashboardStats(): Promise<{
    total_cases: number;
    critical_cases: number;
    avg_processing_time: number;
    success_rate: number;
    cases_by_urgency: Record<string, number>;
    cases_by_hour: Array<{ hour: string; count: number }>;
    processing_times: Array<{ agent: string; avg_time: number }>;
  }> {
    const response = await this.client.get('/analytics/dashboard');
    return response.data;
  }

  async getProcessingMetrics(): Promise<{
    agents: Array<{
      name: string;
      total_requests: number;
      success_rate: number;
      avg_processing_time: number;
    }>;
    hourly_stats: Array<{
      hour: string;
      requests: number;
      successes: number;
      failures: number;
    }>;
  }> {
    const response = await this.client.get('/analytics/processing');
    return response.data;
  }

  // File upload utilities
  async uploadImage(file: File, caseId?: string): Promise<{ image_path: string; image_type: string }> {
    const formData = new FormData();
    formData.append('image', file);
    if (caseId) {
      formData.append('case_id', caseId);
    }

    const response = await this.client.post('/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Utility methods
  async testConnection(): Promise<boolean> {
    try {
      await this.client.get('/');
      return true;
    } catch (error) {
      return false;
    }
  }

  updateBaseURL(newUrl: string): void {
    this.client.defaults.baseURL = newUrl;
  }

  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken(): void {
    localStorage.removeItem('auth_token');
    delete this.client.defaults.headers.common['Authorization'];
  }
}

// Create singleton instance
const apiService = new ApiService();

// Export both the class and the instance
export { ApiService };
export default apiService;

// Utility hooks for React Query
export const queryKeys = {
  health: ['health'] as const,
  metrics: ['metrics'] as const,
  cases: (params?: any) => ['cases', params] as const,
  case: (id: string) => ['case', id] as const,
  caseProcessing: (id: string) => ['case', id, 'processing'] as const,
  chatHistory: (caseId?: string) => ['chat', 'history', caseId] as const,
  dashboardStats: ['analytics', 'dashboard'] as const,
  processingMetrics: ['analytics', 'processing'] as const,
};

// Error handling utilities
export const isApiError = (error: unknown): error is ApiError => {
  return typeof error === 'object' && error !== null && 'message' in error && 'timestamp' in error;
};

export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

// Request/response logging for development
if (process.env.NODE_ENV === 'development') {
  (window as any).apiService = apiService;
  console.log('🔧 Development mode: apiService is available on window.apiService');
}
