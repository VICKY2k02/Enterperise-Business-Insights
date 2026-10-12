import { StyleSheet, Text, View } from "react-native";

type TopCategoryData = {
  name: string;
  percentage: number;
};

type TopCategoryProps = {
  data: TopCategoryData;
};

export default function TopCategory({
  data,
}: TopCategoryProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        Top Performing Category
      </Text>

      <Text style={styles.categoryName}>
        {data.name}
      </Text>

      <Text style={styles.percentage}>
        {data.percentage}% of total sales
      </Text>

      <View style={styles.progressBackground}>
        <View
          style={[
            styles.progress,
            {
              width: `${data.percentage}%`,
            },
          ]}
        />
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
    marginBottom: 14,
  },

  categoryName: {
    fontSize: 20,
    fontWeight: "700",
    color: "#222222",
    marginBottom: 4,
  },

  percentage: {
    fontSize: 14,
    color: "#666666",
    marginBottom: 12,
  },

  progressBackground: {
    height: 10,
    backgroundColor: "#E5E7EB",
    borderRadius: 5,
    overflow: "hidden",
  },

  progress: {
    height: "100%",
    backgroundColor: "#2563EB",
    borderRadius: 5,
  },
});