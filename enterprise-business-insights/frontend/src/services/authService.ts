
const API_BASE_URL = "http://192.168.1.7:8000";

export type UserRole = "Admin" | "Analyst" | "Viewer";

export interface AuthUser {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data.detail ?? "Something went wrong. Please try again.";
  } catch {
    return "Unable to connect to the server. Please try again.";
  }
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as LoginResponse;
}

export async function getCurrentUser(
  token: string,
): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as AuthUser;
}
