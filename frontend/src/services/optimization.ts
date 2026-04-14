const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const optimizationService = {
  /**
   * Get optimization summary for dashboard (gateway-scoped)
   */
  async getSummary(params?: {
    gateway_id?: string;
  }): Promise<{
    total_recommendations: number;
    high_priority_recommendations: number;
    medium_priority_recommendations: number;
    low_priority_recommendations: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.gateway_id) queryParams.append('gateway_id', params.gateway_id);
    
    const url = `${API_BASE_URL}/api/v1/optimization/summary${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch optimization summary: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get recommendations with optional filters (gateway-scoped)
   */
  async getRecommendations(params?: {
    api_id?: string;
    gateway_id?: string;
    priority?: string;
    status?: string;
    recommendation_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params?.api_id) queryParams.append('api_id', params.api_id);
    if (params?.gateway_id) queryParams.append('gateway_id', params.gateway_id);
    if (params?.priority) queryParams.append('priority', params.priority);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.recommendation_type) queryParams.append('recommendation_type', params.recommendation_type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const url = `${API_BASE_URL}/api/v1/optimization/recommendations${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
    }

    return response.json();
  },
};

// Made with Bob