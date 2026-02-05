import { useState, type ChangeEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
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

interface Token {
    text: string;
    lemma: string;
    pos: string;
    is_metaphor: boolean;
    metaphor_type?: string;
    function?: string;
}

interface Sentence {
    id: string;
    text: string;
    tokens: Token[];
}

interface MetaphorResponse {
    token: Token;
    sentence: Sentence;
    document_id: string;
}

const fetchMetaphors = async (search: string) => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    params.append("limit", "50");

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/vuamc/metaphors?${params.toString()}`);
    if (!response.ok) {
        throw new Error("Failed to fetch metaphors");
    }
    return response.json() as Promise<MetaphorResponse[]>;
};

export default function MetaphorsPage() {
    const [search, setSearch] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");

    // Debounce search input
    const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
        setSearch(e.target.value);
        // Simple debounce logic could be added here, but for now we'll just update state
        // and let the user press Enter or rely on fast API.
        // For better UX, let's just trigger on Enter or blur, or use a debounce hook.
        // For this MVP, I'll add a 'Search' button or just update on blur/enter to avoid spamming.
    };

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ["metaphors", debouncedSearch],
        queryFn: () => fetchMetaphors(debouncedSearch),
    });

    return (
        <div className="container mx-auto py-10 space-y-8">
            <Card>
                <CardHeader>
                    <CardTitle>VU Amsterdam Metaphor Corpus</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex gap-4 mb-6">
                        <Input
                            placeholder="Search metaphors..."
                            value={search}
                            onChange={handleSearchChange}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    setDebouncedSearch(search);
                                }
                            }}
                        />
                        <Button onClick={() => setDebouncedSearch(search)}>Search</Button>
                    </div>

                    {isLoading && <div>Loading...</div>}
                    {error && <div className="text-red-500">Error: {(error as Error).message}</div>}

                    {data && (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Metaphor</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Function</TableHead>
                                    <TableHead>Context (Sentence)</TableHead>
                                    <TableHead>Doc ID</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {data.map((item, index) => (
                                    <TableRow key={`${item.document_id}-${item.sentence.id}-${index}`}>
                                        <TableCell className="font-medium">
                                            <span className="text-primary font-bold">{item.token.text}</span>
                                            {item.token.lemma !== item.token.text && (
                                                <span className="text-muted-foreground text-xs ml-1">({item.token.lemma})</span>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            {item.token.metaphor_type && (
                                                <Badge variant="outline">{item.token.metaphor_type}</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>{item.token.function}</TableCell>
                                        <TableCell className="max-w-[500px] whitespace-normal text-sm text-muted-foreground/90 leading-relaxed">
                                            {/* Highlight the metaphor in the sentence */}
                                            {item.sentence.tokens.map((t, i) => (
                                                <span
                                                    key={i}
                                                    className={
                                                        t.text === item.token.text && t.is_metaphor // Simple match, tough if multiple same words
                                                            ? "bg-yellow-100 dark:bg-yellow-900 font-bold px-1 rounded text-foreground"
                                                            : ""
                                                    }
                                                >
                                                    {t.text}{" "}
                                                </span>
                                            ))}
                                        </TableCell>
                                        <TableCell className="text-xs text-muted-foreground whitespace-nowrap align-top pt-4">{item.document_id}</TableCell>
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
