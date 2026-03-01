import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View
} from "react-native";
import Constants from "expo-constants";
import * as Notifications from "expo-notifications";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true
  })
});

function formatDate(value) {
  if (!value) {
    return "null";
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    return value;
  }
  return d.toLocaleString();
}

function ActionButton({ disabled, label, onPress, shineTranslate, variant = "primary" }) {
  const isPrimary = variant === "primary";
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.buttonBase,
        isPrimary ? styles.buttonPrimary : styles.buttonSecondary,
        pressed && !disabled ? styles.buttonPressed : null,
        disabled ? styles.buttonDisabled : null
      ]}
    >
      <Animated.View
        pointerEvents="none"
        style={[
          styles.buttonShine,
          {
            transform: [{ translateX: shineTranslate }, { rotate: "24deg" }]
          }
        ]}
      />
      <Text style={[styles.buttonText, isPrimary ? styles.buttonTextPrimary : styles.buttonTextSecondary]}>
        {label}
      </Text>
    </Pressable>
  );
}

export default function App() {
  const [pushToken, setPushToken] = useState("");
  const [status, setStatus] = useState({ last_checked_at: null, last_updated_at: null });
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const revealAnims = useRef(Array.from({ length: 4 }, () => new Animated.Value(0))).current;
  const ambientAnim = useRef(new Animated.Value(0)).current;

  const apiBaseUrl = useMemo(() => {
    const fromPublic = process.env.EXPO_PUBLIC_API_BASE_URL;
    const fromExpoConfig = Constants.expoConfig?.extra?.apiBaseUrl;
    return (fromPublic || fromExpoConfig || "http://127.0.0.1:8000").replace(/\/+$/, "");
  }, []);

  const expoProjectId = useMemo(() => {
    return (
      process.env.EXPO_PUBLIC_EAS_PROJECT_ID ||
      Constants.easConfig?.projectId ||
      Constants.expoConfig?.extra?.eas?.projectId ||
      ""
    );
  }, []);

  const fetchStatus = useCallback(async () => {
    setLoadingStatus(true);
    try {
      const response = await fetch(`${apiBaseUrl}/status`);
      if (!response.ok) {
        throw new Error(`GET /status failed: ${response.status}`);
      }
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      setMessage(String(error));
    } finally {
      setLoadingStatus(false);
    }
  }, [apiBaseUrl]);

  const requestAndRegisterPushToken = useCallback(async () => {
    setBusy(true);
    setMessage("");
    try {
      if (Platform.OS === "android") {
        await Notifications.setNotificationChannelAsync("default", {
          name: "default",
          importance: Notifications.AndroidImportance.DEFAULT
        });
      }

      const permission = await Notifications.getPermissionsAsync();
      let finalStatus = permission.status;
      if (finalStatus !== "granted") {
        const req = await Notifications.requestPermissionsAsync();
        finalStatus = req.status;
      }
      if (finalStatus !== "granted") {
        throw new Error("Notification permission not granted.");
      }

      if (!expoProjectId) {
        throw new Error(
          'No "projectId" found. Set EXPO_PUBLIC_EAS_PROJECT_ID or app.json -> expo.extra.eas.projectId.'
        );
      }

      const tokenResponse = await Notifications.getExpoPushTokenAsync({
        projectId: expoProjectId
      });
      const token = tokenResponse.data;
      setPushToken(token);

      const registerResponse = await fetch(`${apiBaseUrl}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ push_token: token })
      });
      if (!registerResponse.ok) {
        throw new Error(`POST /register failed: ${registerResponse.status}`);
      }

      setMessage("Push token registered.");
      await fetchStatus();
    } catch (error) {
      setMessage(String(error));
    } finally {
      setBusy(false);
    }
  }, [apiBaseUrl, expoProjectId, fetchStatus]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    const revealSequence = Animated.stagger(
      110,
      revealAnims.map((anim) =>
        Animated.timing(anim, {
          toValue: 1,
          duration: 550,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true
        })
      )
    );

    const ambientLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(ambientAnim, {
          toValue: 1,
          duration: 4600,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true
        }),
        Animated.timing(ambientAnim, {
          toValue: 0,
          duration: 4600,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true
        })
      ])
    );

    revealSequence.start();
    ambientLoop.start();

    return () => {
      revealSequence.stop();
      ambientLoop.stop();
    };
  }, [ambientAnim, revealAnims]);

  const heroFloat = ambientAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-8, 8]
  });

  const orbFloat = ambientAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [14, -12]
  });

  const orbFloatInverse = ambientAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-12, 10]
  });

  const shineTranslate = ambientAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-220, 260]
  });

  const messageTone = message.toLowerCase().includes("error") ? styles.messageError : styles.messageNeutral;
  const loadingAny = busy || loadingStatus;

  const revealStyle = (index) => ({
    opacity: revealAnims[index],
    transform: [
      {
        translateY: revealAnims[index].interpolate({
          inputRange: [0, 1],
          outputRange: [26, 0]
        })
      }
    ]
  });

  const heroTranslateY = Animated.add(
    revealAnims[0].interpolate({
      inputRange: [0, 1],
      outputRange: [26, 0]
    }),
    heroFloat
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View pointerEvents="none" style={styles.backdrop}>
          <Animated.View style={[styles.backdropOrbA, { transform: [{ translateY: orbFloat }] }]} />
          <Animated.View style={[styles.backdropOrbB, { transform: [{ translateY: orbFloatInverse }] }]} />
          <Animated.View style={[styles.backdropOrbC, { transform: [{ translateY: orbFloat }] }]} />
        </View>

        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          bounces={false}
          alwaysBounceVertical={false}
        >
          <Animated.View style={[styles.hero, { opacity: revealAnims[0], transform: [{ translateY: heroTranslateY }] }]}>
            <Text style={styles.title}>TDR Notify</Text>
            <Text style={styles.subtitle}>Tokyo Disney Resort monitor and push relay</Text>
            <View style={styles.apiBadge}>
              <Text style={styles.apiBadgeLabel}>API Base URL</Text>
              <Text style={styles.apiBadgeValue}>{apiBaseUrl}</Text>
            </View>
          </Animated.View>

          <Animated.View style={[styles.section, revealStyle(1)]}>
            <Text style={styles.sectionTitle}>Push Registration</Text>
            <Text style={styles.sectionDescription}>Enable notifications and register the Expo push token.</Text>
            <ActionButton
              disabled={busy}
              label={busy ? "Registering..." : "Enable Notifications & Register"}
              onPress={requestAndRegisterPushToken}
              shineTranslate={shineTranslate}
              variant="primary"
            />
            <Text style={styles.label}>Expo Push Token</Text>
            <Text selectable style={styles.mono}>
              {pushToken || "(not registered yet)"}
            </Text>
          </Animated.View>

          <Animated.View style={[styles.section, revealStyle(2)]}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.sectionTitle}>Monitor Status</Text>
              {loadingAny ? <ActivityIndicator size="small" color="#ffe79a" /> : null}
            </View>
            <Text style={styles.sectionDescription}>Check the most recent crawler and update timestamps.</Text>
            <ActionButton
              disabled={loadingStatus}
              label={loadingStatus ? "Refreshing..." : "Refresh Status"}
              onPress={fetchStatus}
              shineTranslate={shineTranslate}
              variant="secondary"
            />
            <View style={styles.dataRow}>
              <Text style={styles.label}>last_checked_at</Text>
              <Text style={styles.dataValue}>{formatDate(status.last_checked_at)}</Text>
            </View>
            <View style={styles.dataRow}>
              <Text style={styles.label}>last_updated_at</Text>
              <Text style={styles.dataValue}>{formatDate(status.last_updated_at)}</Text>
            </View>
          </Animated.View>

          <Animated.View style={[styles.section, revealStyle(3)]}>
            <Text style={styles.sectionTitle}>Message</Text>
            <Text style={[styles.message, messageTone]}>{message || "(no message)"}</Text>
          </Animated.View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const uiFont = Platform.select({
  ios: "Avenir Next",
  android: "serif",
  default: "Georgia"
});

const titleFont = Platform.select({
  ios: "Avenir Next Condensed",
  android: "serif",
  default: "Trebuchet MS"
});

const monoFont = Platform.select({
  ios: "Menlo",
  android: "monospace",
  default: "monospace"
});

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#041227"
  },
  container: {
    flex: 1
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    overflow: "hidden"
  },
  backdropOrbA: {
    position: "absolute",
    top: -120,
    left: -80,
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: "rgba(95, 198, 255, 0.24)"
  },
  backdropOrbB: {
    position: "absolute",
    top: 180,
    right: -100,
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: "rgba(255, 170, 93, 0.16)"
  },
  backdropOrbC: {
    position: "absolute",
    bottom: -130,
    left: 40,
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: "rgba(157, 128, 255, 0.14)"
  },
  content: {
    width: "100%",
    maxWidth: 760,
    alignSelf: "center",
    paddingTop: Platform.OS === "android" ? 20 : 12,
    paddingHorizontal: 18,
    paddingBottom: 30,
    gap: 14
  },
  hero: {
    borderRadius: 24,
    padding: 20,
    gap: 10,
    backgroundColor: "rgba(8, 36, 73, 0.84)",
    borderWidth: 1,
    borderColor: "rgba(174, 222, 255, 0.34)",
    shadowColor: "#0c6ea7",
    shadowOpacity: 0.25,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 10 },
    elevation: 5
  },
  title: {
    color: "#fff3c8",
    fontSize: 34,
    letterSpacing: 0.6,
    fontFamily: titleFont,
    fontWeight: "700"
  },
  subtitle: {
    color: "#d8eaff",
    fontSize: 15,
    lineHeight: 22,
    fontFamily: uiFont
  },
  apiBadge: {
    marginTop: 6,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "rgba(2, 20, 43, 0.82)",
    borderWidth: 1,
    borderColor: "rgba(255, 223, 137, 0.35)",
    gap: 3
  },
  apiBadgeLabel: {
    color: "#8fcdf6",
    fontSize: 12,
    letterSpacing: 0.8,
    textTransform: "uppercase",
    fontFamily: uiFont
  },
  apiBadgeValue: {
    color: "#fff5d3",
    fontSize: 13,
    fontFamily: monoFont
  },
  section: {
    borderRadius: 20,
    padding: 16,
    gap: 10,
    backgroundColor: "rgba(8, 26, 54, 0.82)",
    borderWidth: 1,
    borderColor: "rgba(145, 200, 255, 0.24)",
    shadowColor: "#020b18",
    shadowOpacity: 0.28,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4
  },
  sectionHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  sectionTitle: {
    color: "#fff1c5",
    fontSize: 20,
    fontFamily: titleFont,
    fontWeight: "700"
  },
  sectionDescription: {
    color: "#bddaff",
    fontSize: 13,
    lineHeight: 19,
    fontFamily: uiFont
  },
  buttonBase: {
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    overflow: "hidden"
  },
  buttonPrimary: {
    backgroundColor: "#2a6fb5",
    borderColor: "#ffe79a"
  },
  buttonSecondary: {
    backgroundColor: "#174b85",
    borderColor: "#9fd0ff"
  },
  buttonPressed: {
    transform: [{ scale: 0.985 }]
  },
  buttonDisabled: {
    opacity: 0.58
  },
  buttonText: {
    textAlign: "center",
    fontSize: 15,
    fontWeight: "700",
    letterSpacing: 0.2,
    fontFamily: uiFont
  },
  buttonTextPrimary: {
    color: "#fff8df"
  },
  buttonTextSecondary: {
    color: "#deefff"
  },
  buttonShine: {
    position: "absolute",
    left: 0,
    top: -30,
    width: 70,
    height: 120,
    backgroundColor: "rgba(255, 255, 255, 0.15)"
  },
  label: {
    color: "#8bc4ef",
    fontSize: 12,
    letterSpacing: 0.7,
    textTransform: "uppercase",
    fontFamily: uiFont
  },
  mono: {
    color: "#f0f7ff",
    fontSize: 13,
    lineHeight: 20,
    fontFamily: monoFont
  },
  dataRow: {
    gap: 4
  },
  dataValue: {
    color: "#ecf6ff",
    fontSize: 14,
    lineHeight: 20,
    fontFamily: monoFont
  },
  message: {
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    lineHeight: 20,
    fontFamily: uiFont
  },
  messageNeutral: {
    color: "#ebf4ff",
    backgroundColor: "rgba(21, 53, 97, 0.7)",
    borderColor: "rgba(165, 208, 249, 0.3)"
  },
  messageError: {
    color: "#ffe5d1",
    backgroundColor: "rgba(111, 38, 37, 0.76)",
    borderColor: "rgba(255, 169, 154, 0.44)"
  }
});
