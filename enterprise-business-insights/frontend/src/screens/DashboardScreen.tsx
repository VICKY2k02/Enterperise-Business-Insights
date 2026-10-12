import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useCallback, useEffect, useState } from "react";

import { Ionicons } from "@expo/vector-icons";

import KpiCard from "../components/KpiCard";
import RevenueTrend from "../components/RevenueTrend";
import SalesSummary from "../components/SalesSummary";
import TopCategory from "../components/TopCategory";
import RecentActivity from "../components/RecentActivity";

import { getDashboardData } from "../services/dashboardService";
import { DashboardData } from "../types/dashboard";


export default function DashboardScreen() {
  const [dashboardData, setDashboardData] =
    useState<DashboardData | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(false);

  const [refreshing, setRefreshing] = useState(false);


  const loadDashboard = useCallback(async () => {
    try {
      setError(false);

      const data = await getDashboardData();

      setDashboardData(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);


  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);


  const handleRefresh = async () => {
    setRefreshing(true);

    await loadDashboard();
  };


  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator
          size="large"
          color="#2563EB"
        />

        <Text style={styles.loadingText}>
          Loading dashboard...
        </Text>
      </View>
    );
  }


  if (error || !dashboardData) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons
          name="alert-circle-outline"
          size={50}
          color="#DC2626"
        />

        <Text style={styles.errorTitle}>
          Unable to load dashboard
        </Text>

        <Text style={styles.errorMessage}>
          Please check your connection and try again.
        </Text>

        <Text
          style={styles.retryButton}
          onPress={loadDashboard}
        >
          Retry
        </Text>
      </View>
    );
  }


  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
        />
      }
    >
      {/* Header */}

      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>
            Good Morning
          </Text>

          <Text style={styles.userName}>
            Vikas Kumar
          </Text>
        </View>

        <View style={styles.headerIcons}>
          <Ionicons
            name="notifications-outline"
            size={26}
            color="#222222"
          />

          <Ionicons
            name="person-circle-outline"
            size={32}
            color="#222222"
            style={styles.profileIcon}
          />
        </View>
      </View>


      {/* KPI Section */}

      <Text style={styles.sectionTitle}>
        Overview
      </Text>

      <View style={styles.kpiContainer}>
        <KpiCard
          metricName="Revenue"
          currentValue={`₹${dashboardData.kpis.revenue.value.toLocaleString("en-IN")}`}
          percentageChange={
            dashboardData.kpis.revenue.change
          }
        />

        <KpiCard
          metricName="Orders"
          currentValue={dashboardData.kpis.orders.value.toLocaleString("en-IN")}
          percentageChange={
            dashboardData.kpis.orders.change
          }
        />

        <KpiCard
          metricName="Customers"
          currentValue={dashboardData.kpis.customers.value.toLocaleString("en-IN")}
          percentageChange={
            dashboardData.kpis.customers.change
          }
        />

        <KpiCard
          metricName="Profit"
          currentValue={`₹${dashboardData.kpis.profit.value.toLocaleString("en-IN")}`}
          percentageChange={
            dashboardData.kpis.profit.change
          }
        />
      </View>


      {/* Analytics Preview */}

      <Text style={styles.sectionTitle}>
        Analytics Preview
      </Text>

      <RevenueTrend
        data={dashboardData.analytics.revenueTrend}
      />

      <SalesSummary
        data={{
          orders:
            dashboardData.analytics.ordersSummary.orders,

          sales:
            `₹${dashboardData.analytics.ordersSummary.sales.toLocaleString("en-IN")}`,
        }}
      />

      <TopCategory
        data={dashboardData.analytics.topCategory}
      />


      {/* Recent Activity */}

      <RecentActivity
        activities={dashboardData.recentActivities}
      />
    </ScrollView>
  );
}


const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F5F7FA",
  },

  content: {
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 30,
  },

  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F5F7FA",
    paddingHorizontal: 30,
  },

  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: "#666666",
  },

  errorTitle: {
    marginTop: 14,
    fontSize: 20,
    fontWeight: "700",
    color: "#222222",
  },

  errorMessage: {
    marginTop: 8,
    fontSize: 14,
    color: "#666666",
    textAlign: "center",
  },

  retryButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: "#2563EB",
    color: "#FFFFFF",
    borderRadius: 8,
    overflow: "hidden",
    fontSize: 15,
    fontWeight: "600",
  },

  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },

  greeting: {
    fontSize: 14,
    color: "#666666",
    marginBottom: 4,
  },

  userName: {
    fontSize: 24,
    fontWeight: "700",
    color: "#222222",
  },

  headerIcons: {
    flexDirection: "row",
    alignItems: "center",
  },

  profileIcon: {
    marginLeft: 16,
  },

  sectionTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#222222",
    marginBottom: 14,
    marginTop: 4,
  },

  kpiContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: 10,
  },
});