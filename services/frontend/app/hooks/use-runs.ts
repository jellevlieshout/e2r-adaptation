import { useQuery } from "@tanstack/react-query";
import { fetchRuns, fetchRun, fetchPredictions, fetchRunMetrics, type RunData, type PredictionData, type RunMetrics } from "~/lib/api";

export function useRuns(limit: number = 50, offset: number = 0) {
    return useQuery<RunData[]>({
        queryKey: ["runs", limit, offset],
        queryFn: () => fetchRuns(limit, offset),
    });
}

export function useRun(runId: string | undefined) {
    return useQuery<RunData>({
        queryKey: ["run", runId],
        queryFn: () => fetchRun(runId!),
        enabled: !!runId,
    });
}

export function useRunPredictions(runId: string | undefined) {
    return useQuery<PredictionData[]>({
        queryKey: ["predictions", runId],
        queryFn: () => fetchPredictions(runId!),
        enabled: !!runId,
    });
}

export function useRunMetrics(runId: string | undefined) {
    return useQuery<RunMetrics>({
        queryKey: ["metrics", runId],
        queryFn: () => fetchRunMetrics(runId!),
        enabled: !!runId,
    });
}
// Forced HMR update
