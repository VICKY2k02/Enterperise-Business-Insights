import { StyleSheet, Text, View } from "react-native";

type RevenueData = {
  month: string;
  revenue: number;
};

type RevenueTrendProps = {
  data: RevenueData[];
};

export default function RevenueTrend({
  data,
}: RevenueTrendProps) {
  const maxRevenue = Math.max(
    ...data.map((item) => item.revenue)
  );

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Revenue Trend</Text>

      <View style={styles.chart}>
        {data.map((item) => {
          const barHeight =
            (item.revenue / maxRevenue) * 120;

          return (
            <View
              key={item.month}
              style={styles.barContainer}
            >
              <View
                style={[
                  styles.bar,
                  { height: barHeight },
                ]}
              />

              <Text style={styles.month}>
                {item.month}
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },

  title: {
    fontSize: 18,
    fontWeight: "700",
    color: "#222222",
    marginBottom: 20,
  },

  chart: {
    height: 160,
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-around",
  },

  barContainer: {
    height: "100%",
    alignItems: "center",
    justifyContent: "flex-end",
  },

  bar: {
    width: 24,
    backgroundColor: "#2563EB",
    borderRadius: 5,
    minHeight: 10,
  },

  month: {
    fontSize: 12,
    color: "#666666",
    marginTop: 8,
  },
});