import { useQuery } from "@tanstack/react-query";
import { fetchRuns, fetchRun, fetchPredictions, type RunData, type PredictionData } from "~/lib/api";

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
