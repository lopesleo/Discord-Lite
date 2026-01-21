import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  SliderField,
  staticClasses,
  Focusable,
  DropdownItem,
  ToggleField,
} from "@decky/ui";
import { callable, definePlugin, toaster } from "@decky/api";
import { useState, useEffect, useCallback, Fragment, useRef } from "react";

// ==================== TRANSLATIONS ====================

const translations = {
  en: {
    // General
    loading: "Loading...",
    sync: "SYNC",
    disconnect: "DISCONNECT",
    connect: "CONNECT",
    connecting: "Connecting...",
    connected: "Connected",
    connectedAs: "Connected as",
    notConnected: "Not connected",
    error: "Error",
    success: "Success",

    // Discord status
    discordNotInstalled: "Discord not installed",
    installDiscord:
      "Install Discord via Discover (Flatpak) to use this plugin.",
    discordNotRunning: "Discord is not running",
    launchDiscord: "LAUNCH DISCORD",
    launching: "Launching...",
    openDiscord: "Discord open! Click to connect",
    connectToDiscord: "CONNECT TO DISCORD",
    authWindow: "A window will appear in Discord to authorize",

    // Voice controls
    controls: "Controls",
    muted: "MUTED",
    micActive: "MIC ACTIVE",
    deafened: "DEAFENED",
    audioActive: "AUDIO ACTIVE",
    microphone: "Microphone",
    volume: "Volume",

    // Server & Channel
    server: "Server",
    changeServer: "CHANGE SERVER",
    noServers: "No servers found",
    close: "CLOSE",
    voiceChannel: "Voice Channel",
    selectChannel: "SELECT CHANNEL",
    noChannels: "No voice channels",
    leaveChannel: "LEAVE CHANNEL",

    // Members
    members: "Members",
    userVolume: "Volume",
    unmuteUser: "Unmute user",
    muteUser: "Mute user",

    // Settings
    settings: "Settings",
    showSettings: "SHOW",
    hideSettings: "HIDE",
    notifications: "Notifications",
    notificationsDesc: "Show toasts when members join/leave",
    autoConnect: "Auto-connect",
    autoConnectDesc: "Connect automatically when Discord is open",
    language: "Language",
    steamSync: "Steam Game Sync",
    steamSyncDesc: "Show current game in Discord status",

    // Call time
    inCall: "In call",
    callTime: "Call time",

    // Toasts
    joined: "joined",
    left: "left",
    theCall: "the call",
    syncComplete: "Synced",
    membersInChannel: "members in channel",
  },
  pt: {
    // General
    loading: "Carregando...",
    sync: "SINCRONIZAR",
    disconnect: "DESCONECTAR",
    connect: "CONECTAR",
    connecting: "Conectando...",
    connected: "Conectado",
    connectedAs: "Conectado como",
    notConnected: "Não conectado",
    error: "Erro",
    success: "Sucesso",

    // Discord status
    discordNotInstalled: "Discord não instalado",
    installDiscord:
      "Instale o Discord pelo Discover (Flatpak) para usar este plugin.",
    discordNotRunning: "Discord não está aberto",
    launchDiscord: "ABRIR DISCORD",
    launching: "Iniciando...",
    openDiscord: "Discord aberto! Clique para conectar",
    connectToDiscord: "CONECTAR AO DISCORD",
    authWindow: "Uma janela aparecerá no Discord para autorizar",

    // Voice controls
    controls: "Controles",
    muted: "MUTADO",
    micActive: "MICROFONE ATIVO",
    deafened: "SURDO",
    audioActive: "ÁUDIO ATIVO",
    microphone: "Microfone",
    volume: "Volume",

    // Server & Channel
    server: "Servidor",
    changeServer: "TROCAR SERVIDOR",
    noServers: "Nenhum servidor encontrado",
    close: "FECHAR",
    voiceChannel: "Canal de Voz",
    selectChannel: "ESCOLHER CANAL",
    noChannels: "Nenhum canal de voz",
    leaveChannel: "SAIR DO CANAL",

    // Members
    members: "Membros",
    userVolume: "Volume",
    unmuteUser: "Desmutar usuário",
    muteUser: "Mutar usuário",

    // Settings
    settings: "Configurações",
    showSettings: "MOSTRAR",
    hideSettings: "OCULTAR",
    notifications: "Notificações",
    notificationsDesc: "Mostrar toasts quando membros entram/saem",
    autoConnect: "Auto-conectar",
    autoConnectDesc: "Conectar automaticamente quando Discord estiver aberto",
    language: "Idioma",
    steamSync: "Sincronizar Jogo Steam",
    steamSyncDesc: "Mostrar jogo atual no status do Discord",

    // Call time
    inCall: "Na call",
    callTime: "Tempo na call",

    // Toasts
    joined: "entrou",
    left: "saiu",
    theCall: "da call",
    syncComplete: "Sincronizado",
    membersInChannel: "membros no canal",
  },
};

type Language = "en" | "pt";
type TranslationKey = keyof (typeof translations)["en"];

// ==================== INTERFACES ====================

interface AutoAuthResponse {
  success: boolean;
  authenticated: boolean;
  user?: { username?: string; id?: string };
  message: string;
}

