import { Link, useParams } from "react-router";
import { format } from "date-fns";
import type { PredictionData } from "~/lib/api";
import { useRun, useRunPredictions, useRunMetrics } from "~/hooks/use-runs";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import { TextAnnotator } from "~/components/text-annotator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Skeleton } from "~/components/ui/skeleton";

function StatusBadge({ status }: { status: string }) {
    const colors: Record<string, string> = {
        completed: "bg-green-500 hover:bg-green-600",
        failed: "bg-red-500 hover:bg-red-600",
        running: "bg-blue-500 hover:bg-blue-600",
    };
    return (
        <Badge className={`${colors[status] || "bg-gray-500"} text-white border-0`}>
            {status}
        </Badge>
    );
}

function MetricCard({ label, value, format: fmt }: { label: string; value: string | number; format?: "percent" }) {
    const display = fmt === "percent" && typeof value === "number"
        ? `${(value * 100).toFixed(1)}%`
        : String(value);
    const sub = fmt === "percent" && typeof value === "number"
        ? (value as number).toFixed(4)
        : undefined;

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium capitalize">{label}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{display}</div>
                {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
            </CardContent>
        </Card>
    );
}

function ConfigRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between py-2 border-b last:border-0">
            <span className="text-sm text-muted-foreground">{label}</span>
            <span className="text-sm font-medium font-mono">{value}</span>
        </div>
    );
}

