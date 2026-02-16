import { Link, useSearchParams } from "react-router";
import { useCompareRuns } from "~/hooks/use-runs";
import { Skeleton } from "~/components/ui/skeleton";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "~/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "~/components/ui/table";
import {
    type ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "~/components/ui/chart";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer } from "recharts";
import type { RunData, RunMetrics } from "~/lib/api";

export default function RunComparePage() {
    const [searchParams] = useSearchParams();
    const runIds = searchParams.getAll("runId");

    const { runs, metrics, isLoading, error } = useCompareRuns(runIds);

    if (isLoading) {
        return (
            <div className="container mx-auto py-10 space-y-8">
                <Skeleton className="h-12 w-1/3" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Skeleton className="h-64" />
                    <Skeleton className="h-64" />
                </div>
                <Skeleton className="h-96 w-full" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto py-10">
                <div className="text-red-500">Error: {(error as Error).message}</div>
                <Button asChild className="mt-4" variant="outline">
                    <Link to="/runs">Back to Runs</Link>
                </Button>
            </div>
        );
    }

    if (runs.length === 0) {
        return (
            <div className="container mx-auto py-10 text-center">
                <h1 className="text-2xl font-bold">No runs selected for comparison</h1>
                <Button asChild className="mt-4" variant="outline">
                    <Link to="/runs">Back to Runs</Link>
                </Button>
            </div>
        );
    }

    // Prepare data for the metrics table
    const allMetricKeys = Array.from(
        new Set(metrics.flatMap((m: RunMetrics) => Object.keys(m.metrics)))
    ).sort();

    // Prepare data for the comparison charts
    const chartData = allMetricKeys.map((metricKey) => {
        const dataPoint: Record<string, any> = { metric: (metricKey as string).replace(/_/g, " ") };
        runs.forEach((run, index) => {
            const runMetrics = metrics.find((m: RunMetrics) => m.run_id === run.run_id);
            if (runMetrics) {
                dataPoint[`run_${index}`] = runMetrics.metrics[metricKey as string];
            }
        });
        return dataPoint;
    });

    const chartConfig: ChartConfig = {};
    const colors = ["#2563eb", "#9333ea", "#f59e0b", "#10b981", "#ef4444"];

    runs.forEach((run, index) => {
        chartConfig[`run_${index}`] = {
            label: `${run.model_name} (${run.run_id.substring(0, 4)})`,
            color: colors[index % colors.length],
        };
    });

    return (
        <div className="container mx-auto py-10 space-y-8">
            <div className="flex justify-between items-center">
                <div className="space-y-1">
                    <Link to="/runs" className="text-sm text-gray-500 hover:underline">
                        &larr; Back to Runs
                    </Link>
                    <h1 className="text-3xl font-bold tracking-tight">Run Comparison</h1>
                    <p className="text-gray-500">
                        Comparing {runs.length} runs across {runs[0].dataset}
                    </p>
                </div>
            </div>

            <div className="grid gap-8 lg:grid-cols-1">
                <Card>
                    <CardHeader>
                        <CardTitle>Metrics Comparison</CardTitle>
                        <CardDescription>Side-by-side comparison of performance metrics</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[400px] w-full mt-4">
                            <ChartContainer config={chartConfig}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData}>
                                        <CartesianGrid vertical={false} strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="metric"
                                            tickLine={false}
                                            tickMargin={10}
                                            axisLine={false}
                                        />
                                        <YAxis orientation="left" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                                        <ChartTooltip content={<ChartTooltipContent hideLabel />} />
                                        <ChartLegend content={<ChartLegendContent />} />
                                        {runs.map((_, index) => (
                                            <Bar
                                                key={`run_${index}`}
                                                dataKey={`run_${index}`}
                                                fill={`var(--color-run_${index})`}
                                                radius={4}
                                            />
                                        ))}
                                    </BarChart>
                                </ResponsiveContainer>
                            </ChartContainer>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Metrics Table</CardTitle>
                        <CardDescription>Detailed metric values for each run</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Metric</TableHead>
                                    {runs.map((run) => (
                                        <TableHead key={run.run_id}>
                                            <div className="flex flex-col">
                                                <span className="font-bold">{run.model_name}</span>
                                                <span className="text-[10px] font-mono text-muted-foreground">{run.run_id.substring(0, 8)}</span>
                                            </div>
                                        </TableHead>
                                    ))}
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {allMetricKeys.map((metricKey) => (
                                    <TableRow key={metricKey}>
                                        <TableCell className="font-medium capitalize">
                                            {metricKey.replace(/_/g, " ")}
                                        </TableCell>
                                        {runs.map((run) => {
                                            const val = metrics.find((m) => m.run_id === run.run_id)?.metrics[metricKey];
                                            return (
                                                <TableCell key={run.run_id}>
                                                    {val !== undefined ? (
                                                        <div className="flex flex-col">
                                                            <span className="font-bold">{(val * 100).toFixed(2)}%</span>
                                                            <span className="text-xs text-muted-foreground">{val.toFixed(4)}</span>
                                                        </div>
                                                    ) : "-"}
                                                </TableCell>
                                            );
                                        })}
                                    </TableRow>
                                ))}
                                <TableRow>
                                    <TableCell className="font-medium">Total Examples</TableCell>
                                    {runs.map((run) => (
                                        <TableCell key={run.run_id}>{run.stats.total_examples}</TableCell>
                                    ))}
                                </TableRow>
                                <TableRow>
                                    <TableCell className="font-medium">Completed</TableCell>
                                    {runs.map((run) => (
                                        <TableCell key={run.run_id}>{run.stats.completed}</TableCell>
                                    ))}
                                </TableRow>
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
