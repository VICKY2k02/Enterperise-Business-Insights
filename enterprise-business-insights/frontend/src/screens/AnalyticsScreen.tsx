
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  getAnalyticsOverview,
} from "../services/analyticsService";

import type {
  AnalyticsOverview,
  AnalyticsTotals,
  OrderStatusCount,
  RevenueTrendPoint,
} from "../types/analytics";

type DateRange = {
  startDate: string;
  endDate: string;
};

type FilterOption =
  | "Today"
  | "Last 7 Days"
  | "Last 30 Days"
  | "This Month"
  | "Custom";

const FILTERS: FilterOption[] = [
  "Today",
  "Last 7 Days",
  "Last 30 Days",
  "This Month",
  "Custom",
];

function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function getDateRange(filter: FilterOption): DateRange {
  const today = new Date();
  const endDate = formatDate(today);
  const start = new Date(today);

  if (filter === "Today") {
    return { startDate: endDate, endDate };
  }

  if (filter === "Last 7 Days") {
    start.setDate(today.getDate() - 6);
  } else if (filter === "Last 30 Days") {
    start.setDate(today.getDate() - 29);
  } else {
    start.setDate(1);
  }

  return {
    startDate: formatDate(start),
    endDate,
  };
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-IN").format(value);
}

function isValidDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }

  const parsed = new Date(`${value}T00:00:00`);

  return (
    !Number.isNaN(parsed.getTime()) &&
    formatDate(parsed) === value
  );
}

function MetricCard({
  title,
  value,
  change,
}: {
  title: string;
  value: string;
  change?: number | null;
}) {
  const hasChange = change !== undefined && change !== null;

  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricTitle}>{title}</Text>
      <Text style={styles.metricValue}>{value}</Text>

      {hasChange ? (
        <Text
          style={[
            styles.metricChange,
            change >= 0 ? styles.positive : styles.negative,
          ]}
        >
          {change > 0 ? "↑" : change < 0 ? "↓" : "—"}{" "}
          {Math.abs(change).toFixed(1)}% vs previous period
        </Text>
      ) : (
        <Text style={styles.mutedText}>No comparison available</Text>
      )}
    </View>
  );
}

function RevenueChart({
  data,
}: {
  data: RevenueTrendPoint[];
}) {
  const maxRevenue = Math.max(
    0,
    ...data.map((item) => item.revenue),
  );

  if (data.length === 0 || maxRevenue === 0) {
    return (
      <Text style={styles.emptyText}>
        No revenue trend data for this period.
      </Text>
    );
  }

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.chartContent}
    >
      {data.map((item, index) => {
        const height = Math.max(
          4,
          (item.revenue / maxRevenue) * 130,
        );

        return (
          <View
            key={`${item.period}-${index}`}
            style={styles.chartColumn}
          >
            <Text style={styles.barValue}>
              {formatNumber(item.revenue)}
            </Text>

            <View style={styles.barArea}>
              <View
                style={[
                  styles.bar,
                  { height },
                ]}
              />
            </View>

            <Text style={styles.barLabel}>
              {item.period}
            </Text>
          </View>
        );
      })}
    </ScrollView>
  );
}

function OrderStatusList({
  statuses,
}: {
  statuses: OrderStatusCount[];
}) {
  if (statuses.length === 0) {
    return (
      <Text style={styles.emptyText}>
        No order status data for this period.
      </Text>
    );
  }

  return (
    <View style={styles.statusList}>
      {statuses.map((item) => (
        <View key={item.status} style={styles.statusRow}>
          <Text style={styles.statusName}>
            {item.status.replace(/_/g, " ")}
          </Text>
          <Text style={styles.statusCount}>
            {formatNumber(item.count)}
          </Text>
        </View>
      ))}
    </View>
  );
}

