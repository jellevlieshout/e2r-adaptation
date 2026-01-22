import { useNavigate, useLocation } from "react-router";
import { useAuth } from "~/context/auth-context";
import { useEffect, type ReactNode } from "react";

// =============================================================================
// Loading Spinner
// =============================================================================

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
      <div className="flex flex-col items-center gap-3">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    </div>
  );
}

// =============================================================================
// Protected Route Component
// =============================================================================

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/login", { state: { from: location }, replace: true });
    }
  }, [isLoading, isAuthenticated, location, navigate]);

  if (isLoading || !isAuthenticated) {
    return <LoadingSpinner />;
  }

  return <>{children}</>;
}
