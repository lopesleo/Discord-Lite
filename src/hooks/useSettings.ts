import { useState, useEffect, useCallback } from "react";
import type { Language } from "../types/index";
import * as DiscordAPI from "../api/discord-api";

interface UseSettingsResult {
  notificationsEnabled: boolean;
  autoConnectEnabled: boolean;
  steamSyncEnabled: boolean;
  language: Language;
  userVolumes: Record<string, number>;
  isLoading: boolean;
  updateNotifications: (enabled: boolean) => Promise<void>;
  updateAutoConnect: (enabled: boolean) => Promise<void>;
  updateSteamSync: (enabled: boolean) => Promise<void>;
  updateLanguage: (lang: Language) => Promise<void>;
  updateUserVolume: (userId: string, volume: number) => Promise<void>;
}

export function useSettings(): UseSettingsResult {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoConnectEnabled, setAutoConnectEnabled] = useState(false);
  const [steamSyncEnabled, setSteamSyncEnabled] = useState(true);
  const [language, setLanguage] = useState<Language>("pt");
  const [userVolumes, setUserVolumes] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);

  // Load settings on mount
  useEffect(() => {
    const loadSettingsData = async () => {
      try {
        const result = await DiscordAPI.getSettings();
        if (result.success && result.settings) {
          setNotificationsEnabled(
            result.settings.notifications_enabled ?? true
          );
          setAutoConnectEnabled(result.settings.auto_connect ?? false);
          setSteamSyncEnabled(result.settings.game_sync_enabled ?? true);
          setLanguage(result.settings.language ?? "pt");
          setUserVolumes(result.settings.user_volumes ?? {});
        }
      } catch (e) {
        console.error("Error loading settings:", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadSettingsData();
  }, []);

  const updateNotifications = useCallback(async (enabled: boolean) => {
    setNotificationsEnabled(enabled);
    await DiscordAPI.saveSettings({ notifications_enabled: enabled });
  }, []);

  const updateAutoConnect = useCallback(async (enabled: boolean) => {
    setAutoConnectEnabled(enabled);
    await DiscordAPI.saveSettings({ auto_connect: enabled });
  }, []);

  const updateSteamSync = useCallback(async (enabled: boolean) => {
    setSteamSyncEnabled(enabled);
    await DiscordAPI.saveSettings({ game_sync_enabled: enabled });
  }, []);

  const updateLanguage = useCallback(async (lang: Language) => {
    setLanguage(lang);
    await DiscordAPI.saveSettings({ language: lang });
  }, []);

  const updateUserVolume = useCallback(
    async (userId: string, volume: number) => {
      await DiscordAPI.setUserVolume(userId, Math.round(volume));
      const newVolumes = { ...userVolumes, [userId]: volume };
      setUserVolumes(newVolumes);
      await DiscordAPI.saveSettings({ user_volumes: newVolumes });
    },
    [userVolumes]
  );

  return {
    notificationsEnabled,
    autoConnectEnabled,
    steamSyncEnabled,
    language,
    userVolumes,
    isLoading,
    updateNotifications,
    updateAutoConnect,
    updateSteamSync,
    updateLanguage,
    updateUserVolume,
  };
}
