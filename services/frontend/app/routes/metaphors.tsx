import { useState, type ChangeEvent } from "react";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { useMetaphors } from "~/hooks/use-vuamc";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "~/components/ui/table";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "~/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";



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

    const { data, isLoading, error } = useMetaphors(debouncedSearch);

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
                                    <TableHead>
                                        <div className="flex items-center gap-1">
                                            Metaphor
                                            <TooltipProvider delayDuration={0}>
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                                                    </TooltipTrigger>
                                                    <TooltipContent className="max-w-[400px] p-4 text-sm">
                                                        <p><strong>Metaphors in VUAMC</strong></p>
                                                        <p className="mt-2">Words marked as metaphor-related (mrw) or metaphor flags (mFlag).</p>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        </div>
                                    </TableHead>
                                    <TableHead>
                                        <div className="flex items-center gap-1">
                                            Type
                                            <TooltipProvider delayDuration={0}>
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                                                    </TooltipTrigger>
                                                    <TooltipContent className="max-w-[400px] p-4 text-sm space-y-2">
                                                        <p><strong>Metaphor Types (MIPVU)</strong></p>
                                                        <ul className="list-disc pl-4 space-y-1">
                                                            <li><strong>met (Indirect):</strong> Indirect metaphor. E.g., "valuable" in "valuable work" (contrasts with money sense).</li>
                                                            <li><strong>lit (Direct):</strong> Direct metaphor or simile. E.g., "like a ferret".</li>
                                                            <li><strong>impl (Implicit):</strong> Implicit metaphor. E.g., "realizing it" referring to something abstract.</li>
                                                        </ul>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        </div>
                                    </TableHead>
                                    <TableHead>
                                        <div className="flex items-center gap-1">
                                            Function
                                            <TooltipProvider delayDuration={0}>
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                                                    </TooltipTrigger>
                                                    <TooltipContent className="max-w-[400px] p-4 text-sm space-y-2">
                                                        <p><strong>Annotation Function</strong></p>
                                                        <ul className="list-disc pl-4 space-y-1">
                                                            <li><strong>mrw:</strong> Metaphor Related Word. Candidate for cross-domain mapping.</li>
                                                            <li><strong>mFlag:</strong> Metaphor Flag. Signal for comparison (e.g., 'like', 'as if'). Types:
                                                                <ul className="list-circle pl-4 mt-1">
                                                                    <li><em>lex:</em> single word (e.g., 'like')</li>
                                                                    <li><em>morph:</em> part of word (e.g., 'wave-like')</li>
                                                                    <li><em>phrase:</em> phrase (e.g., 'in the role of')</li>
                                                                </ul>
                                                            </li>
                                                        </ul>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        </div>
                                    </TableHead>
                                    <TableHead>
                                        <div className="flex items-center gap-1">
                                            Status
                                            <TooltipProvider delayDuration={0}>
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                                                    </TooltipTrigger>
                                                    <TooltipContent className="max-w-[400px] p-4 text-sm space-y-2">
                                                        <p><strong>Status / Ambiguity Codes</strong></p>
                                                        <ul className="list-disc pl-4 space-y-1">
                                                            <li><strong>WIDLII:</strong> "When In Doubt, Leave It In". Ambiguous cases (e.g. "driven up the road" - phys/abstract).</li>
                                                            <li><strong>PP:</strong> Possible Personification. E.g. "A party can't decide" ('decide' is human trait).</li>
                                                            <li><strong>UNCERTAIN:</strong> Annotators were unsure (rare).</li>
                                                        </ul>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        </div>
                                    </TableHead>
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
                                        <TableCell>
                                            <div className="flex flex-col gap-1">
                                                <span>{item.token.function}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {item.token.status && (
                                                <Badge
                                                    variant="secondary"
                                                    className={
                                                        item.token.status === "WIDLII"
                                                            ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                                                            : item.token.status === "PP"
                                                                ? "bg-purple-100 text-purple-800 hover:bg-purple-200"
                                                                : ""
                                                    }
                                                >
                                                    {item.token.status}
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="max-w-[500px] whitespace-normal text-sm text-muted-foreground/90 leading-relaxed">
                                            {/* Highlight the metaphor in the sentence */}
                                            {item.sentence.tokens.map((t, i) => (
                                                <span
                                                    key={i}
                                                    className={
                                                        t.text === item.token.text && t.is_metaphor // Simple match
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
