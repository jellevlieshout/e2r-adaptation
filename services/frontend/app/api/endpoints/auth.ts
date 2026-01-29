import type { LoginRequest, AuthResponse, User } from "../types";
import { apiClient, isMockApiEnabled, setStoredToken, clearStoredToken } from "../client";
import { mockAuthResponse, mockUser, delay } from "../mock-data";

// =============================================================================
// Authentication Endpoints
// =============================================================================

/**
 * Login with email and password
 */
export async function login(credentials: LoginRequest): Promise<AuthResponse> {
  if (isMockApiEnabled()) {
    await delay(800);
    
    // Simple mock validation
    if (credentials.email === "demo@example.com" && credentials.password === "password") {
      setStoredToken(mockAuthResponse.token);
      return mockAuthResponse;
    }
    
    throw new Error("Invalid email or password");
  }

  const response = await apiClient<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: credentials,
    requiresAuth: false,
  });

  // Store the token
  setStoredToken(response.token);

  return response;
}

/**
 * Logout the current user
 */
export async function logout(): Promise<void> {
  if (isMockApiEnabled()) {
    await delay(300);
    clearStoredToken();
    return;
  }

  try {
    await apiClient<void>("/api/auth/logout", {
      method: "POST",
    });
  } finally {
    // Always clear the token, even if the API call fails
    clearStoredToken();
  }
}

/**
 * Get the current authenticated user
 */
export async function getCurrentUser(): Promise<User | null> {
  if (isMockApiEnabled()) {
    await delay(300);
    return mockUser;
  }

  try {
    return await apiClient<User>("/api/auth/me");
  } catch {
    return null;
  }
}

/**
 * Refresh the authentication token
 */
export async function refreshToken(): Promise<AuthResponse> {
  if (isMockApiEnabled()) {
    await delay(300);
    return mockAuthResponse;
  }

  const response = await apiClient<AuthResponse>("/api/auth/refresh", {
    method: "POST",
  });

  setStoredToken(response.token);

  return response;
}
