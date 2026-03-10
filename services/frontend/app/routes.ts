import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/runs.tsx"),
  route("runs/compare", "routes/runs-compare.tsx"),
  route("runs/:runId", "routes/runs.$runId.tsx"),
] satisfies RouteConfig;
