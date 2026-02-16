import { useQuery } from "@tanstack/react-query";
import { fetchDatasetStats } from "~/lib/api";

export function useDatasetStats() {
    return useQuery({
        queryKey: ["dataset-stats"],
        queryFn: fetchDatasetStats,
    });
}