interface VoiceMember {
  user_id: string;
  username: string;
  avatar?: string;
  mute: boolean;
  deaf: boolean;
  volume: number;
}

interface VoiceChannel {
  id: string;
  name: string;
  type: number;
}

interface Guild {
  id: string;
  name: string;
  icon_url?: string;
}

interface VoiceStateResponse {
  success: boolean;
  authenticated?: boolean;
  is_muted?: boolean;
  is_deafened?: boolean;
  input_volume?: number;
  output_volume?: number;
  channel_id?: string | null;
  channel_name?: string | null;
  guild_id?: string | null;
  in_voice?: boolean;
  members?: VoiceMember[];
  speaking_users?: string[];
  message?: string;
}

interface ActionResponse {
  success: boolean;
  is_muted?: boolean;
  is_deafened?: boolean;
  volume?: number;
  message?: string;
}

interface ChannelsResponse {
  success: boolean;
  guild_id?: string;
  channels: VoiceChannel[];
  message?: string;
}

interface GuildsResponse {
  success: boolean;
  guilds: Guild[];
  selected_guild_id?: string;
  message?: string;
}

interface DiscordStatusResponse {
  success: boolean;
  installed?: boolean;
  running?: boolean;
  flatpak?: boolean;
  native?: boolean;
  message?: string;
}

interface SettingsResponse {
  success: boolean;
  settings: {
    notifications_enabled?: boolean;
    auto_connect?: boolean;
    game_sync_enabled?: boolean;
    language?: Language;
    user_volumes?: Record<string, number>;
  };
}

interface VoiceEvent {
  type: "VOICE_JOIN" | "VOICE_LEAVE";
  user_id?: string;
  username?: string;
  avatar?: string;
}

// ==================== CALLABLE FUNCTIONS ====================

const autoAuth = callable<[], AutoAuthResponse>("auto_auth");
const checkStatus = callable<[], AutoAuthResponse>("check_status");
const logout = callable<[], ActionResponse>("logout");
const getVoiceState = callable<[], VoiceStateResponse>("get_voice_state");
const toggleMute = callable<[], ActionResponse>("toggle_mute");
const toggleDeafen = callable<[], ActionResponse>("toggle_deafen");
const setInputVolume = callable<[number], ActionResponse>("set_input_volume");
const setOutputVolume = callable<[number], ActionResponse>("set_output_volume");
const leaveVoice = callable<[], ActionResponse>("leave_voice");
const getVoiceChannels = callable<[string?], ChannelsResponse>(
  "get_voice_channels",
);
const joinVoiceChannel = callable<[string], ActionResponse>(
  "join_voice_channel",
);
const setUserVolume = callable<[string, number], ActionResponse>(
  "set_user_volume",
);
const muteUser = callable<[string, boolean], ActionResponse>("mute_user");
const getGuilds = callable<[], GuildsResponse>("get_guilds");
const selectGuild = callable<[string], ActionResponse>("select_guild");
const checkDiscordInstalled = callable<[], DiscordStatusResponse>(
  "check_discord_installed",
);
const launchDiscord = callable<[], ActionResponse>("launch_discord");
const checkDiscordRunning = callable<[], DiscordStatusResponse>(
  "check_discord_running",
);
const syncFullState = callable<
  [],
  VoiceStateResponse & {
    guilds?: Guild[];
    selected_guild_id?: string;
    is_camera_on?: boolean;
    is_screen_sharing?: boolean;
  }
>("sync_full_state");
const getPendingEvents = callable<
  [],
  { success: boolean; events: VoiceEvent[] }
>("get_pending_events");
const getSettings = callable<[], SettingsResponse>("get_settings");
const saveSettings = callable<[Record<string, unknown>], ActionResponse>(
  "save_settings_async",
);

// ==================== HELPER FUNCTIONS ====================

const formatTime = (seconds: number): string => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

// ==================== STYLES ====================

const theme = {
  colors: {
    primary: "#5865F2",
    primaryHover: "#4752C4",
    success: "#3BA55C",
    danger: "#ED4245",
    warning: "#FAA61A",
    background: {
      primary: "rgba(30, 31, 34, 0.95)",
      secondary: "rgba(43, 45, 49, 0.9)",
      tertiary: "rgba(54, 57, 63, 0.8)",
      hover: "rgba(79, 84, 92, 0.4)",
    },
    text: {
      primary: "#FFFFFF",
      secondary: "#B9BBBE",
      muted: "#72767D",
    },
    border: "rgba(255, 255, 255, 0.06)",
  },
  borderRadius: {
    sm: "4px",
    md: "8px",
    lg: "12px",
    full: "50%",
  },
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "20px",
  },
};

