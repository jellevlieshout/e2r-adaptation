import * as React from "react";
import { useNavigate } from "react-router";
import { AppLayout } from "~/components/layout/app-layout";
import { ProtectedRoute } from "~/components/layout/protected-route";
import { Button } from "~/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Textarea } from "~/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "~/components/ui/select";
import { createManualExample } from "~/lib/api";
import { PlusCircle, Loader2 } from "lucide-react";
import type { Route } from "./+types/manual.new";

export function meta({ }: Route.MetaArgs) {
    return [{ title: "New Manual Example | E2R" }];
}

function NewManualExampleContent() {
    const navigate = useNavigate();
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);

        const formData = new FormData(e.currentTarget);
        const text = formData.get("text") as string;
        const phenomenon = formData.get("phenomenon") as string;
        const exampleId = formData.get("example_id") as string;

        try {
            await createManualExample({
                text,
                phenomenon,
                example_id: exampleId || undefined,
            });
            navigate("/"); // Redirect to dashboard for now
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create example");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AppLayout>
            <div className="max-w-2xl mx-auto space-y-6">
                <div className="flex flex-col gap-1">
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                        Create Manual Example
                    </h1>
                    <p className="text-muted-foreground">
                        Add a new example to the manual dataset for experimentation.
                    </p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Example Details</CardTitle>
                        <CardDescription>
                            Enter the text and select the linguistic phenomenon it contains.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="text">Input Text</Label>
                                <Textarea
                                    id="text"
                                    name="text"
                                    placeholder="Enter the text containing figurative language..."
                                    required
                                    className="min-h-[100px]"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="phenomenon">Phenomenon</Label>
                                    <Select name="phenomenon" defaultValue="metaphor" required>
                                        <SelectTrigger id="phenomenon">
                                            <SelectValue placeholder="Select type" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="metaphor">Metaphor</SelectItem>
                                            <SelectItem value="idiom">Idiom</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="example_id">Example ID (Optional)</Label>
                                    <Input
                                        id="example_id"
                                        name="example_id"
                                        placeholder="manual_001"
                                    />
                                </div>
                            </div>

                            {error && (
                                <p className="text-sm font-medium text-destructive">{error}</p>
                            )}

                            <div className="flex justify-end gap-3 pt-4">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => navigate(-1)}
                                    disabled={isSubmitting}
                                >
                                    Cancel
                                </Button>
                                <Button type="submit" disabled={isSubmitting} className="gap-2">
                                    {isSubmitting ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <PlusCircle className="w-4 h-4" />
                                    )}
                                    Create Example
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </AppLayout>
    );
}

export default function ManualNew() {
    return (
        <ProtectedRoute>
            <NewManualExampleContent />
        </ProtectedRoute>
    );
}
