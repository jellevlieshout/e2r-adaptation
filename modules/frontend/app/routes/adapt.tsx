import { useState } from "react";
import { useNavigate } from "react-router";
import { useCreateAdaptation } from "~/hooks/use-adaptations";
import { AppLayout } from "~/components/layout/app-layout";
import { ProtectedRoute } from "~/components/layout/protected-route";
import { Button } from "~/components/ui/button";
import { Textarea } from "~/components/ui/textarea";
import { Label } from "~/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Alert, AlertDescription } from "~/components/ui/alert";
import { Badge } from "~/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "~/components/ui/tooltip";
import type { Route } from "./+types/adapt";
import type { AdaptationResponse, FigurativeExpression } from "~/api/types";

// =============================================================================
// Meta
// =============================================================================

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Adapt Text | E2R Expression Adapter" },
    { name: "description", content: "Adapt figurative expressions for easier comprehension" },
  ];
}

// =============================================================================
// Expression Type Colors
// =============================================================================

const expressionTypeColors: Record<FigurativeExpression["type"], string> = {
  idiom: "bg-purple-100 text-purple-700",
  conceptual_metaphor: "bg-blue-100 text-blue-700",
};

const expressionTypeLabels: Record<FigurativeExpression["type"], string> = {
  idiom: "Idiom",
  conceptual_metaphor: "Conceptual Metaphor",
};

// =============================================================================
// Highlighted Text Component
// =============================================================================

interface HighlightedTextProps {
  text: string;
  expressions: FigurativeExpression[];
}

function HighlightedText({ text, expressions }: HighlightedTextProps) {
  if (expressions.length === 0) {
    return <p className="whitespace-pre-wrap">{text}</p>;
  }

  const sortedExpressions = [...expressions].sort((a, b) => a.startIndex - b.startIndex);
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  sortedExpressions.forEach((expr, i) => {
    if (expr.startIndex > lastIndex) {
      parts.push(<span key={`text-${i}`}>{text.slice(lastIndex, expr.startIndex)}</span>);
    }

    parts.push(
      <Tooltip key={`expr-${i}`}>
        <TooltipTrigger asChild>
          <mark className={`px-1 rounded ${expressionTypeColors[expr.type]} cursor-help`}>
            {expr.original}
          </mark>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border shadow-lg">
          <p className="font-medium text-xs mb-1">{expressionTypeLabels[expr.type]}</p>
          <p className="text-xs text-gray-600 dark:text-gray-400">{expr.explanation}</p>
        </TooltipContent>
      </Tooltip>
    );

    lastIndex = expr.endIndex;
  });

  if (lastIndex < text.length) {
    parts.push(<span key="text-end">{text.slice(lastIndex)}</span>);
  }

  return <p className="whitespace-pre-wrap leading-relaxed">{parts}</p>;
}

// =============================================================================
// Result Component
// =============================================================================

interface AdaptationResultProps {
  result: AdaptationResponse;
  onReset: () => void;
}

function AdaptationResult({ result, onReset }: AdaptationResultProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="text-sm text-gray-600">
        {result.expressions.length > 0 ? (
          <>Found {result.expressions.length} expression{result.expressions.length !== 1 ? "s" : ""}</>
        ) : (
          "No figurative expressions detected"
        )}
      </div>

      {/* Original Text */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Original</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-sm">
            <HighlightedText text={result.originalText} expressions={result.expressions} />
          </div>
        </CardContent>
      </Card>

      {/* Adapted Text */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Adapted</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800 text-sm">
            <p className="whitespace-pre-wrap leading-relaxed">{result.adaptedText}</p>
          </div>
        </CardContent>
      </Card>

      {/* Expression Details */}
      {result.expressions.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {result.expressions.map((expr) => (
              <div key={expr.id} className="p-3 border rounded-lg text-sm">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="font-medium">"{expr.original}"</span>
                  <Badge className={expressionTypeColors[expr.type]}>
                    {expressionTypeLabels[expr.type]}
                  </Badge>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-2">{expr.explanation}</p>
                <div>
                  <span className="text-gray-400">Simplified: </span>
                  <span className="text-green-600 dark:text-green-400">"{expr.simplifiedVersion}"</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={onReset} variant="outline">
          Adapt Another
        </Button>
        <Button onClick={() => navigate(`/history/${result.id}`)}>
          View Details
        </Button>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

function AdaptPageContent() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AdaptationResponse | null>(null);
  const createAdaptation = useCreateAdaptation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    try {
      const response = await createAdaptation.mutateAsync({ text: text.trim() });
      setResult(response);
    } catch (error) {
      console.error("Failed to create adaptation:", error);
    }
  };

  const handleReset = () => {
    setText("");
    setResult(null);
    createAdaptation.reset();
  };

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Adapt Text
          </h1>
          <p className="text-gray-500 mt-1">
            Enter text to identify and simplify figurative expressions.
          </p>
        </div>

        {result ? (
          <AdaptationResult result={result} onReset={handleReset} />
        ) : (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Enter Text</CardTitle>
              <CardDescription>
                Paste text that may contain idioms or conceptual metaphors.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {createAdaptation.isError && (
                  <Alert variant="destructive">
                    <AlertDescription>
                      {createAdaptation.error?.message || "Failed to process text."}
                    </AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="text">Text</Label>
                  <Textarea
                    id="text"
                    placeholder="e.g., I tried to break the ice, but time is money so I had to leave."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={6}
                    disabled={createAdaptation.isPending}
                    className="resize-y"
                  />
                  <p className="text-xs text-gray-400">{text.length} characters</p>
                </div>

                <Button
                  type="submit"
                  disabled={!text.trim() || createAdaptation.isPending}
                  className="w-full"
                >
                  {createAdaptation.isPending ? "Analyzing..." : "Adapt Text"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}

export default function Adapt() {
  return (
    <ProtectedRoute>
      <AdaptPageContent />
    </ProtectedRoute>
  );
}