const styles = {
  // Status Badge
  statusBadge: (connected: boolean) => ({
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    backgroundColor: connected
      ? "rgba(59, 165, 92, 0.15)"
      : "rgba(88, 101, 242, 0.15)",
    borderRadius: theme.borderRadius.lg,
    fontSize: "14px",
    fontWeight: 600,
    color: connected ? theme.colors.success : theme.colors.primary,
    border: connected
      ? `1px solid rgba(59, 165, 92, 0.3)`
      : `1px solid rgba(88, 101, 242, 0.3)`,
  }),

  // Channel Info Badge
  channelBadge: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    backgroundColor: "rgba(88, 101, 242, 0.1)",
    borderRadius: theme.borderRadius.md,
    marginTop: theme.spacing.sm,
    border: `1px solid rgba(88, 101, 242, 0.2)`,
  },

  channelName: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    color: theme.colors.primary,
    fontSize: "13px",
    fontWeight: 500,
  },

  callTime: {
    fontSize: "12px",
    color: theme.colors.text.muted,
    fontFamily: "monospace",
  },

  // Control Buttons
  controlButton: (
    active: boolean,
    focused: boolean = false,
    disabled: boolean = false,
  ) => ({
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    backgroundColor: disabled
      ? "rgba(128, 128, 128, 0.1)"
      : active
        ? "rgba(59, 165, 92, 0.2)"
        : theme.colors.background.tertiary,
    borderRadius: theme.borderRadius.md,
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "all 0.15s ease",
    border: focused
      ? `2px solid ${theme.colors.primary}`
      : active
        ? `2px solid ${theme.colors.success}`
        : `2px solid ${theme.colors.border}`,
    boxShadow: focused ? `0 0 8px rgba(88, 101, 242, 0.5)` : "none",
    opacity: disabled ? 0.5 : 1,
  }),

  // Member Items
  memberItem: {
    backgroundColor: theme.colors.background.tertiary,
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing.xs,
    border: `1px solid transparent`,
    transition: "all 0.15s ease",
  },

  memberItemFocused: {
    backgroundColor: "rgba(88, 101, 242, 0.15)",
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing.xs,
    overflow: "hidden",
    border: `1px solid ${theme.colors.primary}`,
    boxShadow: `0 0 12px rgba(88, 101, 242, 0.25)`,
  },

  memberHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: theme.spacing.md,
    cursor: "pointer",
    borderRadius: theme.borderRadius.md,
    border: "2px solid transparent", // Borda invisível por padrão para não pular layout
    transition: "all 0.2s ease",
  },

  memberHeaderFocused: {
    backgroundColor: "rgba(255, 255, 255, 0.1)", // Um brilho de fundo
    border: "2px solid white", // A borda branca clássica do Steam Deck
  },

  memberAvatar: {
    width: "36px",
    height: "36px",
    borderRadius: theme.borderRadius.full,
    backgroundColor: theme.colors.background.hover,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
    fontWeight: 600,
    marginRight: theme.spacing.md,
    color: theme.colors.text.primary,
    border: `2px solid ${theme.colors.border}`,
  },

  memberInfo: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "2px",
  },

  memberName: {
    fontSize: "14px",
    fontWeight: 500,
    color: theme.colors.text.primary,
  },

  memberStatus: {
    fontSize: "12px",
    color: theme.colors.text.muted,
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.xs,
  },

  memberControls: {
    padding: theme.spacing.md,
    paddingTop: theme.spacing.sm,
    borderTop: `1px solid ${theme.colors.border}`,
    backgroundColor: "rgba(0, 0, 0, 0.2)",
  },

  // Info Text
  infoText: {
    fontSize: "12px",
    color: theme.colors.text.muted,
    textAlign: "center" as const,
    padding: theme.spacing.md,
  },

  // Server List (vertical scroll)
  serverList: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "4px",
    maxHeight: "200px",
    overflowY: "auto" as const,
    padding: theme.spacing.xs,
    backgroundColor: theme.colors.background.secondary,
    borderRadius: theme.borderRadius.md,
  },

  serverItem: (selected: boolean, focused: boolean) => ({
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    backgroundColor: selected
      ? "rgba(88, 101, 242, 0.25)"
      : focused
        ? "rgba(88, 101, 242, 0.15)"
        : "transparent",
    borderRadius: theme.borderRadius.md,
    cursor: "pointer",
    transition: "all 0.15s ease",
    border: focused
      ? `2px solid ${theme.colors.primary}`
      : selected
        ? `2px solid rgba(88, 101, 242, 0.5)`
        : `2px solid transparent`,
    boxShadow: focused ? `0 0 8px rgba(88, 101, 242, 0.4)` : "none",
    minHeight: "44px",
  }),

  serverIcon: {
    width: "32px",
    height: "32px",
    borderRadius: theme.borderRadius.sm,
    backgroundColor: theme.colors.background.hover,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
    fontWeight: 600,
    color: theme.colors.text.primary,
    flexShrink: 0,
    objectFit: "cover" as const,
  },

  serverName: {
    fontSize: "13px",
    color: theme.colors.text.primary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
    flex: 1,
  },

  // Channel List
  channelItem: (selected: boolean, focused: boolean) => ({
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    backgroundColor: selected
      ? "rgba(88, 101, 242, 0.25)"
      : focused
        ? "rgba(88, 101, 242, 0.15)"
        : "transparent",
    borderRadius: theme.borderRadius.md,
    cursor: "pointer",
    transition: "all 0.15s ease",
    border: focused
      ? `2px solid ${theme.colors.primary}`
      : selected
        ? `2px solid rgba(88, 101, 242, 0.5)`
        : `2px solid transparent`,
    boxShadow: focused ? `0 0 8px rgba(88, 101, 242, 0.4)` : "none",
    marginBottom: "2px",
  }),

  channelIcon: (focused: boolean) => ({
    fontSize: "14px",
    color: focused ? theme.colors.primary : theme.colors.text.muted,
  }),

  channelText: (selected: boolean, focused: boolean) => ({
    fontSize: "13px",
    color:
      focused || selected ? theme.colors.primary : theme.colors.text.secondary,
    fontWeight: focused || selected ? 500 : 400,
  }),

  // Speaking indicator
  speakingRing: {
    boxShadow: `0 0 0 3px ${theme.colors.success}, 0 0 12px ${theme.colors.success}`,
  },

  speakingBadge: {
    position: "absolute" as const,
    bottom: "-2px",
    right: "-2px",
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    backgroundColor: theme.colors.success,
    border: `2px solid ${theme.colors.background.primary}`,
  },
};

