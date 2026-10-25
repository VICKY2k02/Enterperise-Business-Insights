
export interface AnalyticsTotals {
  revenue: number;
  orders: number;
  profit: number;
  customers: number;
}

export interface AnalyticsChanges {
  revenue_percentage: number | null;
  orders_percentage: number | null;
  profit_percentage: number | null;
}

export interface ComparisonPeriod {
  start_date: string;
  end_date: string;
  totals: AnalyticsTotals;
  changes: AnalyticsChanges;
}

export interface RevenueTrendPoint {
  period: string;
  revenue: number;
}

export interface OrderStatusCount {
  status: string;
  count: number;
}

export interface TopCategoryAnalytics {
  name: string;
  sales: number;
  items_sold: number;
  contribution_percentage: number;
}

export interface AnalyticsOverview {
  start_date: string;
  end_date: string;
  totals: AnalyticsTotals;
  revenue_trend_interval: string;
  revenue_trend: RevenueTrendPoint[];
  order_status_breakdown: OrderStatusCount[];
  top_category: TopCategoryAnalytics | null;
  previous_period: ComparisonPeriod | null;
}
