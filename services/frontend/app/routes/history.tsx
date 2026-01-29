import { useState } from "react";
import { Link } from "react-router";
import { useAdaptations, useDeleteAdaptation } from "~/hooks/use-adaptations";
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
import type { Route } from "./+types/history";
import type { AdaptationResponse, FigurativeExpression } from "~/api/types";

// =============================================================================
// Meta
// =============================================================================

export function meta({}: Route.MetaArgs) {
  return [
    { title: "History | E2R Expression Adapter" },
    { name: "description", content: "View your past text adaptations" },
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
// History Card Component
// =============================================================================

interface HistoryCardProps {
  adaptation: AdaptationResponse;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

function HistoryCard({ adaptation, onDelete, isDeleting }: HistoryCardProps) {
  const expressionTypes = [...new Set(adaptation.expressions.map((e) => e.type))];
  const date = new Date(adaptation.createdAt);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-sm font-medium truncate">
              {adaptation.originalText.slice(0, 60)}
              {adaptation.originalText.length > 60 ? "..." : ""}
            </CardTitle>
            <p className="text-xs text-gray-400 mt-1">
              {date.toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </p>
          </div>
          <Badge variant="secondary" className="text-xs">
            {adaptation.expressions.length} expr.
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {expressionTypes.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {expressionTypes.map((type) => (
              <Badge key={type} className={`text-xs ${expressionTypeColors[type]}`}>
                {expressionTypeLabels[type]}
              </Badge>
            ))}
          </div>
        )}

        <p className="text-sm text-gray-500 line-clamp-2 mb-3">
          {adaptation.adaptedText}
        </p>

        <div className="flex items-center gap-2">
          <Button asChild variant="outline" size="sm">
            <Link to={`/history/${adaptation.id}`}>View</Link>
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                disabled={isDeleting}
              >
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
                <AlertDialogAction
                  onClick={() => onDelete(adaptation.id)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function HistorySkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/4 mt-1" />
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex gap-1 mb-3">
          <Skeleton className="h-5 w-14" />
        </div>
        <Skeleton className="h-4 w-full mb-1" />
        <Skeleton className="h-4 w-2/3 mb-3" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-8 w-16" />
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Main Component
// =============================================================================

function HistoryPageContent() {
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, isError, error } = useAdaptations(page, pageSize);
  const deleteAdaptation = useDeleteAdaptation();

  const handleDelete = async (id: string) => {
    await deleteAdaptation.mutateAsync(id);
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              History
            </h1>
            <p className="text-gray-500 mt-1">Your past adaptations.</p>
          </div>
          <Button asChild>
            <Link to="/adapt">New</Link>
          </Button>
        </div>

        {isError && (
          <Card className="mb-4 border-red-200">
            <CardContent className="pt-4">
              <p className="text-red-600 text-sm">
                {error?.message || "Failed to load history."}
              </p>
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <HistorySkeleton key={i} />
            ))}
          </div>
        ) : data?.data.length === 0 ? (
          <Card className="text-center py-8">
            <CardContent>
              <p className="text-gray-500 mb-4">No adaptations yet.</p>
              <Button asChild>
                <Link to="/adapt">Adapt Text</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="space-y-3">
              {data?.data.map((adaptation) => (
                <HistoryCard
                  key={adaptation.id}
                  adaptation={adaptation}
                  onDelete={handleDelete}
                  isDeleting={deleteAdaptation.isPending}
                />
              ))}
            </div>

            {data && data.totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-500">
                  {page} / {data.totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(data.totalPages, p + 1))}
                  disabled={page === data.totalPages}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  );
}

export default function History() {
  return (
    <ProtectedRoute>
      <HistoryPageContent />
    </ProtectedRoute>
  );
}
