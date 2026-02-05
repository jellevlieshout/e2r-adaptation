import { apiClient } from "../client";
import type { SemEvalSample } from "../types";

export const getSemevalSamples = async (
    task: string,
    split: string,
    language: string,
    limit: number = 50
) => {
    const params = new URLSearchParams();
    if (task && task !== "all") params.append("task", task);
    if (split && split !== "all") params.append("split", split);
    if (language && language !== "all") params.append("language", language);
    params.append("limit", limit.toString());

    return apiClient<SemEvalSample[]>(`/semeval/samples?${params.toString()}`);
};