export default function AnalyticsScreen() {
  const initialRange = useMemo(
    () => getDateRange("This Month"),
    [],
  );

  const [activeFilter, setActiveFilter] =
    useState<FilterOption>("This Month");

  const [appliedRange, setAppliedRange] =
    useState<DateRange>(initialRange);

  const [customStartDate, setCustomStartDate] =
    useState(initialRange.startDate);

  const [customEndDate, setCustomEndDate] =
    useState(initialRange.endDate);

  const [analytics, setAnalytics] =
    useState<AnalyticsOverview | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateError, setDateError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadAnalytics() {
      setLoading(true);
      setError(null);

      try {
        const result = await getAnalyticsOverview(
          {
            startDate: appliedRange.startDate,
            endDate: appliedRange.endDate,
            comparisonPeriod: true,
          },
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setAnalytics(result);
        }
      } catch (err: unknown) {
        if (controller.signal.aborted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadAnalytics();

    return () => {
      controller.abort();
    };
  }, [appliedRange, retryCount]);

  const applyFilter = (filter: FilterOption) => {
    setActiveFilter(filter);
    setDateError(null);

    if (filter === "Custom") {
      return;
    }

    const range = getDateRange(filter);
    setCustomStartDate(range.startDate);
    setCustomEndDate(range.endDate);
    setAppliedRange(range);
  };

  const applyCustomRange = () => {
    if (
      !isValidDate(customStartDate) ||
      !isValidDate(customEndDate)
    ) {
      setDateError("Enter valid dates in YYYY-MM-DD format.");
      return;
    }

    if (customStartDate > customEndDate) {
      setDateError("Start date must be on or before end date.");
      return;
    }

    setDateError(null);
    setAppliedRange({
      startDate: customStartDate,
      endDate: customEndDate,
    });
  };

  const retry = useCallback(() => {
    setRetryCount((count) => count + 1);
  }, []);

  const totals: AnalyticsTotals | null =
    analytics?.totals ?? null;

  const changes = analytics?.previous_period?.changes;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
        <Text style={styles.subtitle}>
          Business performance overview
        </Text>
      </View>

      <View style={styles.filterSection}>
        <Text style={styles.sectionTitle}>Date range</Text>

        <View style={styles.filterList}>
          {FILTERS.map((filter) => {
            const selected = activeFilter === filter;

            return (
              <Pressable
                key={filter}
                onPress={() => applyFilter(filter)}
                style={[
                  styles.filterButton,
                  selected && styles.selectedFilter,
                ]}
                accessibilityRole="button"
                accessibilityState={{ selected }}
              >
                <Text
                  style={[
                    styles.filterText,
                    selected && styles.selectedFilterText,
                  ]}
                >
                  {filter === "Custom"
                    ? "Custom Range"
                    : filter}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {activeFilter === "Custom" && (
          <View style={styles.customDateCard}>
            <Text style={styles.inputLabel}>
              Start date (YYYY-MM-DD)
            </Text>
            <TextInput
              value={customStartDate}
              onChangeText={setCustomStartDate}
              placeholder="2026-10-01"
              style={styles.dateInput}
              autoCapitalize="none"
              accessibilityLabel="Custom start date"
            />

            <Text style={styles.inputLabel}>
              End date (YYYY-MM-DD)
            </Text>
            <TextInput
              value={customEndDate}
              onChangeText={setCustomEndDate}
              placeholder="2026-10-22"
              style={styles.dateInput}
              autoCapitalize="none"
              accessibilityLabel="Custom end date"
            />

            {dateError && (
              <Text style={styles.errorText}>{dateError}</Text>
            )}

            <Pressable
              onPress={applyCustomRange}
              style={styles.applyButton}
            >
              <Text style={styles.applyButtonText}>
                Apply Date Range
              </Text>
            </Pressable>
          </View>
        )}

        <Text style={styles.periodText}>
          Showing {appliedRange.startDate} to{" "}
          {appliedRange.endDate}
        </Text>
      </View>

      {loading && (
        <View style={styles.messageCard}>
          <ActivityIndicator size="large" color="#2563EB" />
          <Text style={styles.messageText}>
            Loading analytics...
          </Text>
        </View>
      )}

      {!loading && error && (
        <View style={styles.messageCard}>
          <Text style={styles.errorTitle}>
            Unable to load analytics
          </Text>
          <Text style={styles.errorText}>{error}</Text>

          <Pressable onPress={retry} style={styles.applyButton}>
            <Text style={styles.applyButtonText}>
              Retry
            </Text>
          </Pressable>
        </View>
      )}

      {!loading && !error && analytics && (
        <>
          <Text style={styles.sectionTitle}>
            Performance summary
          </Text>

          <View style={styles.metricGrid}>
            <MetricCard
              title="Revenue"
              value={formatCurrency(totals?.revenue ?? 0)}
              change={changes?.revenue_percentage}
            />

            <MetricCard
              title="Orders"
              value={formatNumber(totals?.orders ?? 0)}
              change={changes?.orders_percentage}
            />

            <MetricCard
              title="Profit"
              value={formatCurrency(totals?.profit ?? 0)}
              change={changes?.profit_percentage}
            />

            <MetricCard
              title="Customers"
              value={formatNumber(totals?.customers ?? 0)}
            />
          </View>

          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>
              Revenue trend
            </Text>
            <Text style={styles.cardSubtitle}>
              Interval: {analytics.revenue_trend_interval}
            </Text>
            <RevenueChart data={analytics.revenue_trend} />
          </View>

          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>
              Order status breakdown
            </Text>
            <OrderStatusList
              statuses={analytics.order_status_breakdown}
            />
          </View>

          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>
              Top category
            </Text>

            {analytics.top_category ? (
              <>
                <Text style={styles.categoryName}>
                  {analytics.top_category.name}
                </Text>

                <View style={styles.categoryRow}>
                  <Text style={styles.categoryLabel}>
                    Sales
                  </Text>
                  <Text style={styles.categoryValue}>
                    {formatCurrency(
                      analytics.top_category.sales,
                    )}
                  </Text>
                </View>

                <View style={styles.categoryRow}>
                  <Text style={styles.categoryLabel}>
                    Items sold
                  </Text>
                  <Text style={styles.categoryValue}>
                    {formatNumber(
                      analytics.top_category.items_sold,
                    )}
                  </Text>
                </View>

                <View style={styles.categoryRow}>
                  <Text style={styles.categoryLabel}>
                    Revenue contribution
                  </Text>
                  <Text style={styles.categoryValue}>
                    {analytics.top_category.contribution_percentage.toFixed(
                      1,
                    )}
                    %
                  </Text>
                </View>
              </>
            ) : (
              <Text style={styles.emptyText}>
                No category sales found for this period.
              </Text>
            )}
          </View>

          <Text style={styles.footerText}>
            Data from your business analytics API
          </Text>
        </>
      )}

      {!loading && !error && !analytics && (
        <View style={styles.messageCard}>
          <Text style={styles.emptyText}>
            No analytics data is available.
          </Text>
          <Pressable onPress={retry} style={styles.applyButton}>
            <Text style={styles.applyButtonText}>
              Reload
            </Text>
          </Pressable>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#F5F7FB",
  },
  content: {
    padding: 18,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 22,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#172033",
  },
  subtitle: {
    marginTop: 5,
    fontSize: 14,
    color: "#687386",
  },
  filterSection: {
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderRadius: 16,
    marginBottom: 22,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#172033",
    marginBottom: 12,
  },
  filterList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  filterButton: {
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: "#F0F2F7",
  },
  selectedFilter: {
    backgroundColor: "#2563EB",
  },
  filterText: {
    color: "#475467",
    fontSize: 12,
    fontWeight: "600",
  },
  selectedFilterText: {
    color: "#FFFFFF",
  },
  customDateCard: {
    marginTop: 16,
    gap: 8,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#475467",
  },
  dateInput: {
    borderWidth: 1,
    borderColor: "#D8DEE9",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: "#172033",
    backgroundColor: "#FFFFFF",
  },
  applyButton: {
    marginTop: 8,
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
    backgroundColor: "#2563EB",
  },
  applyButtonText: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
  periodText: {
    color: "#687386",
    fontSize: 12,
    marginTop: 14,
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 20,
  },
  metricCard: {
    width: "48%",
    flexGrow: 1,
    flexBasis: "44%",
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    minHeight: 125,
  },
  metricTitle: {
    fontSize: 13,
    color: "#687386",
    marginBottom: 10,
  },
  metricValue: {
    fontSize: 21,
    fontWeight: "700",
    color: "#172033",
  },
  metricChange: {
    marginTop: 9,
    fontSize: 11,
    fontWeight: "600",
  },
  positive: {
    color: "#15803D",
  },
  negative: {
    color: "#DC2626",
  },
  mutedText: {
    marginTop: 9,
    fontSize: 11,
    color: "#8992A3",
  },
  sectionCard: {
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderRadius: 16,
    marginBottom: 18,
  },
  cardSubtitle: {
    color: "#687386",
    fontSize: 12,
    marginTop: -6,
    marginBottom: 18,
  },
  chartContent: {
    paddingTop: 8,
    paddingBottom: 6,
    paddingRight: 8,
    gap: 14,
  },
  chartColumn: {
    width: 68,
    alignItems: "center",
  },
  barValue: {
    fontSize: 10,
    color: "#687386",
    marginBottom: 5,
  },
  barArea: {
    height: 140,
    width: 34,
    justifyContent: "flex-end",
    alignItems: "center",
    backgroundColor: "#F0F5FF",
    borderRadius: 8,
    overflow: "hidden",
  },
  bar: {
    width: 34,
    backgroundColor: "#3B82F6",
    borderTopLeftRadius: 6,
    borderTopRightRadius: 6,
  },
  barLabel: {
    marginTop: 8,
    fontSize: 10,
    color: "#687386",
  },
  statusList: {
    gap: 14,
  },
  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#EEF0F5",
  },
  statusName: {
    fontSize: 14,
    color: "#475467",
    textTransform: "capitalize",
  },
  statusCount: {
    fontSize: 14,
    fontWeight: "700",
    color: "#172033",
  },
  categoryName: {
    fontSize: 20,
    fontWeight: "700",
    color: "#2563EB",
    marginBottom: 14,
  },
  categoryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#EEF0F5",
    gap: 12,
  },
  categoryLabel: {
    color: "#687386",
    fontSize: 13,
    flexShrink: 1,
  },
  categoryValue: {
    color: "#172033",
    fontWeight: "600",
    fontSize: 13,
  },
  messageCard: {
    backgroundColor: "#FFFFFF",
    padding: 24,
    borderRadius: 16,
    alignItems: "center",
    marginBottom: 20,
    gap: 12,
  },
  messageText: {
    color: "#687386",
    fontSize: 14,
  },
  errorTitle: {
    color: "#B91C1C",
    fontSize: 17,
    fontWeight: "700",
  },
  errorText: {
    color: "#B91C1C",
    fontSize: 13,
  },
  emptyText: {
    color: "#687386",
    fontSize: 13,
    paddingVertical: 12,
  },
  footerText: {
    textAlign: "center",
    color: "#8992A3",
    fontSize: 11,
    marginTop: 2,
  },
});
