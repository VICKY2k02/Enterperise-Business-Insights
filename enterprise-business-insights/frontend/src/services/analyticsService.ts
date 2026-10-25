
import type { AnalyticsOverview } from "../types/analytics";

const API_BASE_URL = "http://192.168.1.4:8000";

export interface AnalyticsQuery {
  startDate: string;
  endDate: string;
  comparisonPeriod?: boolean;
}

export async function getAnalyticsOverview(
  query: AnalyticsQuery,
  signal?: AbortSignal,
): Promise<AnalyticsOverview> {
  const params = new URLSearchParams({
    start_date: query.startDate,
    end_date: query.endDate,
    comparison_period: String(query.comparisonPeriod ?? true),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/analytics/overview?${params.toString()}`,
    { signal },
  );

  if (!response.ok) {
    throw new Error(
      `Unable to load analytics. HTTP ${response.status}`,
    );
  }

  return (await response.json()) as AnalyticsOverview;
}
