import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  // Public routes
  route("login", "routes/login.tsx"),

  // Protected routes (auth check handled by ProtectedRoute component)
  index("routes/home.tsx"),
  route("adapt", "routes/adapt.tsx"),
  route("history", "routes/history.tsx"),
  route("history/:id", "routes/history.$id.tsx"),
] satisfies RouteConfig;
