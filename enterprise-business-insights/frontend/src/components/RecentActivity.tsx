import { StyleSheet, Text, View } from "react-native";

type Activity = {
  id: number;
  title: string;
  description: string;
  value: string;
};

type RecentActivityProps = {
  activities: Activity[];
};

export default function RecentActivity({
  activities,
}: RecentActivityProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        Recent Activity
      </Text>

      {activities.map((activity) => (
        <View
          key={activity.id}
          style={styles.activity}
        >
          <View style={styles.activityContent}>
            <Text style={styles.activityTitle}>
              {activity.title}
            </Text>

            <Text style={styles.description}>
              {activity.description}
            </Text>
          </View>

          <Text style={styles.value}>
            {activity.value}
          </Text>
        </View>
      ))}
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
    marginBottom: 4,
  },

  activity: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#EEEEEE",
  },

  activityContent: {
    flex: 1,
    marginRight: 12,
  },

  activityTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#222222",
    marginBottom: 4,
  },

  description: {
    fontSize: 13,
    color: "#777777",
  },

  value: {
    fontSize: 13,
    fontWeight: "600",
    color: "#333333",
  },
});