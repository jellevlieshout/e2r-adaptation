import { Link, useParams, useNavigate } from "react-router";
import { useAdaptation, useDeleteAdaptation } from "~/hooks/use-adaptations";
import { AppLayout } from "~/components/layout/app-layout";
import { ProtectedRoute } from "~/components/layout/protected-route";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "~/components/ui/alert-dialog";
import { Skeleton } from "~/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "~/components/ui/tooltip";
import type { Route } from "./+types/history.$id";
import type { FigurativeExpression } from "~/api/types";

// =============================================================================
// Meta
// =============================================================================

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Adaptation Details | E2R Expression Adapter" },
    { name: "description", content: "View adaptation details" },
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
    return <p className="whitespace-pre-wrap leading-relaxed">{text}</p>;
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
// Loading Skeleton
// =============================================================================

function DetailSkeleton() {
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <Skeleton className="h-6 w-32" />
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-20" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-20" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

function DetailPageContent() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: adaptation, isLoading, isError } = useAdaptation(id);
  const deleteAdaptation = useDeleteAdaptation();

  const handleDelete = async () => {
    if (!id) return;
    await deleteAdaptation.mutateAsync(id);
    navigate("/history");
  };

  if (isLoading) {
    return (
      <AppLayout>
        <DetailSkeleton />
      </AppLayout>
    );
  }

  if (isError || !adaptation) {
    return (
      <AppLayout>
        <div className="max-w-md mx-auto text-center py-12">
          <p className="text-gray-500 mb-4">Adaptation not found.</p>
          <Button asChild>
            <Link to="/history">Back to History</Link>
          </Button>
        </div>
      </AppLayout>
    );
  }

  const date = new Date(adaptation.createdAt);
  const expressionTypes = [...new Set(adaptation.expressions.map((e) => e.type))];

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
          <Link to="/history" className="hover:text-gray-600">History</Link>
          <span>/</span>
          <span>Details</span>
        </div>

        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Adaptation Details
            </h1>
            <p className="text-sm text-gray-500">
              {date.toLocaleDateString("en-US", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete adaptation?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete this adaptation.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        <div className="space-y-4">
          {/* Summary */}
          <div className="flex items-center gap-3 text-sm">
            <span className="text-gray-500">
              {adaptation.expressions.length} expression{adaptation.expressions.length !== 1 ? "s" : ""} found
            </span>
            {expressionTypes.map((type) => (
              <Badge key={type} className={expressionTypeColors[type]}>
                {expressionTypeLabels[type]}
              </Badge>
            ))}
          </div>

          {/* Original Text */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Original</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-sm">
                <HighlightedText text={adaptation.originalText} expressions={adaptation.expressions} />
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
                <p className="whitespace-pre-wrap leading-relaxed">{adaptation.adaptedText}</p>
              </div>
            </CardContent>
          </Card>

          {/* Expression Details */}
          {adaptation.expressions.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Expression Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {adaptation.expressions.map((expr, index) => (
                  <div key={expr.id} className="p-3 border rounded-lg text-sm">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gray-100 text-xs">
                          {index + 1}
                        </span>
                        <span className="font-medium">"{expr.original}"</span>
                      </div>
                      <Badge className={expressionTypeColors[expr.type]}>
                        {expressionTypeLabels[expr.type]}
                      </Badge>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 mb-2 ml-7">{expr.explanation}</p>
                    <div className="ml-7">
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
            <Button asChild variant="outline">
              <Link to="/history">Back</Link>
            </Button>
            <Button asChild>
              <Link to="/adapt">New Adaptation</Link>
            </Button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default function HistoryDetail() {
  return (
    <ProtectedRoute>
      <DetailPageContent />
    </ProtectedRoute>
  );
}
