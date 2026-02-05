import { apiClient } from "../client";
import type { MetaphorResponse } from "../types";

export const getMetaphors = async (search: string, limit: number = 50) => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    params.append("limit", limit.toString());

    return apiClient<MetaphorResponse[]>(`/vuamc/metaphors?${params.toString()}`);
};
