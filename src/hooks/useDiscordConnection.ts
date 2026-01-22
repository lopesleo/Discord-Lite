import { useState, useEffect, useCallback } from "react";
import type { Language, Guild, VoiceStateResponse } from "../types/index";
import { translations } from "../i18n/translations";
import * as DiscordAPI from "../api/discord-api";

interface UseDiscordConnectionOptions {
  language: Language;
  autoConnectEnabled: boolean;
  onAuthSuccess?: (data: {
    username: string;
    voiceState: VoiceStateResponse | null;
    guilds: Guild[];
    selectedGuildId: string | null;
  }) => Promise<void>;
}

interface UseDiscordConnectionResult {
  discordInstalled: boolean;
  discordRunning: boolean;
  isAuthenticated: boolean;
  isConnecting: boolean;
  statusMessage: string;
  username: string;
  isLoading: boolean;
  isLaunching: boolean;
  handleConnect: () => Promise<void>;
  handleLaunchDiscord: () => Promise<void>;
  handleLogout: () => Promise<void>;
}

export function useDiscordConnection(
  options: UseDiscordConnectionOptions
): UseDiscordConnectionResult {
  const { language, autoConnectEnabled, onAuthSuccess } = options;

  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [username, setUsername] = useState("");

  // Discord status
  const [discordInstalled, setDiscordInstalled] = useState(true);
  const [discordRunning, setDiscordRunning] = useState(false);
  const [isLaunching, setIsLaunching] = useState(false);

  const t = useCallback(
    (key: keyof typeof translations.en): string =>
      translations[language][key] || key,
    [language]
  );

  const handleConnect = useCallback(async () => {
    setIsConnecting(true);
    setStatusMessage(translations[language].connecting);

    try {
      const result = await DiscordAPI.autoAuth();

      if (result.authenticated) {
        setIsAuthenticated(true);
        setUsername(result.user?.username || "");
        setStatusMessage(
          `${translations[language].connectedAs} ${result.user?.username || ""}`
        );

        // Load initial data
        const voice = await DiscordAPI.getVoiceState();
        const guildsRes = await DiscordAPI.getGuilds();

        if (onAuthSuccess) {
          await onAuthSuccess({
            username: result.user?.username || "",
            voiceState: voice.success ? voice : null,
            guilds: guildsRes.success ? guildsRes.guilds : [],
            selectedGuildId: guildsRes.selected_guild_id || null,
          });
        }
      } else {
        setStatusMessage(result.message);
      }
    } catch {
      setStatusMessage(translations[language].error);
    } finally {
      setIsConnecting(false);
    }
  }, [language, onAuthSuccess]);

  const handleLaunchDiscord = useCallback(async () => {
    setIsLaunching(true);
    try {
      const result = await DiscordAPI.launchDiscord();
      if (result.success) {
        setStatusMessage(t("launching"));
        setTimeout(async () => {
          const running = await DiscordAPI.checkDiscordRunning();
          setDiscordRunning(running.running || false);
          if (running.running) {
            setStatusMessage(t("openDiscord"));
          }
          setIsLaunching(false);
        }, 5000);
      } else {
        setStatusMessage(result.message || t("error"));
        setIsLaunching(false);
      }
    } catch {
      setStatusMessage(t("error"));
      setIsLaunching(false);
    }
  }, [t]);

  const handleLogout = useCallback(async () => {
    await DiscordAPI.logout();
    setIsAuthenticated(false);
    setUsername("");
    setStatusMessage(t("notConnected"));
  }, [t]);

  // ==================== INITIAL CHECK & POLLING ====================

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    const checkStatusLoop = async () => {
      try {
        // 1. Check if Discord is installed
        if (!discordInstalled) {
          const installed = await DiscordAPI.checkDiscordInstalled();
          setDiscordInstalled(installed.installed || false);
          if (!installed.installed) return;
        }

        // 2. Check if Discord is running
        const running = await DiscordAPI.checkDiscordRunning();
        const isRunning = running.running || false;
        setDiscordRunning(isRunning);

        // 3. Handle authentication status
        if (isRunning) {
          if (isAuthenticated) {
            // Already authenticated, just maintain status
          } else {
            // Check if there's an existing valid session
            const status = await DiscordAPI.checkStatus();
            if (status.authenticated) {
              setIsAuthenticated(true);
              setUsername(status.user?.username || "");
              setStatusMessage(
                `${t("connectedAs")} ${status.user?.username || ""}`
              );

              // Load initial data
              const voice = await DiscordAPI.getVoiceState();
              const guildsRes = await DiscordAPI.getGuilds();

              if (onAuthSuccess) {
                await onAuthSuccess({
                  username: status.user?.username || "",
                  voiceState: voice.success ? voice : null,
                  guilds: guildsRes.success ? guildsRes.guilds : [],
                  selectedGuildId: guildsRes.selected_guild_id || null,
                });
              }
            } else {
              // Not authenticated - check if we should auto-connect
              if (autoConnectEnabled && !isConnecting) {
                handleConnect();
              } else {
                setStatusMessage(t("connect"));
              }
            }
          }
        } else {
          setStatusMessage(t("discordNotRunning"));
        }
      } catch (e) {
        console.error("Check status loop error:", e);
      } finally {
        setIsLoading(false);
      }
    };

    // Run immediately on mount
    checkStatusLoop();

    // Poll while Discord is not running or not authenticated
    if (!discordRunning || !isAuthenticated) {
      intervalId = setInterval(checkStatusLoop, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [
    discordInstalled,
    discordRunning,
    isAuthenticated,
    autoConnectEnabled,
    isConnecting,
    language,
    handleConnect,
    onAuthSuccess,
    t,
  ]);

  return {
    discordInstalled,
    discordRunning,
    isAuthenticated,
    isConnecting,
    statusMessage,
    username,
    isLoading,
    isLaunching,
    handleConnect,
    handleLaunchDiscord,
    handleLogout,
  };
}