function PredictionCard({ pred }: { pred: PredictionData }) {
    const goldLabel = pred.gold_detection?.is_figurative ? "Figurative" : "Literal";
    const predLabel = pred.predicted_detection?.is_figurative ? "Figurative" : "Literal";
    const match = goldLabel === predLabel;

    return (
        <div className="border rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-start">
                <span className="font-mono text-xs text-muted-foreground">
                    {pred.example_id}
                </span>
                {pred.latency_ms != null && (
                    <span className="text-xs text-muted-foreground">{pred.latency_ms}ms</span>
                )}
            </div>

            <div className="bg-white dark:bg-gray-950 p-3 rounded border">
                <TextAnnotator
                    text={pred.input_text}
                    goldSpans={pred.gold_detection?.spans || []}
                    predictedSpans={pred.predicted_detection?.spans || []}
                />
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span className="text-muted-foreground">Gold: </span>
                    <span className={`font-semibold ${pred.gold_detection?.is_figurative ? "text-red-600" : ""}`}>
                        {goldLabel}
                    </span>
                </div>
                <div>
                    <span className="text-muted-foreground">Predicted: </span>
                    <span className={`font-semibold ${match ? "text-green-600" : "text-orange-600"}`}>
                        {predLabel}
                    </span>
                </div>
            </div>

            {(pred.predicted_detection?.figurative_expressions?.length || pred.gold_detection?.figurative_expressions?.length) ? (
                <div className="grid grid-cols-2 gap-4 text-sm border-t pt-2">
                    {pred.gold_detection?.figurative_expressions && pred.gold_detection.figurative_expressions.length > 0 && (
                        <div>
                            <span className="text-muted-foreground block mb-1">Gold expressions:</span>
                            <div className="flex flex-wrap gap-1">
                                {pred.gold_detection.figurative_expressions.map((expr, i) => (
                                    <span key={i} className="inline-block px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full border border-red-200">
                                        {expr}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                    {pred.predicted_detection?.figurative_expressions && pred.predicted_detection.figurative_expressions.length > 0 && (
                        <div>
                            <span className="text-muted-foreground block mb-1">Predicted expressions:</span>
                            <div className="flex flex-wrap gap-1">
                                {pred.predicted_detection.figurative_expressions.map((expr, i) => (
                                    <span key={i} className="inline-block px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full border border-blue-200">
                                        {expr}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : null}

            {(pred.gold_replacement || pred.predicted_replacement) && (
                <div className="grid grid-cols-2 gap-4 text-sm border-t pt-2">
                    {pred.gold_replacement && (
                        <div>
                            <span className="text-muted-foreground">Gold replacement: </span>
                            <span className="italic">{pred.gold_replacement}</span>
                        </div>
                    )}
                    {pred.predicted_replacement && (
                        <div>
                            <span className="text-muted-foreground">Predicted replacement: </span>
                            <span className="italic">{pred.predicted_replacement}</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function RunDetailsPage() {
    const { runId } = useParams();
    const { data: run, isLoading: isLoadingRun, error: runError, refetch: refetchRun } = useRun(runId);
    const { data: predictions, isLoading: isLoadingPreds, error: predsError, refetch: refetchPreds } = useRunPredictions(runId, true);
    const { data: metricsData, isLoading: isLoadingMetrics, refetch: refetchMetrics } = useRunMetrics(runId);

    const isLoading = isLoadingRun;
    const error = runError || predsError;

    const handleRefresh = () => {
        refetchRun();
        refetchPreds();
        refetchMetrics();
    };

    if (isLoading) {
        return (
            <div className="container mx-auto py-10 space-y-8">
                <Skeleton className="h-12 w-1/3" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    if (error || !run) {
        return (
            <div className="container mx-auto py-10">
                <div className="text-red-500">Error: {error?.message || "Run not found"}</div>
                <Button asChild className="mt-4" variant="outline">
                    <Link to="/">Back to Runs</Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-10 space-y-8">
            <div className="flex justify-between items-center">
                <div className="space-y-1">
                    <Link to="/" className="text-sm text-muted-foreground hover:underline">
                        &larr; Back to Runs
                    </Link>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                        Run {run.run_id.substring(0, 8)}
                        <StatusBadge status={run.status} />
                    </h1>
                    <p className="text-muted-foreground">
                        {run.dataset} &middot; {run.phenomenon} &middot; {run.model_name}
                    </p>
                </div>
                <Button onClick={handleRefresh} variant="outline">
                    Refresh
                </Button>
            </div>

            <Tabs defaultValue="overview" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="predictions">
                        Predictions {predictions ? `(${predictions.length})` : ""}
                    </TabsTrigger>
                    <TabsTrigger value="prompt">Prompt</TabsTrigger>
                </TabsList>

                {/* ── Overview Tab ── */}
                <TabsContent value="overview" className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Run Configuration</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ConfigRow label="Model" value={run.model_name} />
                            <ConfigRow label="Dataset" value={run.dataset} />
                            <ConfigRow label="Phenomenon" value={run.phenomenon} />
                            <ConfigRow label="Task Type" value={run.task_type} />
                            <ConfigRow label="Temperature" value={String(run.temperature)} />
                            <ConfigRow label="Top P" value={String(run.top_p)} />
                            <ConfigRow label="Prompt Version" value={run.prompt_version} />
                            <ConfigRow label="Prompt Hash" value={run.prompt_hash || "—"} />
                            <ConfigRow label="Created" value={format(new Date(run.created_at), "PPpp")} />
                            <ConfigRow label="Status" value={run.status} />
                        </CardContent>
                    </Card>

                    <div className="grid gap-4 md:grid-cols-3">
                        <MetricCard label="Total Examples" value={run.stats.total_examples} />
                        <MetricCard label="Completed" value={run.stats.completed} />
                        <MetricCard label="Failed" value={run.stats.failed} />
                    </div>

                    {isLoadingMetrics ? (
                        <Skeleton className="h-32 w-full" />
                    ) : metricsData && Object.keys(metricsData.metrics).length > 0 ? (
                        <div>
                            <h3 className="text-lg font-semibold mb-3">
                                Evaluation Metrics
                                <span className="text-sm font-normal text-muted-foreground ml-2">
                                    ({metricsData.examples_evaluated} examples)
                                </span>
                            </h3>
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                {Object.entries(metricsData.metrics).map(([key, value]) => (
                                    <MetricCard key={key} label={key.replace(/_/g, " ")} value={value} format="percent" />
                                ))}
                            </div>
                        </div>
                    ) : (
                        <Card>
                            <CardContent className="py-8 text-center text-muted-foreground">
                                No metrics available. Run evaluation first.
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                {/* ── Predictions Tab ── */}
                <TabsContent value="predictions" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardDescription>
                                <span className="inline-block w-3 h-3 bg-red-200 mr-1 border border-red-300 rounded-sm"></span> Gold
                                <span className="inline-block w-3 h-3 bg-blue-200 ml-3 mr-1 border border-blue-300 rounded-sm"></span> Predicted
                                <span className="inline-block w-3 h-3 bg-purple-200 ml-3 mr-1 border border-purple-300 rounded-sm"></span> Overlap
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoadingPreds ? (
                                <div className="space-y-4">
                                    <Skeleton className="h-32 w-full" />
                                    <Skeleton className="h-32 w-full" />
                                </div>
                            ) : !predictions || predictions.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    No predictions found.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {predictions.map((pred) => (
                                        <PredictionCard key={pred.example_id} pred={pred} />
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* ── Prompt Tab ── */}
                <TabsContent value="prompt">
                    <Card>
                        <CardHeader>
                            <CardTitle>Prompt Text</CardTitle>
                            <CardDescription>
                                Version: {run.prompt_version} &middot; Hash: {run.prompt_hash || "—"}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {run.prompt_text ? (
                                <pre className="bg-gray-950 text-gray-100 p-4 rounded-lg overflow-auto max-h-[600px] text-sm leading-relaxed whitespace-pre-wrap">
                                    {run.prompt_text}
                                </pre>
                            ) : (
                                <div className="text-center py-8 text-muted-foreground">
                                    Prompt text not stored for this run.
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
