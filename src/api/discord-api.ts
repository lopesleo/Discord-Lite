import { callable } from "@decky/api";
import type {
  AutoAuthResponse,
  VoiceStateResponse,
  ActionResponse,
  ChannelsResponse,
  GuildsResponse,
  DiscordStatusResponse,
  SettingsResponse,
  VoiceEvent,
  Guild,
} from "../types/index";

// ==================== API CALLS ====================

export const autoAuth = callable<[], AutoAuthResponse>("auto_auth");
export const checkStatus = callable<[], AutoAuthResponse>("check_status");
export const logout = callable<[], ActionResponse>("logout");
export const getVoiceState = callable<[], VoiceStateResponse>("get_voice_state");
export const toggleMute = callable<[], ActionResponse>("toggle_mute");
export const toggleDeafen = callable<[], ActionResponse>("toggle_deafen");
export const setInputVolume = callable<[number], ActionResponse>("set_input_volume");
export const setOutputVolume = callable<[number], ActionResponse>("set_output_volume");
export const leaveVoice = callable<[], ActionResponse>("leave_voice");
export const getVoiceChannels = callable<[string?], ChannelsResponse>(
  "get_voice_channels",
);
export const joinVoiceChannel = callable<[string], ActionResponse>(
  "join_voice_channel",
);
export const setUserVolume = callable<[string, number], ActionResponse>(
  "set_user_volume",
);
export const muteUser = callable<[string, boolean], ActionResponse>("mute_user");
export const getGuilds = callable<[], GuildsResponse>("get_guilds");
export const selectGuild = callable<[string], ActionResponse>("select_guild");
export const checkDiscordInstalled = callable<[], DiscordStatusResponse>(
  "check_discord_installed",
);
export const launchDiscord = callable<[], ActionResponse>("launch_discord");
export const checkDiscordRunning = callable<[], DiscordStatusResponse>(
  "check_discord_running",
);
export const syncFullState = callable<
  [],
  VoiceStateResponse & {
    guilds?: Guild[];
    selected_guild_id?: string;
    is_camera_on?: boolean;
    is_screen_sharing?: boolean;
  }
>("sync_full_state");
export const getPendingEvents = callable<
  [],
  { success: boolean; events: VoiceEvent[] }
>("get_pending_events");
export const getSettings = callable<[], SettingsResponse>("get_settings");
export const saveSettings = callable<[Record<string, unknown>], ActionResponse>(
  "save_settings_async",
);
