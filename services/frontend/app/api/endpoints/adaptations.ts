import type {
  AdaptationRequest,
  AdaptationResponse,
  PaginatedResponse,
} from "../types";
import { apiClient, isMockApiEnabled } from "../client";
import { mockAdaptations, delay, generateMockAdaptation } from "../mock-data";

// =============================================================================
// Adaptation Endpoints
// =============================================================================

/**
 * Create a new text adaptation
 */
export async function createAdaptation(
  request: AdaptationRequest
): Promise<AdaptationResponse> {
  // if (isMockApiEnabled()) {
  //   await delay(1500); // Simulate processing time
  //   return generateMockAdaptation(request.text);
  // }

  return apiClient<AdaptationResponse>("/adapt", {
    method: "POST",
    body: request,
  });
}

/**
 * Get all adaptations for the current user
 */
export async function getAdaptations(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedResponse<AdaptationResponse>> {
  if (isMockApiEnabled()) {
    await delay(500);

    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedData = mockAdaptations.slice(start, end);

    return {
      data: paginatedData,
      total: mockAdaptations.length,
      page,
      pageSize,
      totalPages: Math.ceil(mockAdaptations.length / pageSize),
    };
  }

  return apiClient<PaginatedResponse<AdaptationResponse>>(
    `/api/adaptations?page=${page}&pageSize=${pageSize}`
  );
}

/**
 * Get a single adaptation by ID
 */
export async function getAdaptation(id: string): Promise<AdaptationResponse> {
  if (isMockApiEnabled()) {
    await delay(400);

    const adaptation = mockAdaptations.find((a) => a.id === id);
    if (!adaptation) {
      throw new Error("Adaptation not found");
    }

    return adaptation;
  }

  return apiClient<AdaptationResponse>(`/api/adaptations/${id}`);
}

/**
 * Delete an adaptation
 */
export async function deleteAdaptation(id: string): Promise<void> {
  if (isMockApiEnabled()) {
    await delay(300);

    const index = mockAdaptations.findIndex((a) => a.id === id);
    if (index !== -1) {
      mockAdaptations.splice(index, 1);
    }

    return;
  }

  return apiClient<void>(`/api/adaptations/${id}`, {
    method: "DELETE",
  });
}
