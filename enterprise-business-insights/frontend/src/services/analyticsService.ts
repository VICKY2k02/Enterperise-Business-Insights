
import * as SecureStore from "expo-secure-store";
import type { AnalyticsOverview } from "../types/analytics";

const API_BASE_URL = "http://192.168.1.15:8000";
const TOKEN_KEY = "enterprise_business_insights_access_token";

export interface AnalyticsQuery {
  startDate: string;
  endDate: string;
  comparisonPeriod?: boolean;
}

export async function getAnalyticsOverview(
  query: AnalyticsQuery,
  signal?: AbortSignal,
): Promise<AnalyticsOverview> {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);

  if (!token) {
    throw new Error("Your session has expired. Please log in again.");
  }

  const params = new URLSearchParams({
    start_date: query.startDate,
    end_date: query.endDate,
    comparison_period: String(query.comparisonPeriod ?? true),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/analytics/overview?${params.toString()}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
      signal,
    },
  );

  if (response.status === 401) {
    throw new Error("Authentication failed. Please log in again.");
  }

  if (!response.ok) {
    throw new Error(`Unable to load analytics. HTTP ${response.status}`);
  }

  return (await response.json()) as AnalyticsOverview;
}
