import { NavigationContainer } from "@react-navigation/native";

import BottomTabNavigator from "./src/navigation/BottomTabNavigator";
import {AuthProvider} from "./src/context/AuthContext";

export default function App() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <BottomTabNavigator />
      </NavigationContainer>
    </AuthProvider>
  );
}