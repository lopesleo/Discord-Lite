// ==================== TYPE DEFINITIONS ====================

export type Language = "en" | "pt";

// Translation types (defined here to avoid circular import)
export interface Translations {
  loading: string;
  sync: string;
  disconnect: string;
  connect: string;
  connecting: string;
  connected: string;
  connectedAs: string;
  notConnected: string;
  error: string;
  success: string;
  discordNotInstalled: string;
  installDiscord: string;
  discordNotRunning: string;
  launchDiscord: string;
  launching: string;
  openDiscord: string;
  connectToDiscord: string;
  authWindow: string;
  controls: string;
  muted: string;
  micActive: string;
  deafened: string;
  audioActive: string;
  microphone: string;
  volume: string;
  server: string;
  changeServer: string;
  noServers: string;
  close: string;
  voiceChannel: string;
  selectChannel: string;
  noChannels: string;
  leaveChannel: string;
  members: string;
  userVolume: string;
  unmuteUser: string;
  muteUser: string;
  settings: string;
  showSettings: string;
  hideSettings: string;
  notifications: string;
  notificationsDesc: string;
  autoConnect: string;
  autoConnectDesc: string;
  language: string;
  steamSync: string;
  steamSyncDesc: string;
  inCall: string;
  callTime: string;
  joined: string;
  left: string;
  theCall: string;
  syncComplete: string;
  membersInChannel: string;
}

export type TranslationKey = keyof Translations;

export interface AutoAuthResponse {
  success: boolean;
  authenticated: boolean;
  user?: { username?: string; id?: string };
  message: string;
}

export interface VoiceMember {
  user_id: string;
  username: string;
  avatar?: string;
  mute: boolean;
  deaf: boolean;
  volume: number;
}

export interface VoiceChannel {
  id: string;
  name: string;
  type: number;
}

export interface Guild {
  id: string;
  name: string;
  icon_url?: string;
}

export interface VoiceStateResponse {
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

export interface ActionResponse {
  success: boolean;
  is_muted?: boolean;
  is_deafened?: boolean;
  volume?: number;
  message?: string;
}

export interface ChannelsResponse {
  success: boolean;
  guild_id?: string;
  channels: VoiceChannel[];
  message?: string;
}

export interface GuildsResponse {
  success: boolean;
  guilds: Guild[];
  selected_guild_id?: string;
  message?: string;
}

export interface DiscordStatusResponse {
  success: boolean;
  installed?: boolean;
  running?: boolean;
  flatpak?: boolean;
  native?: boolean;
  message?: string;
}

export interface SettingsResponse {
  success: boolean;
  settings: {
    notifications_enabled?: boolean;
    auto_connect?: boolean;
    game_sync_enabled?: boolean;
    language?: Language;
    user_volumes?: Record<string, number>;
  };
}

export interface VoiceEvent {
  type: "VOICE_JOIN" | "VOICE_LEAVE";
  user_id?: string;
  username?: string;
  avatar?: string;
}
