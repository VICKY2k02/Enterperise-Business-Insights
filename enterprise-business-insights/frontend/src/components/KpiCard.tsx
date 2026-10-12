import { StyleSheet, Text, View } from "react-native";

type KpiCardProps = {
  metricName: string;
  currentValue: string;
  percentageChange: number;
};

export default function KpiCard({
  metricName,
  currentValue,
  percentageChange,
}: KpiCardProps) {
  const isPositive = percentageChange >= 0;

  return (
    <View style={styles.card}>
      <Text style={styles.metricName}>{metricName}</Text>

      <Text style={styles.currentValue}>{currentValue}</Text>

      <View style={styles.changeContainer}>
        <Text style={styles.indicator}>
          {isPositive ? "↑" : "↓"}
        </Text>

        <Text
          style={[
            styles.percentage,
            isPositive ? styles.positive : styles.negative,
          ]}
        >
          {Math.abs(percentageChange)}%
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "48%",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 3,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 5,
    shadowOffset: {
      width: 0,
      height: 2,
    },
  },

  metricName: {
    fontSize: 14,
    color: "#666666",
    marginBottom: 8,
  },

  currentValue: {
    fontSize: 24,
    fontWeight: "700",
    color: "#222222",
    marginBottom: 8,
  },

  changeContainer: {
    flexDirection: "row",
    alignItems: "center",
  },

  indicator: {
    fontSize: 18,
    marginRight: 4,
  },

  percentage: {
    fontSize: 14,
    fontWeight: "600",
  },

  positive: {
    color: "#16A34A",
  },

  negative: {
    color: "#DC2626",
  },
});