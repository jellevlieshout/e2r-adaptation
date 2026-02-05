import { useState } from "react";
import { Button } from "~/components/ui/button";
import { Textarea } from "~/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Label } from "~/components/ui/label";

export default function DetectPage() {
    const [text, setText] = useState("");
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDetect = async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/detect`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    task: "metaphor_detection",
                    text: text,
                    language: "en",
                }),
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();
            setResult(data);
        } catch (err: any) {
            setError(err.message || "An error occurred");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mx-auto py-10 space-y-8">
            <Card>
                <CardHeader>
                    <CardTitle>Canonical Metaphor Detection I/O (v1)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="input-text">Input Text</Label>
                        <Textarea
                            id="input-text"
                            placeholder="Enter text here..."
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            rows={5}
                        />
                    </div>
                    <Button onClick={handleDetect} disabled={loading || !text}>
                        {loading ? "Detecting..." : "Detect Metaphors"}
                    </Button>

                    {error && <div className="text-red-500 font-medium">{error}</div>}

                    {result && (
                        <div className="space-y-2">
                            <Label>Structured Output (JSON)</Label>
                            <div className="bg-slate-950 text-slate-50 p-4 rounded-md overflow-auto max-h-[500px]">
                                <pre className="text-sm font-mono">
                                    {JSON.stringify(result, null, 2)}
                                </pre>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
