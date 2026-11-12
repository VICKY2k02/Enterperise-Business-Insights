
import * as SecureStore from "expo-secure-store";
import type { DashboardData } from "../types/dashboard";

const API_BASE_URL = "http://192.168.1.7:8000";
const TOKEN_KEY = "enterprise_business_insights_access_token";

export async function getDashboardData(): Promise<DashboardData> {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);

  if (!token) {
    throw new Error("Your session has expired. Please log in again.");
  }

  const response = await fetch(`${API_BASE_URL}/api/dashboard`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });

  if (response.status === 401) {
    throw new Error("Authentication failed. Please log in again.");
  }

  if (!response.ok) {
    throw new Error(`Unable to load dashboard data. HTTP ${response.status}`);
  }

  return (await response.json()) as DashboardData;
}
