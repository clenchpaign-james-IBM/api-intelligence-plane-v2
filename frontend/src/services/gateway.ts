import type { Gateway, PaginatedResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const gatewayService = {
  /**
   * List all gateways with optional pagination
   */
  async list(params?: {
    skip?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Gateway>> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const url = `${API_BASE_URL}/api/v1/gateways${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch gateways: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get a specific gateway by ID
   */
  async get(id: string): Promise<Gateway> {
    const response = await fetch(`${API_BASE_URL}/api/v1/gateways/${id}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Gateway not found: ${id}`);
      }
      throw new Error(`Failed to fetch gateway: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Create a new gateway
   */
  async create(gateway: Omit<Gateway, 'id' | 'created_at' | 'updated_at' | 'last_sync_at'>): Promise<Gateway> {
    const response = await fetch(`${API_BASE_URL}/api/v1/gateways`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(gateway),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to create gateway: ${error.detail || response.statusText}`);
    }

    return response.json();
  },

  /**
   * Update an existing gateway
   */
  async update(id: string, gateway: Partial<Omit<Gateway, 'id' | 'created_at' | 'updated_at'>>): Promise<Gateway> {
    const response = await fetch(`${API_BASE_URL}/api/v1/gateways/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(gateway),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Gateway not found: ${id}`);
      }
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to update gateway: ${error.detail || response.statusText}`);
    }

    return response.json();
  },

  /**
   * Delete a gateway
   */
  async delete(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/gateways/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Gateway not found: ${id}`);
      }
      throw new Error(`Failed to delete gateway: ${response.statusText}`);
    }
  },

  /**
   * Sync APIs from a gateway
   */
  async sync(id: string, forceRefresh: boolean = false): Promise<{ message: string; apis_discovered: number }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/gateways/${id}/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ force_refresh: forceRefresh }),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Gateway not found: ${id}`);
      }
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to sync gateway: ${error.detail || response.statusText}`);
    }

    return response.json();
  },

  /**
   * Test gateway connectivity
   */
  async testConnection(id: string): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/gateways/${id}/test`, {
      method: 'POST',
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Gateway not found: ${id}`);
      }
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to test gateway connection: ${error.detail || response.statusText}`);
    }

    return response.json();
  },
};

// Made with Bob
