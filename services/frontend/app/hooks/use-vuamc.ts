import { useQuery } from "@tanstack/react-query";
import { getMetaphors } from "~/api/endpoints/vuamc";
import type { MetaphorResponse } from "~/api/types";

// =============================================================================
// Query Keys
// =============================================================================

export const vuamcKeys = {
    all: ["vuamc"] as const,
    metaphors: (search: string) => [...vuamcKeys.all, "metaphors", { search }] as const,
};

// =============================================================================
// Hooks
// =============================================================================

export function useMetaphors(search: string = "") {
    return useQuery<MetaphorResponse[], Error>({
        queryKey: vuamcKeys.metaphors(search),
        queryFn: () => getMetaphors(search),
    });
}
