import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { format } from "date-fns";
import { useRun, useRunPredictions } from "~/hooks/use-runs";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import { TextAnnotator } from "~/components/text-annotator";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "~/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Skeleton } from "~/components/ui/skeleton";

export default function RunDetailsPage() {
    const { runId } = useParams();
    const { data: run, isLoading: isLoadingRun, error: runError, refetch: refetchRun } = useRun(runId);
    const { data: predictions, isLoading: isLoadingPreds, error: predsError, refetch: refetchPreds } = useRunPredictions(runId);

    const isLoading = isLoadingRun || isLoadingPreds;
    const error = runError || predsError;

    const handleRefresh = () => {
        refetchRun();
        refetchPreds();
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "completed":
                return "bg-green-500 hover:bg-green-600";
            case "failed":
                return "bg-red-500 hover:bg-red-600";
            case "running":
                return "bg-blue-500 hover:bg-blue-600";
            default:
                return "bg-gray-500 hover:bg-gray-600";
        }
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
                    <Link to="/runs">Back to Runs</Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-10 space-y-8">
            <div className="flex justify-between items-center">
                <div className="space-y-1">
                    <Link to="/runs" className="text-sm text-gray-500 hover:underline">
                        &larr; Back to Runs
                    </Link>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                        Run {run.run_id.substring(0, 8)}
                        <Badge className={getStatusColor(run.status)}>{run.status}</Badge>
                    </h1>
                    <p className="text-gray-500">
                        {run.dataset} • {run.phenomenon} • {run.model_name}
                    </p>
                </div>
                <Button onClick={handleRefresh} variant="outline">
                    Refresh
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Examples</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{run.stats.total_examples}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Completed</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                            {run.stats.completed}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Failed</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${run.stats.failed > 0 ? 'text-red-600' : ''}`}>
                            {run.stats.failed}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Created</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-sm font-medium">
                            {format(new Date(run.created_at), "PP HH:mm")}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="predictions" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="predictions">Predictions</TabsTrigger>
                    <TabsTrigger value="metrics">Metrics (Coming Soon)</TabsTrigger>
                    <TabsTrigger value="json">Raw JSON</TabsTrigger>
                </TabsList>

                <TabsContent value="predictions" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Example Inspection</CardTitle>
                            <CardDescription>
                                <span className="inline-block w-3 h-3 bg-red-200 mr-1 border border-red-300"></span> Gold
                                <span className="inline-block w-3 h-3 bg-blue-200 ml-3 mr-1 border border-blue-300"></span> Predicted
                                <span className="inline-block w-3 h-3 bg-purple-200 ml-3 mr-1 border border-purple-300"></span> Overlap
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                {(predictions || []).map((pred) => (
                                    <div
                                        key={pred.example_id}
                                        className="border rounded-md p-4 space-y-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                                    >
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-semibold text-sm text-gray-500">
                                                ID: {pred.example_id}
                                            </h3>
                                            {pred.latency_ms && (
                                                <span className="text-xs text-gray-400">
                                                    {pred.latency_ms}ms
                                                </span>
                                            )}
                                        </div>

                                        <div className="bg-white dark:bg-gray-950 p-3 rounded border">
                                            <TextAnnotator
                                                text={pred.input_text}
                                                // Note: We don't have gold spans in PredictionData yet!
                                                // We might need to fetch DatasetExample or store gold in prediction for easier visualization.
                                                // For now, let's assume we want to visualize just predictions, 
                                                // or we encounter a limitation in our data model plan.
                                                // PLAN says "Gold spans (red)" in Section 12.2.
                                                // But PredictionData schema doesn't have gold data. 
                                                // We should probably fetch it or maybe it's usually joined.
                                                // Ideally backend should return it.
                                                // For this iteration, I will visualize PREDICTED spans.
                                                predictedSpans={pred.predicted_detection?.spans || []}
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <span className="font-semibold">Detection: </span>
                                                {pred.predicted_detection?.is_figurative
                                                    ? "Figurative"
                                                    : "Literal"}
                                            </div>
                                            {pred.predicted_replacement && (
                                                <div>
                                                    <span className="font-semibold">Replacement: </span>
                                                    <span className="italic">
                                                        {pred.predicted_replacement}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="metrics">
                    <Card>
                        <CardContent className="pt-6">
                            <p>Metrics visualization will be implemented in Step 8.</p>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="json">
                    <Card>
                        <CardContent className="pt-6">
                            <pre className="bg-gray-900 text-gray-100 p-4 rounded overflow-auto max-h-[500px] text-xs">
                                {JSON.stringify(run, null, 2)}
                            </pre>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
