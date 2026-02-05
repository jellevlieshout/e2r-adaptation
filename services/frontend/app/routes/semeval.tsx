import { useState, type ChangeEvent } from "react";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { useSemevalSamples } from "~/hooks/use-semeval";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "~/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "~/components/ui/select";
import { Label } from "~/components/ui/label";



export default function SemEvalPage() {
    const [task, setTask] = useState("all");
    const [split, setSplit] = useState("all");
    const [language, setLanguage] = useState("all");

    const { data: samples, isLoading, error } = useSemevalSamples(task, split, language);

    return (
        <div className="container mx-auto py-10 space-y-8">
            <Card>
                <CardHeader>
                    <CardTitle>SemEval 2022 Task 2: Idiomaticity Detection</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-wrap gap-4 mb-6 items-end">
                        <div className="space-y-2 w-40">
                            <Label>Task</Label>
                            <Select value={task} onValueChange={setTask}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select Task" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All</SelectItem>
                                    <SelectItem value="A">Task A</SelectItem>
                                    <SelectItem value="B">Task B</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2 w-40">
                            <Label>Split</Label>
                            <Select value={split} onValueChange={setSplit}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select Split" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All</SelectItem>
                                    <SelectItem value="train">Train</SelectItem>
                                    <SelectItem value="dev">Dev</SelectItem>
                                    <SelectItem value="test">Test</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2 w-40">
                            <Label>Language</Label>
                            <Select value={language} onValueChange={setLanguage}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select Language" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All</SelectItem>
                                    <SelectItem value="EN">English</SelectItem>
                                    <SelectItem value="PT">Portuguese</SelectItem>
                                    <SelectItem value="GL">Galician</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {isLoading && <div>Loading...</div>}
                    {error && <div className="text-red-500">Error: {(error as Error).message}</div>}

                    {samples && (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>MWE</TableHead>
                                    <TableHead>Lang</TableHead>
                                    <TableHead>Context / Sentence 1</TableHead>
                                    <TableHead>Sentence 2 / Context</TableHead>
                                    <TableHead>Labels</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {samples.map((sample) => (
                                    <TableRow key={sample.id}>
                                        <TableCell className="font-medium whitespace-nowrap">
                                            <div className="flex flex-col">
                                                <span>{sample.mwe1}</span>
                                                {sample.mwe2 && sample.mwe2 !== "None" && (
                                                    <span className="text-muted-foreground text-xs">{sample.mwe2}</span>
                                                )}
                                                <span className="text-xs text-muted-foreground mt-1">{sample.id}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell><Badge variant="outline">{sample.language}</Badge></TableCell>
                                        <TableCell className="max-w-[400px] text-sm whitespace-normal break-words">
                                            {sample.context_previous && <span className="text-muted-foreground mr-1">{sample.context_previous}</span>}
                                            <span className={sample.context_previous ? "font-semibold" : ""}>{sample.sentence1}</span>
                                            {sample.context_next && <span className="text-muted-foreground ml-1">{sample.context_next}</span>}
                                        </TableCell>
                                        <TableCell className="max-w-[400px] text-sm whitespace-normal break-words">
                                            {sample.sentence2 && sample.sentence2 !== "None" && sample.sentence2}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex flex-col gap-1">
                                                {sample.label && (
                                                    <Badge variant={sample.label === "0" ? "secondary" : "default"}>
                                                        Label: {sample.label}
                                                    </Badge>
                                                )}
                                                {sample.sim && (
                                                    <Badge variant="outline">Sim: {sample.sim}</Badge>
                                                )}
                                                {sample.setting && (
                                                    <span className="text-xs text-muted-foreground">{sample.setting}</span>
                                                )}
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
