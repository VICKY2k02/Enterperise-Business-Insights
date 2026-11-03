
import {
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { useAuth } from "../context/AuthContext";

export default function ProfileScreen() {
  const { user, logout } = useAuth();

  async function handleLogout() {
    Alert.alert(
      "Logout",
      "Are you sure you want to log out?",
      [
        {
          text: "Cancel",
          style: "cancel",
        },
        {
          text: "Logout",
          style: "destructive",
          onPress: () => {
            void logout().catch(() => {
              Alert.alert(
                "Logout failed",
                "Unable to clear the saved session. Please try again.",
              );
            });
          },
        },
      ],
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile</Text>

      <View style={styles.profileCard}>
        <Text style={styles.label}>Full Name : {user?.full_name ?? "Not available"}</Text>
        {/* <Text style={styles.value}>{user?.full_name ?? "Not available"}</Text> */}

        <Text style={styles.label}>Email : {user?.email ?? "Not available"}</Text>
        {/* <Text style={styles.value}>{user?.email ?? "Not available"}</Text> */}

        <Text style={styles.label}>Role : {user?.role ?? "Not available"}</Text>
        {/* <Text style={styles.value}>{user?.role ?? "Not available"}</Text> */}
      </View>

      <TouchableOpacity
        style={styles.logoutButton}
        onPress={handleLogout}
        accessibilityRole="button"
      >
        <Text style={styles.logoutButtonText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    backgroundColor: "#F3F6FB",
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    marginBottom: 20,
    color: "#1E293B",
  },
  profileCard: {
    width: "100%",
    maxWidth: 440,
    padding: 20,
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
  },
  // label: {
  //   marginTop: 10,
  //   fontSize: 13,
  //   color: "#64748B",
  // },
  label: {
    marginTop: 4,
    fontSize: 16,
    fontWeight: "600",
    color: "#1E293B",
    marginBottom: 5,
  },
  logoutButton: {
    width: "100%",
    maxWidth: 440,
    minHeight: 48,
    marginTop: 24,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: "#ea4e11",
  },
  logoutButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
});
