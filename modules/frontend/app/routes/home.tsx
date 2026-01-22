import { Link } from "react-router";
import { useAdaptations } from "~/hooks/use-adaptations";
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
import { Badge } from "~/components/ui/badge";
import { Skeleton } from "~/components/ui/skeleton";
import type { Route } from "./+types/home";
import type { FigurativeExpression } from "~/api/types";

// =============================================================================
// Meta
// =============================================================================

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Dashboard | E2R Expression Adapter" },
    {
      name: "description",
      content: "Adapt figurative expressions for easier comprehension",
    },
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
// Recent Activity Skeleton
// =============================================================================

function RecentActivitySkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
          <Skeleton className="h-8 w-8 rounded-full" />
          <div className="flex-1 space-y-1">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

function DashboardContent() {
  const { data, isLoading } = useAdaptations(1, 5);
  const recentAdaptations = data?.data || [];

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            Simplify figurative language for better comprehension.
          </p>
        </div>

        {/* Quick Action */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Adapt Text</CardTitle>
            <CardDescription>
              Enter text containing idioms or conceptual metaphors to get a simplified version.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link to="/adapt">Start Adapting</Link>
            </Button>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Recent Adaptations</CardTitle>
              {recentAdaptations.length > 0 && (
                <Button asChild variant="ghost" size="sm">
                  <Link to="/history">View All</Link>
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <RecentActivitySkeleton />
            ) : recentAdaptations.length === 0 ? (
              <p className="text-gray-500 text-center py-6">
                No adaptations yet. Start by adapting your first text.
              </p>
            ) : (
              <div className="space-y-2">
                {recentAdaptations.map((adaptation) => {
                  const date = new Date(adaptation.createdAt);
                  const types = [...new Set(adaptation.expressions.map((e) => e.type))];

                  return (
                    <Link
                      key={adaptation.id}
                      to={`/history/${adaptation.id}`}
                      className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800 text-sm font-medium text-gray-600 dark:text-gray-400">
                        {adaptation.expressions.length}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                          {adaptation.originalText.slice(0, 60)}
                          {adaptation.originalText.length > 60 ? "..." : ""}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-400">
                            {date.toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })}
                          </span>
                          {types.map((type) => (
                            <Badge
                              key={type}
                              className={`text-xs ${expressionTypeColors[type]}`}
                            >
                              {expressionTypeLabels[type]}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info */}
        <div className="text-sm text-gray-500 flex items-center gap-4">
          <span>Supported types:</span>
          <Badge className={expressionTypeColors.idiom}>Idiom</Badge>
          <Badge className={expressionTypeColors.conceptual_metaphor}>Conceptual Metaphor</Badge>
        </div>
      </div>
    </AppLayout>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
