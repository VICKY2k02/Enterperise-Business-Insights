export interface KPIData {
  value: number;
  change: number;
}

export interface RevenueTrendItem {
  month: string;
  revenue: number;
}

export interface OrdersSummary {
  orders: number;
  sales: number;
}

export interface TopCategory {
  name: string;
  percentage: number;
}

export interface RecentActivity {
  id: number;
  title: string;
  description: string;
  value: string;
}

export interface DashboardKPIs {
  revenue: KPIData;
  orders: KPIData;
  customers: KPIData;
  profit: KPIData;
}

export interface DashboardAnalytics {
  revenueTrend: RevenueTrendItem[];
  ordersSummary: OrdersSummary;
  topCategory: TopCategory;
}

export interface DashboardData {
  kpis: DashboardKPIs;
  analytics: DashboardAnalytics;
  recentActivities: RecentActivity[];
}