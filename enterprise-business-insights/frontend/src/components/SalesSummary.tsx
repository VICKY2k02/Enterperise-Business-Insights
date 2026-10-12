import { StyleSheet, Text, View } from "react-native";

type SalesSummaryData = {
  orders: number;
  sales: string;
};

type SalesSummaryProps = {
  data: SalesSummaryData;
};

export default function SalesSummary({
  data,
}: SalesSummaryProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        Sales / Orders Summary
      </Text>

      <View style={styles.row}>
        <View style={styles.item}>
          <Text style={styles.label}>
            Total Orders
          </Text>

          <Text style={styles.value}>
            {data.orders}
          </Text>
        </View>

        <View style={styles.item}>
          <Text style={styles.label}>
            Total Sales
          </Text>

          <Text style={styles.value}>
            {data.sales}
          </Text>
        </View>
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
    marginBottom: 18,
  },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
  },

  item: {
    width: "48%",
  },

  label: {
    fontSize: 13,
    color: "#666666",
    marginBottom: 6,
  },

  value: {
    fontSize: 22,
    fontWeight: "700",
    color: "#222222",
  },
});