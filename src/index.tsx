import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  SliderField,
  staticClasses,
  DropdownItem,
  ToggleField,
} from "@decky/ui";
import { definePlugin, toaster } from "@decky/api";
import { useState, useCallback, Fragment, useRef } from "react";

// Plugin version
const PLUGIN_VERSION = "1.4.0";

// Import types
import type {
  Language,
  TranslationKey,
} from "./types/index";

// Import translations
import { translations } from "./i18n/translations";

// Import API
import * as DiscordAPI from "./api/discord-api";

// Import styles
import { theme } from "./styles/theme";
import { styles } from "./styles/component-styles";

// Import hooks
import { useDiscordConnection } from "./hooks/useDiscordConnection";
import { useVoiceState } from "./hooks/useVoiceState";
import { useSettings } from "./hooks/useSettings";
import { useGuildsAndChannels } from "./hooks/useGuildsAndChannels";

// Import components
import { MemberItem, ChannelItem } from "./components";

// Main Content Component
function Content() {
  // UI State (not managed by hooks)
  const [expandedMember, setExpandedMember] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Settings Hook
  const settings = useSettings();
  const {
    language,
    notificationsEnabled,
    autoConnectEnabled,
    updateNotifications,
    updateAutoConnect,
    updateSteamSync,
    updateLanguage,
    updateUserVolume,
  } = settings;

  // Translation helper
  const t = useCallback(
    (key: TranslationKey): string => translations[language][key] || key,
    [language]
  );

  // Guilds and Channels Hook
  const guildsAndChannels = useGuildsAndChannels();
  const {
    guilds,
    selectedGuildId,
    channels,
    showChannelPicker,
    isLoadingChannels,
    isJoiningChannel,
    setGuilds,
    setSelectedGuildId,
    setShowChannelPicker,
    selectGuild: handleSelectGuild,
    loadChannels: handleLoadChannels,
    joinChannel,
  } = guildsAndChannels;

  // Discord Connection Hook
  const connection = useDiscordConnection({
    language,
    autoConnectEnabled,
    onAuthSuccess: async (data) => {
      if (data.voiceState) voiceControl.setVoiceState(data.voiceState);
      setGuilds(data.guilds);
      setSelectedGuildId(data.selectedGuildId);
    },
  });

  // Voice State Hook
  const voiceControl = useVoiceState({
    isAuthenticated: connection.isAuthenticated,
    syncCompleteText: t("syncComplete"),
    membersInChannelText: t("membersInChannel"),
  });

  // Refs
  const notificationsEnabledRef = useRef(notificationsEnabled);
  notificationsEnabledRef.current = notificationsEnabled;

  // Handlers
  const handleJoinChannel = useCallback(
    (channelId: string) => {
      joinChannel(channelId, (voice) => voiceControl.setVoiceState(voice));
    },
    [joinChannel, voiceControl]
  );

  const handleUserMuteToggle = useCallback(
    async (userId: string, muted: boolean) => {
      await DiscordAPI.muteUser(userId, muted);
    },
    []
  );

  const handleSync = useCallback(async () => {
    setIsSyncing(true);
    try {
      const fullState = await DiscordAPI.syncFullState();
      if (fullState.success) {
        voiceControl.setVoiceState(fullState);
        if (fullState.guilds) setGuilds(fullState.guilds);
        if (fullState.selected_guild_id) setSelectedGuildId(fullState.selected_guild_id);
        toaster.toast({
          title: `✅ ${t("syncComplete")}`,
          body: `${fullState.members?.length || 0} ${t("membersInChannel")}`,
          duration: 2000,
        });
      }
    } catch {
      console.error("Sync error");
    } finally {
      setIsSyncing(false);
    }
  }, [voiceControl, setGuilds, setSelectedGuildId, t]);

  // Render: Loading state
  if (connection.isLoading) {
    return (
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={{ ...styles.infoText, padding: "30px" }}>
            ⏳ {t("loading")}
          </div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Render: Discord not installed
  if (!connection.discordInstalled) {
    return (
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={styles.statusBadge(false)}>
            ❌ {t("discordNotInstalled")}
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={styles.infoText}>{t("installDiscord")}</div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Render: Discord not running
  if (!connection.discordRunning && !connection.isAuthenticated) {
    return (
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={styles.statusBadge(false)}>
            💤 {t("discordNotRunning")}
          </div>
        </PanelSectionRow>

        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={connection.handleLaunchDiscord}
            disabled={connection.isLaunching}
          >
            {connection.isLaunching ? `⏳ ${t("launching")}` : `🚀 ${t("launchDiscord")}`}
          </ButtonItem>
        </PanelSectionRow>

        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={connection.handleConnect}
            disabled={connection.isConnecting}
          >
            {connection.isConnecting ? `⏳ ${t("connecting")}` : `🔗 ${t("connect")}`}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Render: Not authenticated
  if (!connection.isAuthenticated) {
    return (
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={styles.statusBadge(false)}>🔌 {connection.statusMessage}</div>
        </PanelSectionRow>

        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={connection.handleConnect}
            disabled={connection.isConnecting}
          >
            {connection.isConnecting
              ? `⏳ ${t("connecting")}`
              : `🔗 ${t("connectToDiscord")}`}
          </ButtonItem>
        </PanelSectionRow>

        <PanelSectionRow>
          <div style={styles.infoText}>{t("authWindow")}</div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // Render: Authenticated (main UI)
  const { voiceState } = voiceControl;

  return (
    <Fragment>
      {/* Connection Status */}
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={styles.statusBadge(true)}>
            <span>✅</span>
            <span>{connection.username || t("connected")}</span>
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={handleSync}
            disabled={isSyncing}
          >
            {isSyncing ? "⏳ " : "🔄 "}{t("sync")}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      {/* Server & Voice Channel */}
      <PanelSection title={`🏠 ${t("server")} & 📢 ${t("voiceChannel")}`}>
        <PanelSectionRow>
          {guilds.length > 0 ? (
            <DropdownItem
              label={t("server")}
              rgOptions={guilds.map((guild) => ({
                label: guild.name,
                data: guild.id,
              }))}
              selectedOption={selectedGuildId || guilds[0]?.id}
              onChange={(option) => handleSelectGuild(option.data)}
            />
          ) : (
            <div style={styles.infoText}>{t("noServers")}</div>
          )}
        </PanelSectionRow>

        {voiceState?.in_voice && voiceState.channel_name && (
          <PanelSectionRow>
            <div style={styles.channelBadge}>
              <div style={styles.channelName}>
                <span>🔊</span>
                <span>{voiceState.channel_name}</span>
              </div>
            </div>
          </PanelSectionRow>
        )}
        {!showChannelPicker ? (
          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={() => handleLoadChannels(voiceState)}
              disabled={isLoadingChannels}
            >
              {isLoadingChannels ? "⏳ " : "🔊 "}{t("selectChannel")}
            </ButtonItem>
          </PanelSectionRow>
        ) : (
          <Fragment>
            {isLoadingChannels ? (
              <PanelSectionRow>
                <div style={styles.infoText}>⏳ {t("loading")}</div>
              </PanelSectionRow>
            ) : channels.length > 0 ? (
              <PanelSectionRow>
                <div
                  style={{
                    backgroundColor: theme.colors.background.secondary,
                    borderRadius: theme.borderRadius.md,
                    padding: theme.spacing.sm,
                    maxHeight: "200px",
                    overflowY: "auto" as const,
                  }}
                >
                  {channels.map((channel) => (
                    <ChannelItem
                      key={channel.id}
                      channel={channel}
                      selected={channel.id === voiceState?.channel_id}
                      onSelect={() => handleJoinChannel(channel.id)}
                      disabled={isJoiningChannel}
                    />
                  ))}
                </div>
              </PanelSectionRow>
            ) : (
              <PanelSectionRow>
                <div style={styles.infoText}>{t("noChannels")}</div>
              </PanelSectionRow>
            )}
            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={() => setShowChannelPicker(false)}
                disabled={isJoiningChannel}
              >
                ✖ {t("close")}
              </ButtonItem>
            </PanelSectionRow>
          </Fragment>
        )}

        {voiceState?.in_voice && (
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={voiceControl.leaveVoice}>
              📴 {t("leaveChannel")}
            </ButtonItem>
          </PanelSectionRow>
        )}
      </PanelSection>

      {/* Voice Controls - Only when in channel */}
      {voiceState?.in_voice && (
        <PanelSection title={`🎤 ${t("controls")}`}>
          <PanelSectionRow>
            <ToggleField
              label={`🎤 ${t("microphone")}`}
              description={voiceState?.is_muted ? t("muted") : t("micActive")}
              checked={!voiceState?.is_muted}
              onChange={() => voiceControl.toggleMute()}
              disabled={voiceState?.is_deafened}
            />
          </PanelSectionRow>

          <PanelSectionRow>
            <ToggleField
              label={`🔊 Audio`}
              description={voiceState?.is_deafened ? t("deafened") : t("audioActive")}
              checked={!voiceState?.is_deafened}
              onChange={voiceControl.toggleDeafen}
            />
          </PanelSectionRow>

          <PanelSectionRow>
            <SliderField
              label={`🎤 ${t("microphone")} ${t("volume")}`}
              value={voiceState?.input_volume ?? 100}
              min={0}
              max={100}
              step={5}
              onChange={voiceControl.setInputVolume}
              showValue
            />
          </PanelSectionRow>

          <PanelSectionRow>
            <SliderField
              label={`🔊 ${t("volume")}`}
              value={voiceState?.output_volume ?? 100}
              min={0}
              max={200}
              step={5}
              onChange={voiceControl.setOutputVolume}
              showValue
            />
          </PanelSectionRow>
        </PanelSection>
      )}

      {/* Members */}
      {voiceState?.in_voice &&
        voiceState.members &&
        voiceState.members.length > 0 && (
          <PanelSection
            title={`👥 ${t("members")} (${voiceState.members.length})`}
          >
            {voiceState.members.map((member) => (
              <MemberItem
                key={member.user_id}
                member={member}
                savedVolume={settings.userVolumes[member.user_id]}
                isSpeaking={voiceState.speaking_users?.includes(member.user_id)}
                onVolumeChange={updateUserVolume}
                onMuteToggle={handleUserMuteToggle}
                expanded={expandedMember === member.user_id}
                onToggleExpand={() =>
                  setExpandedMember(
                    expandedMember === member.user_id ? null : member.user_id,
                  )
                }
                t={t}
              />
            ))}
          </PanelSection>
        )}

      {/* Settings */}
      <PanelSection title={`⚙️ ${t("settings")}`}>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={() => setShowSettings(!showSettings)}
          >
            {showSettings ? `▲ ${t("hideSettings")}` : `▼ ${t("showSettings")}`}
          </ButtonItem>
        </PanelSectionRow>

        {showSettings && (
          <Fragment>
            <PanelSectionRow>
              <ToggleField
                label={t("notifications")}
                description={t("notificationsDesc")}
                checked={notificationsEnabled}
                onChange={updateNotifications}
              />
            </PanelSectionRow>

            <PanelSectionRow>
              <ToggleField
                label={t("autoConnect")}
                description={t("autoConnectDesc")}
                checked={autoConnectEnabled}
                onChange={updateAutoConnect}
              />
            </PanelSectionRow>

            <PanelSectionRow>
              <ToggleField
                label={t("steamSync")}
                description={t("steamSyncDesc")}
                checked={settings.steamSyncEnabled}
                onChange={updateSteamSync}
              />
            </PanelSectionRow>

            <PanelSectionRow>
              <DropdownItem
                label={t("language")}
                rgOptions={[
                  { label: "Português", data: "pt" },
                  { label: "English", data: "en" },
                ]}
                selectedOption={language}
                onChange={(opt) => updateLanguage(opt.data as Language)}
              />
            </PanelSectionRow>

            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={connection.handleLogout}
              >
                🚪 {t("disconnect")}
              </ButtonItem>
            </PanelSectionRow>
          </Fragment>
        )}
      </PanelSection>
    </Fragment>
  );
}

// Plugin Export & Event Polling

let eventPollingInterval: ReturnType<typeof setInterval> | null = null;
let notificationsEnabled = true;
let currentLanguage: Language = "pt";

const startEventPolling = () => {
  if (eventPollingInterval) return;

  const pollEvents = async () => {
    try {
      const settings = await DiscordAPI.getSettings();
      notificationsEnabled = settings.settings?.notifications_enabled ?? true;
      currentLanguage = settings.settings?.language ?? "pt";

      if (!notificationsEnabled) return;

      const result = await DiscordAPI.getPendingEvents();
      if (result.success && result.events.length > 0) {
        const t = translations[currentLanguage];

        for (const event of result.events) {
          if (event.type === "VOICE_JOIN" && event.username) {
            const avatarUrl =
              event.avatar && event.user_id
                ? `https://cdn.discordapp.com/avatars/${event.user_id}/${event.avatar}.png?size=64`
                : `https://cdn.discordapp.com/embed/avatars/${parseInt(event.user_id || "0") % 5}.png`;

            toaster.toast({
              title: `🎤 ${event.username}`,
              body: `${t.joined} ${t.theCall}`,
              logo: (
                <img
                  src={avatarUrl}
                  style={{ width: 40, height: 40, borderRadius: "50%" }}
                />
              ),
              duration: 4000,
            });
          } else if (event.type === "VOICE_LEAVE" && event.username) {
            const avatarUrl =
              event.avatar && event.user_id
                ? `https://cdn.discordapp.com/avatars/${event.user_id}/${event.avatar}.png?size=64`
                : `https://cdn.discordapp.com/embed/avatars/${parseInt(event.user_id || "0") % 5}.png`;

            toaster.toast({
              title: `👋 ${event.username}`,
              body: `${t.left} ${t.theCall}`,
              logo: (
                <img
                  src={avatarUrl}
                  style={{ width: 40, height: 40, borderRadius: "50%" }}
                />
              ),
              duration: 4000,
            });
          }
        }
      }
    } catch (e) {
      console.error("Discord Lite: Event polling error:", e);
    }
  };

  eventPollingInterval = setInterval(pollEvents, 3000);
  pollEvents();
  console.log("Discord Lite: Event polling started");
};

const stopEventPolling = () => {
  if (eventPollingInterval) {
    clearInterval(eventPollingInterval);
    eventPollingInterval = null;
    console.log("Discord Lite: Event polling stopped");
  }
};

export default definePlugin(() => {
  console.log("Discord Lite: Plugin loaded");
  startEventPolling();

  return {
    name: "Discord Lite",
    titleView: <div className={staticClasses.Title}>Discord Lite v{PLUGIN_VERSION}</div>,
    content: <Content />,
    icon: (
      <svg width="1em" height="1em" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.947 2.418-2.157 2.418z" />
      </svg>
    ),
    onDismount() {
      stopEventPolling();
      console.log("Discord Lite: Plugin unloaded");
    },
  };
});
