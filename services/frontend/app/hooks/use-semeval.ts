import { useQuery } from "@tanstack/react-query";
import { getSemevalSamples } from "~/api/endpoints/semeval";
import type { SemEvalSample } from "~/api/types";

// =============================================================================
// Query Keys
// =============================================================================

export const semevalKeys = {
    all: ["semeval"] as const,
    samples: (task: string, split: string, language: string) =>
        [...semevalKeys.all, "samples", { task, split, language }] as const,
};

// =============================================================================
// Hooks
// =============================================================================

export function useSemevalSamples(
    task: string = "all",
    split: string = "all",
    language: string = "all"
) {
    return useQuery<SemEvalSample[], Error>({
        queryKey: semevalKeys.samples(task, split, language),
        queryFn: () => getSemevalSamples(task, split, language),
    });
}
