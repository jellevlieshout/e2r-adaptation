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

export function useRunPredictions(runId: string | undefined, includeGold = false) {
    return useQuery<PredictionData[]>({
        queryKey: ["predictions", runId, includeGold],
        queryFn: () => fetchPredictions(runId!, includeGold),
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

export function useCompareRuns(runIds: string[]) {
    const runsQuery = useQuery<RunData[]>({
        queryKey: ["runs", "comparison", runIds],
        queryFn: async () => {
            const allRuns = await fetchRuns(100, 0);
            return allRuns.filter(r => runIds.includes(r.run_id));
        },
        enabled: runIds.length > 0,
    });

    const metricsQuery = useQuery<RunMetrics[]>({
        queryKey: ["metrics", "comparison", runIds],
        queryFn: async () => {
            return Promise.all(runIds.map(id => fetchRunMetrics(id)));
        },
        enabled: runIds.length > 0,
    });

    return {
        runs: runsQuery.data || [],
        metrics: metricsQuery.data || [],
        isLoading: runsQuery.isLoading || metricsQuery.isLoading,
        error: runsQuery.error || metricsQuery.error,
    };
}
