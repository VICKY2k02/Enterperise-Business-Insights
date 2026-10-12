import { DashboardData } from "../types/dashboard";

const API_BASE_URL = "http://192.168.1.3:8000";

export async function getDashboardData(): Promise<DashboardData> {
  const response = await fetch(
    `${API_BASE_URL}/api/dashboard`
  );

  if (!response.ok) {
    throw new Error("Unable to load dashboard data.");
  }

  const data: DashboardData = await response.json();

  return data;
}