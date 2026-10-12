import { StyleSheet, Text, View } from "react-native";

import { Activity } from "../utils/dashboardMockData";

type ActivityItemProps = {
  activity: Activity;
};

export default function ActivityItem({
  activity,
}: ActivityItemProps) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>{activity.title}</Text>

        <Text style={styles.description}>
          {activity.description}
        </Text>
      </View>

      <Text style={styles.value}>
        {activity.value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },

  content: {
    flex: 1,
    marginRight: 10,
  },

  title: {
    fontSize: 15,
    fontWeight: "600",
    color: "#222222",
    marginBottom: 4,
  },

  description: {
    fontSize: 13,
    color: "#666666",
  },

  value: {
    fontSize: 14,
    fontWeight: "600",
    color: "#2563EB",
  },
});