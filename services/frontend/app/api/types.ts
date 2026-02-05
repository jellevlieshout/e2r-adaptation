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
// VUAMC (Metaphor) Types
// =============================================================================

export interface Token {
  text: string;
  lemma: string;
  pos: string;
  is_metaphor: boolean;
  metaphor_type?: string;
  function?: string;
  status?: string;
}

export interface Sentence {
  id: string;
  text: string;
  tokens: Token[];
}

export interface MetaphorResponse {
  token: Token;
  sentence: Sentence;
  document_id: string;
}

// =============================================================================
// SemEval Types
// =============================================================================

export interface SemEvalSample {
  id: string;
  mwe1: string;
  language: string;
  sentence1: string;
  sentence2?: string;
  mwe2?: string;
  sim?: string;
  label?: string;
  context_previous?: string;
  context_next?: string;
  setting?: string;
  alternative1?: string;
  alternative2?: string;
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
