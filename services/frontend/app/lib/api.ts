
export interface RunStats {
    total_examples: number;
    completed: number;
    failed: number;
}

export type RunStatus = "running" | "completed" | "failed";

export interface RunData {
    run_id: string;
    dataset: string;
    phenomenon: string;
    task_type: string;
    model_name: string;
    temperature: number;
    top_p: number;
    prompt_version: string;
    created_at: string;
    status: RunStatus;
    stats: RunStats;
}

export interface Span {
    start: number;
    end: number;
}

export interface DetectionResult {
    is_figurative: boolean;
    token_labels?: number[];
    spans: Span[];
}

export interface PredictionData {
    type: "prediction";
    run_id: string;
    example_id: string;
    dataset: string;
    phenomenon: string;
    task_type: string;
    input_text: string;
    predicted_detection?: DetectionResult | null;
    predicted_replacement?: string | null;
    raw_model_output?: string | null;
    latency_ms?: number;
    token_usage?: Record<string, any>;
    confidence?: number;
    created_at: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:3030";

export async function fetchRuns(limit = 50, offset = 0): Promise<RunData[]> {
    const response = await fetch(`${API_BASE_URL}/runs?limit=${limit}&offset=${offset}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch runs: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchRun(runId: string): Promise<RunData> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch run ${runId}: ${response.statusText}`);
    }
    return response.json();
}

export async function fetchPredictions(runId: string): Promise<PredictionData[]> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/predictions`);
    if (!response.ok) {
        throw new Error(`Failed to fetch predictions for run ${runId}: ${response.statusText}`);
    }
    return response.json();
}

export interface RunMetrics {
    run_id: string;
    metrics: Record<string, number>;
    examples_evaluated: number;
}

export async function fetchRunMetrics(runId: string): Promise<RunMetrics> {
    const response = await fetch(`${API_BASE_URL}/runs/${runId}/metrics`);
    if (!response.ok) {
        throw new Error(`Failed to fetch metrics for run ${runId}: ${response.statusText}`);
    }
    return response.json();
}
