import { useRuns } from "~/hooks/use-runs";
import { Link } from "react-router";
import { format } from "date-fns";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "~/components/ui/table";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";

export default function RunsPage() {
    const { data: runs, isLoading, error, refetch } = useRuns();

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

    return (
        <div className="container mx-auto py-10 space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold tracking-tight">Experiment Runs</h1>
                <Button onClick={() => refetch()} variant="outline">
                    Refresh
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Recent Runs</CardTitle>
                </CardHeader>
                <CardContent>
                    {error && (
                        <div className="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50 dark:bg-gray-800 dark:text-red-400">
                            Failed to load runs: {error.message}
                        </div>
                    )}

                    {isLoading ? (
                        <div className="text-center py-10">Loading runs...</div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Run ID</TableHead>
                                    <TableHead>Dataset</TableHead>
                                    <TableHead>Phenomenon</TableHead>
                                    <TableHead>Model</TableHead>
                                    <TableHead>Stats</TableHead>
                                    <TableHead>Created At</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {(!runs || runs.length === 0) ? (
                                    <TableRow>
                                        <TableCell colSpan={8} className="text-center h-24">
                                            No runs found. Start a new experiment to see results here.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    runs.map((run) => (
                                        <TableRow key={run.run_id}>
                                            <TableCell>
                                                <Badge className={`${getStatusColor(run.status)} text-white border-0`}>
                                                    {run.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">
                                                {run.run_id.substring(0, 8)}...
                                            </TableCell>
                                            <TableCell>{run.dataset}</TableCell>
                                            <TableCell>{run.phenomenon}</TableCell>
                                            <TableCell>{run.model_name}</TableCell>
                                            <TableCell>
                                                {run.stats.completed} / {run.stats.total_examples}
                                                {run.stats.failed > 0 && (
                                                    <span className="text-red-500 ml-1">
                                                        ({run.stats.failed} failed)
                                                    </span>
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                {format(new Date(run.created_at), "MMM d, HH:mm")}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button asChild size="sm" variant="ghost">
                                                    <Link to={`/runs/${run.run_id}`}>View</Link>
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
