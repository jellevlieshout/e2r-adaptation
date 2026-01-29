// =============================================================================
// User and Authentication Types
// =============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

// =============================================================================
// Figurative Expression Types
// =============================================================================

export type ExpressionType =
  | "idiom"
  | "conceptual_metaphor";

export interface FigurativeExpression {
  id: string;
  type: ExpressionType;
  original: string;
  startIndex: number;
  endIndex: number;
  explanation: string;
  simplifiedVersion: string;
}

// =============================================================================
// Adaptation Types
// =============================================================================

export interface AdaptationRequest {
  text: string;
}

export interface AdaptationResponse {
  id: string;
  originalText: string;
  adaptedText: string;
  expressions: FigurativeExpression[];
  createdAt: string;
}

// =============================================================================
// API Response Wrappers
// =============================================================================

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