// ==================== MEMBER COMPONENT ====================

interface MemberItemProps {
  member: VoiceMember;
  savedVolume?: number;
  isSpeaking?: boolean;
  onVolumeChange: (userId: string, volume: number) => void;
  onMuteToggle: (userId: string, muted: boolean) => void;
  expanded: boolean;
  onToggleExpand: () => void;
  t: (key: TranslationKey) => string;
}

function MemberItem({
  member,
  savedVolume,
  isSpeaking,
  onVolumeChange,
  onMuteToggle,
  expanded,
  onToggleExpand,
  t,
}: MemberItemProps) {
  const [localVolume, setLocalVolume] = useState(
    savedVolume ?? member.volume ?? 100,
  );
  const [isMuted, setIsMuted] = useState(member.mute);

  // NOVO: Estado de foco visual APENAS para o cabeçalho
  const [headerFocused, setHeaderFocused] = useState(false);

  // Sincronização com o Backend
  useEffect(() => {
    setLocalVolume(savedVolume ?? member.volume ?? 100);
  }, [savedVolume, member.volume]);

  useEffect(() => {
    setIsMuted(member.mute);
  }, [member.mute]);

  const handleVolumeChange = useCallback(
    (value: number) => {
      setLocalVolume(value);
      onVolumeChange(member.user_id, value);
    },
    [member.user_id, onVolumeChange],
  );

  const handleMuteToggle = useCallback(() => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    onMuteToggle(member.user_id, newMuted);
  }, [member.user_id, isMuted, onMuteToggle]);

  const avatarUrl = member.avatar
    ? `https://cdn.discordapp.com/avatars/${member.user_id}/${member.avatar}.png?size=64`
    : null;

  const getStatusIcon = () => {
    if (isSpeaking) return "🗣️";
    if (member.deaf) return "🔇";
    if (member.mute) return "🎤❌";
    return "🎤";
  };

  const avatarStyle = {
    ...styles.memberAvatar,
    objectFit: "cover" as const,
    ...(isSpeaking ? styles.speakingRing : {}),
  };

  return (
    <div style={styles.memberItem}>
      <Focusable
        onActivate={onToggleExpand}
        onFocus={() => setHeaderFocused(true)}
        onBlur={() => setHeaderFocused(false)}
        style={{
          ...styles.memberHeader,
          ...(headerFocused ? styles.memberHeaderFocused : {}),
        }}
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{ position: "relative" as const }}>
            {avatarUrl ? (
              <img src={avatarUrl} alt={member.username} style={avatarStyle} />
            ) : (
              <div style={avatarStyle}>
                {member.username.charAt(0).toUpperCase()}
              </div>
            )}
            {isSpeaking && <div style={styles.speakingBadge} />}
          </div>
          <div style={{ ...styles.memberInfo, marginLeft: theme.spacing.md }}>
            <span style={styles.memberName}>{member.username}</span>
            <span style={styles.memberStatus}>
              {getStatusIcon()} {localVolume}%
            </span>
          </div>
        </div>
        <span style={{ color: theme.colors.text.muted }}>
          {expanded ? "▲" : "▼"}
        </span>
      </Focusable>

      {expanded && (
        <div style={styles.memberControls}>
          <SliderField
            label={`${t("userVolume")}: ${localVolume}%`}
            value={localVolume}
            min={0}
            max={200}
            step={5}
            onChange={handleVolumeChange}
            showValue={false}
          />

          <div style={{ marginTop: theme.spacing.sm }}>
            <ButtonItem layout="below" onClick={handleMuteToggle}>
              {isMuted ? `🔊 ${t("unmuteUser")}` : `🔇 ${t("muteUser")}`}
            </ButtonItem>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== SERVER ITEM COMPONENT ====================

interface ServerItemProps {
  guild: Guild;
  selected: boolean;
  onSelect: () => void;
}

function ServerItem({ guild, selected, onSelect }: ServerItemProps) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <Focusable
      style={styles.serverItem(selected, isFocused)}
      onActivate={onSelect}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
    >
      {guild.icon_url ? (
        <img src={guild.icon_url} alt={guild.name} style={styles.serverIcon} />
      ) : (
        <div style={styles.serverIcon}>
          {guild.name.charAt(0).toUpperCase()}
        </div>
      )}
      <span style={styles.serverName}>{guild.name}</span>
      {selected && <span style={{ color: theme.colors.success }}>✓</span>}
    </Focusable>
  );
}

