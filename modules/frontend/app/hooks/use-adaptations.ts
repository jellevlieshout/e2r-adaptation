import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { AdaptationRequest, AdaptationResponse, PaginatedResponse } from "~/api/types";
import {
  getAdaptations,
  getAdaptation,
  createAdaptation,
  deleteAdaptation,
} from "~/api/endpoints/adaptations";

// =============================================================================
// Query Keys
// =============================================================================

export const adaptationKeys = {
  all: ["adaptations"] as const,
  lists: () => [...adaptationKeys.all, "list"] as const,
  list: (page: number, pageSize: number) =>
    [...adaptationKeys.lists(), { page, pageSize }] as const,
  details: () => [...adaptationKeys.all, "detail"] as const,
  detail: (id: string) => [...adaptationKeys.details(), id] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to fetch paginated list of adaptations
 */
export function useAdaptations(page: number = 1, pageSize: number = 10) {
  return useQuery<PaginatedResponse<AdaptationResponse>, Error>({
    queryKey: adaptationKeys.list(page, pageSize),
    queryFn: () => getAdaptations(page, pageSize),
  });
}

/**
 * Hook to fetch a single adaptation by ID
 */
export function useAdaptation(id: string | undefined) {
  return useQuery<AdaptationResponse, Error>({
    queryKey: adaptationKeys.detail(id!),
    queryFn: () => getAdaptation(id!),
    enabled: !!id,
  });
}

/**
 * Hook to create a new adaptation
 */
export function useCreateAdaptation() {
  const queryClient = useQueryClient();

  return useMutation<AdaptationResponse, Error, AdaptationRequest>({
    mutationFn: createAdaptation,
    onSuccess: (data) => {
      // Invalidate the list queries to refetch
      queryClient.invalidateQueries({ queryKey: adaptationKeys.lists() });

      // Optionally, add the new adaptation to the cache
      queryClient.setQueryData(adaptationKeys.detail(data.id), data);
    },
  });
}

/**
 * Hook to delete an adaptation
 */
export function useDeleteAdaptation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteAdaptation,
    onSuccess: (_, deletedId) => {
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: adaptationKeys.lists() });

      // Remove from detail cache
      queryClient.removeQueries({ queryKey: adaptationKeys.detail(deletedId) });
    },
  });
}