// ==================== CHANNEL ITEM COMPONENT ====================

interface ChannelItemProps {
  channel: VoiceChannel;
  selected: boolean;
  onSelect: () => void;
}

function ChannelItem({ channel, selected, onSelect }: ChannelItemProps) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <Focusable
      style={styles.channelItem(selected, isFocused)}
      onActivate={onSelect}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
    >
      <span style={styles.channelIcon(isFocused)}>🔊</span>
      <span style={styles.channelText(selected, isFocused)}>
        {channel.name}
      </span>
      {isFocused && (
        <span style={{ marginLeft: "auto", color: theme.colors.primary }}>
          →
        </span>
      )}
    </Focusable>
  );
}

// ==================== MAIN COMPONENT ====================
let globalCallStartTime: number | null = null;
function Content() {
  // Language
  const [language, setLanguage] = useState<Language>("pt");
  const t = useCallback(
    (key: TranslationKey): string => translations[language][key] || key,
    [language],
  );

  // Settings
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoConnectEnabled, setAutoConnectEnabled] = useState(false);
  const [steamSyncEnabled, setSteamSyncEnabled] = useState(true);
  const [userVolumes, setUserVolumes] = useState<Record<string, number>>({});

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

  // Voice state
  const [voiceState, setVoiceState] = useState<VoiceStateResponse | null>(null);
  const [expandedMember, setExpandedMember] = useState<string | null>(null);

  // Focus states for control buttons
  const [muteFocused, setMuteFocused] = useState(false);
  const [deafenFocused, setDeafenFocused] = useState(false);

  // Call timer
  const [callDuration, setCallDuration] = useState(0);

  // Servers & Channels
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null);
  const [channels, setChannels] = useState<VoiceChannel[]>([]);
  const [showGuildPicker, setShowGuildPicker] = useState(false);
  const [showChannelPicker, setShowChannelPicker] = useState(false);

  // Settings panel
  const [showSettings, setShowSettings] = useState(false);

  // Refs
  const notificationsEnabledRef = useRef(notificationsEnabled);
  notificationsEnabledRef.current = notificationsEnabled;

  // ==================== LOAD SETTINGS ====================

  useEffect(() => {
    const loadSettingsData = async () => {
      try {
        const result = await getSettings();
        if (result.success && result.settings) {
          setNotificationsEnabled(
            result.settings.notifications_enabled ?? true,
          );
          setAutoConnectEnabled(result.settings.auto_connect ?? false);
          setSteamSyncEnabled(result.settings.game_sync_enabled ?? true);
          setLanguage(result.settings.language ?? "pt");
          setUserVolumes(result.settings.user_volumes ?? {});
        }
      } catch (e) {
        console.error("Error loading settings:", e);
      }
    };
    loadSettingsData();
  }, []);

  // ==================== CALL TIMER (CORRIGIDO) ====================

  useEffect(() => {
    if (voiceState?.in_voice) {
      if (!globalCallStartTime) {
        globalCallStartTime = Date.now();
      }
    } else {
      globalCallStartTime = null;
      setCallDuration(0);
    }
  }, [voiceState?.in_voice]);

  useEffect(() => {
    if (!voiceState?.in_voice || !globalCallStartTime) return;

    const updateTime = () => {
      if (globalCallStartTime) {
        setCallDuration(Math.floor((Date.now() - globalCallStartTime) / 1000));
      }
    };

    updateTime();

    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, [voiceState?.in_voice]);

  // ==================== HANDLERS ====================

  const handleConnect = useCallback(async () => {
    setIsConnecting(true);
    setStatusMessage(translations[language].connecting);

    try {
      const result = await autoAuth();

      if (result.authenticated) {
        setIsAuthenticated(true);
        setUsername(result.user?.username || "");
        setStatusMessage(
          `${translations[language].connectedAs} ${result.user?.username || ""}`,
        );

        const voice = await getVoiceState();
        if (voice.success) setVoiceState(voice);

        const guildsRes = await getGuilds();
        if (guildsRes.success) {
          setGuilds(guildsRes.guilds);
          setSelectedGuildId(guildsRes.selected_guild_id || null);
        }
      } else {
        setStatusMessage(result.message);
      }
    } catch {
      setStatusMessage(translations[language].error);
    } finally {
      setIsConnecting(false);
    }
  }, [language]);

  // ==================== INITIAL CHECK & POLLING ====================

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    const checkStatusLoop = async () => {
      try {
        // 1. Verifica se está instalado (só precisa confirmar uma vez se for true)
        if (!discordInstalled) {
          const installed = await checkDiscordInstalled();
          setDiscordInstalled(installed.installed || false);
          // Se não estiver instalado, nem continua
          if (!installed.installed) return;
        }

        // 2. Verifica se está rodando
        const running = await checkDiscordRunning();
        const isRunning = running.running || false;
        setDiscordRunning(isRunning);

        // 3. Se estiver rodando, tenta pegar o status da autenticação
        if (isRunning) {
          // Se já estamos autenticados, apenas atualiza o status
          if (isAuthenticated) {
            // Opcional: Atualizar info do usuário se necessário
          } else {
            // Se não estamos autenticados, verifica se já existe uma sessão válida
            const status = await checkStatus();
            if (status.authenticated) {
              setIsAuthenticated(true);
              setUsername(status.user?.username || "");
              setStatusMessage(
                `${t("connectedAs")} ${status.user?.username || ""}`,
              );

              // Carrega dados iniciais
              const voice = await getVoiceState();
              if (voice.success) setVoiceState(voice);
              const guildsRes = await getGuilds();
              if (guildsRes.success) {
                setGuilds(guildsRes.guilds);
                setSelectedGuildId(guildsRes.selected_guild_id || null);
              }
            } else {
              // Se não está autenticado, verifica se devemos auto-conectar
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

    // Roda imediatamente ao abrir
    checkStatusLoop();

    // Isso faz o menu "descongelar" assim que você abrir o Discord.
    if (!discordRunning || !isAuthenticated) {
      intervalId = setInterval(checkStatusLoop, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [
    language,
    discordInstalled,
    discordRunning,
    isAuthenticated,
    autoConnectEnabled,
  ]);

  // ==================== VOICE STATE SYNC ====================

  useEffect(() => {
    if (!isAuthenticated) return;

    const syncVoiceState = async () => {
      try {
        const voice = await getVoiceState();
        if (voice.success) setVoiceState(voice);
      } catch (e) {
        console.error("Error syncing voice state:", e);
      }
    };

    const intervalId = setInterval(syncVoiceState, 5000);
    return () => clearInterval(intervalId);
  }, [isAuthenticated]);

  // ==================== HANDLERS ====================

  const handleLaunchDiscord = async () => {
    setIsLaunching(true);
    try {
      const result = await launchDiscord();
      if (result.success) {
        setStatusMessage(t("launching"));
        setTimeout(async () => {
          const running = await checkDiscordRunning();
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
  };

  const handleLogout = async () => {
    await logout();
    setIsAuthenticated(false);
    setVoiceState(null);
    setGuilds([]);
    setChannels([]);
    setUsername("");
    setStatusMessage(t("notConnected"));
  };

  const handleSync = async () => {
    try {
      const fullState = await syncFullState();
      if (fullState.success) {
        setVoiceState(fullState);
        if (fullState.guilds) setGuilds(fullState.guilds);
        if (fullState.selected_guild_id)
          setSelectedGuildId(fullState.selected_guild_id);
        toaster.toast({
          title: `✅ ${t("syncComplete")}`,
          body: `${fullState.members?.length || 0} ${t("membersInChannel")}`,
          duration: 2000,
        });
      }
    } catch {
      console.error("Sync error");
    }
  };

  const handleToggleMute = async () => {
    const result = await toggleMute();
    if (result.success) {
      setVoiceState((prev) =>
        prev ? { ...prev, is_muted: result.is_muted } : null,
      );
    }
  };

  const handleToggleDeafen = async () => {
    const result = await toggleDeafen();
    if (result.success) {
      setVoiceState((prev) =>
        prev
          ? {
              ...prev,
              is_deafened: result.is_deafened,
              is_muted: result.is_muted,
            }
          : null,
      );
    }
  };

  const handleLeaveVoice = async () => {
    const result = await leaveVoice();
    if (result.success) {
      setVoiceState((prev) =>
        prev
          ? { ...prev, in_voice: false, channel_name: null, members: [] }
          : null,
      );
    }
  };

  const handleInputVolume = async (value: number) => {
    const result = await setInputVolume(Math.round(value));
    if (result.success) {
      // Usar o volume retornado pelo backend (que foi verificado)
      setVoiceState((prev) =>
        prev ? { ...prev, input_volume: result.volume ?? value } : null,
      );
    } else {
      // Reverter para o valor anterior se falhou
      console.error("Falha ao definir volume de entrada:", result.message);
    }
  };

  const handleOutputVolume = async (value: number) => {
    const result = await setOutputVolume(Math.round(value));
    if (result.success) {
      // Usar o volume retornado pelo backend (que foi verificado)
      setVoiceState((prev) =>
        prev ? { ...prev, output_volume: result.volume ?? value } : null,
      );
    } else {
      // Reverter para o valor anterior se falhou
      console.error("Falha ao definir volume de saída:", result.message);
    }
  };

  const handleSelectGuild = async (guildId: string) => {
    await selectGuild(guildId);
    setSelectedGuildId(guildId);
    setShowGuildPicker(false);

    const channelsRes = await getVoiceChannels(guildId);
    if (channelsRes.success) {
      setChannels(channelsRes.channels);
      setShowChannelPicker(true);
    }
  };

  const handleLoadChannels = async () => {
    const guildId = selectedGuildId || voiceState?.guild_id || undefined;
    const result = await getVoiceChannels(guildId);
    if (result.success) {
      setChannels(result.channels);
      setShowChannelPicker(true);
    }
  };

  const handleJoinChannel = async (channelId: string) => {
    const result = await joinVoiceChannel(channelId);
    if (result.success) {
      setShowChannelPicker(false);
      const voice = await getVoiceState();
      if (voice.success) setVoiceState(voice);
    }
  };

  const handleUserVolumeChange = async (userId: string, volume: number) => {
    await setUserVolume(userId, Math.round(volume));
    const newVolumes = { ...userVolumes, [userId]: volume };
    setUserVolumes(newVolumes);
    await saveSettings({ user_volumes: newVolumes });
  };

  const handleUserMuteToggle = async (userId: string, muted: boolean) => {
    await muteUser(userId, muted);
  };

  const handleNotificationsChange = async (enabled: boolean) => {
    setNotificationsEnabled(enabled);
    await saveSettings({ notifications_enabled: enabled });
  };

  const handleAutoConnectChange = async (enabled: boolean) => {
    setAutoConnectEnabled(enabled);
    await saveSettings({ auto_connect: enabled });
  };

  const handleSteamSyncChange = async (enabled: boolean) => {
    setSteamSyncEnabled(enabled);
    await saveSettings({ game_sync_enabled: enabled });
  };

  const handleLanguageChange = async (lang: Language) => {
    setLanguage(lang);
    await saveSettings({ language: lang });
  };

  // ==================== RENDER: LOADING ====================

  if (isLoading) {
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

  // ==================== RENDER: DISCORD NOT INSTALLED ====================

  if (!discordInstalled) {
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

  // ==================== RENDER: DISCORD NOT RUNNING ====================

  if (!discordRunning && !isAuthenticated) {
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
            onClick={handleLaunchDiscord}
            disabled={isLaunching}
          >
            {isLaunching ? `⏳ ${t("launching")}` : `🚀 ${t("launchDiscord")}`}
          </ButtonItem>
        </PanelSectionRow>

        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={handleConnect}
            disabled={isConnecting}
          >
            {isConnecting ? `⏳ ${t("connecting")}` : `🔗 ${t("connect")}`}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  // ==================== RENDER: NOT AUTHENTICATED ====================

  if (!isAuthenticated) {
    return (
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={styles.statusBadge(false)}>🔌 {statusMessage}</div>
        </PanelSectionRow>

        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={handleConnect}
            disabled={isConnecting}
          >
            {isConnecting
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

  // ==================== RENDER: AUTHENTICATED ====================

  const selectedGuild = guilds.find((g) => g.id === selectedGuildId);

  return (
    <Fragment>
      {/* Status & Channel */}
      <PanelSection title="Discord Lite">
        <PanelSectionRow>
          <div style={styles.statusBadge(true)}>
            <span>✅</span>
            <span>{username || t("connected")}</span>
          </div>
        </PanelSectionRow>

        {voiceState?.in_voice && voiceState.channel_name && (
          <PanelSectionRow>
            <div style={styles.channelBadge}>
              <div style={styles.channelName}>
                <span>🔊</span>
                <span>{voiceState.channel_name}</span>
              </div>
              <div style={styles.callTime}>⏱️ {formatTime(callDuration)}</div>
            </div>
          </PanelSectionRow>
        )}
      </PanelSection>

      {/* Voice Controls */}
      <PanelSection title={`🎤 ${t("controls")}`}>
        <PanelSectionRow>
          <Focusable
            style={styles.controlButton(
              !voiceState?.is_muted && !voiceState?.is_deafened,
              muteFocused,
              voiceState?.is_deafened || false,
            )}
            onActivate={() => {
              if (!voiceState?.is_deafened) {
                handleToggleMute();
              }
            }}
            onFocus={() => setMuteFocused(true)}
            onBlur={() => setMuteFocused(false)}
          >
            <div style={{ width: "100%", textAlign: "center" }}>
              {voiceState?.is_deafened
                ? `🔇 ${t("muted")} (${t("deafened")})`
                : voiceState?.is_muted
                  ? `🔇 ${t("muted")}`
                  : `🎤 ${t("micActive")}`}
            </div>
          </Focusable>
        </PanelSectionRow>

        <PanelSectionRow>
          <Focusable
            style={styles.controlButton(
              !voiceState?.is_deafened,
              deafenFocused,
            )}
            onActivate={handleToggleDeafen}
            onFocus={() => setDeafenFocused(true)}
            onBlur={() => setDeafenFocused(false)}
          >
            <div style={{ width: "100%", textAlign: "center" }}>
              {voiceState?.is_deafened
                ? `🔇 ${t("deafened")}`
                : `🔊 ${t("audioActive")}`}
            </div>
          </Focusable>
        </PanelSectionRow>

        <PanelSectionRow>
          <SliderField
            label={t("microphone")}
            value={voiceState?.input_volume ?? 100}
            min={0}
            max={100}
            step={5}
            onChange={handleInputVolume}
            showValue
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <SliderField
            label={t("volume")}
            value={voiceState?.output_volume ?? 100}
            min={0}
            max={200}
            step={5}
            onChange={handleOutputVolume}
            showValue
          />
        </PanelSectionRow>
      </PanelSection>

      {/* Server Selection */}
      <PanelSection title={`🏠 ${t("server")}`}>
        {!showGuildPicker ? (
          <Fragment>
            {selectedGuild && (
              <PanelSectionRow>
                <Focusable
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: theme.spacing.md,
                    padding: theme.spacing.md,
                    backgroundColor: "rgba(88, 101, 242, 0.1)",
                    borderRadius: theme.borderRadius.md,
                    border: `1px solid rgba(88, 101, 242, 0.3)`,
                  }}
                  onActivate={() => setShowGuildPicker(true)}
                >
                  {selectedGuild.icon_url ? (
                    <img
                      src={selectedGuild.icon_url}
                      alt={selectedGuild.name}
                      style={{
                        width: "40px",
                        height: "40px",
                        borderRadius: theme.borderRadius.md,
                        objectFit: "cover",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: "40px",
                        height: "40px",
                        borderRadius: theme.borderRadius.md,
                        backgroundColor: theme.colors.primary,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "16px",
                        fontWeight: 600,
                        color: "#fff",
                      }}
                    >
                      {selectedGuild.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontSize: "14px",
                        fontWeight: 500,
                        color: theme.colors.text.primary,
                      }}
                    >
                      {selectedGuild.name}
                    </div>
                    <div
                      style={{
                        fontSize: "12px",
                        color: theme.colors.text.muted,
                      }}
                    >
                      {t("changeServer")} →
                    </div>
                  </div>
                </Focusable>
              </PanelSectionRow>
            )}
            {!selectedGuild && (
              <PanelSectionRow>
                <ButtonItem
                  layout="below"
                  onClick={() => setShowGuildPicker(true)}
                >
                  📋 {t("changeServer")}
                </ButtonItem>
              </PanelSectionRow>
            )}
          </Fragment>
        ) : (
          <Fragment>
            {guilds.length > 0 ? (
              <PanelSectionRow>
                <div style={styles.serverList}>
                  {guilds.map((guild) => (
                    <ServerItem
                      key={guild.id}
                      guild={guild}
                      selected={guild.id === selectedGuildId}
                      onSelect={() => handleSelectGuild(guild.id)}
                    />
                  ))}
                </div>
              </PanelSectionRow>
            ) : (
              <PanelSectionRow>
                <div style={styles.infoText}>{t("noServers")}</div>
              </PanelSectionRow>
            )}
            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={() => setShowGuildPicker(false)}
              >
                ✖ {t("close")}
              </ButtonItem>
            </PanelSectionRow>
          </Fragment>
        )}
      </PanelSection>

      {/* Channel Selection */}
      <PanelSection title={`📢 ${t("voiceChannel")}`}>
        {!showChannelPicker ? (
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleLoadChannels}>
              🔊 {t("selectChannel")}
            </ButtonItem>
          </PanelSectionRow>
        ) : (
          <Fragment>
            {channels.length > 0 ? (
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
              >
                ✖ {t("close")}
              </ButtonItem>
            </PanelSectionRow>
          </Fragment>
        )}

        {voiceState?.in_voice && (
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleLeaveVoice}>
              📴 {t("leaveChannel")}
            </ButtonItem>
          </PanelSectionRow>
        )}
      </PanelSection>

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
                savedVolume={userVolumes[member.user_id]}
                isSpeaking={voiceState.speaking_users?.includes(member.user_id)}
                onVolumeChange={handleUserVolumeChange}
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
                onChange={handleNotificationsChange}
              />
            </PanelSectionRow>

            <PanelSectionRow>
              <ToggleField
                label={t("autoConnect")}
                description={t("autoConnectDesc")}
                checked={autoConnectEnabled}
                onChange={handleAutoConnectChange}
              />
            </PanelSectionRow>

            <PanelSectionRow>
              <ToggleField
                label={t("steamSync")}
                description={t("steamSyncDesc")}
                checked={steamSyncEnabled}
                onChange={handleSteamSyncChange}
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
                onChange={(opt) => handleLanguageChange(opt.data as Language)}
              />
            </PanelSectionRow>
          </Fragment>
        )}
      </PanelSection>

      {/* Actions */}
      <PanelSection>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={handleSync}>
            🔄 {t("sync")}
          </ButtonItem>
        </PanelSectionRow>

        <PanelSectionRow>
          <ButtonItem layout="below" onClick={handleLogout}>
            🚪 {t("disconnect")}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
    </Fragment>
  );
}

// ==================== PLUGIN EXPORT ====================

let eventPollingInterval: ReturnType<typeof setInterval> | null = null;
let notificationsEnabled = true;
let currentLanguage: Language = "pt";

const startEventPolling = () => {
  if (eventPollingInterval) return;

  const pollEvents = async () => {
    try {
      const settings = await getSettings();
      notificationsEnabled = settings.settings?.notifications_enabled ?? true;
      currentLanguage = settings.settings?.language ?? "pt";

      if (!notificationsEnabled) return;

      const result = await getPendingEvents();
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
    titleView: <div className={staticClasses.Title}>Discord Lite</div>,
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
