import { useState, useCallback } from "react";
import type { Guild, VoiceChannel, VoiceStateResponse } from "../types/index";
import * as DiscordAPI from "../api/discord-api";

interface UseGuildsAndChannelsResult {
  guilds: Guild[];
  selectedGuildId: string | null;
  channels: VoiceChannel[];
  showGuildPicker: boolean;
  showChannelPicker: boolean;
  setGuilds: React.Dispatch<React.SetStateAction<Guild[]>>;
  setSelectedGuildId: React.Dispatch<React.SetStateAction<string | null>>;
  setChannels: React.Dispatch<React.SetStateAction<VoiceChannel[]>>;
  setShowGuildPicker: React.Dispatch<React.SetStateAction<boolean>>;
  setShowChannelPicker: React.Dispatch<React.SetStateAction<boolean>>;
  selectGuild: (guildId: string) => Promise<void>;
  loadChannels: (voiceState: VoiceStateResponse | null) => Promise<void>;
  joinChannel: (channelId: string, onSuccess: (voiceState: VoiceStateResponse) => void) => Promise<void>;
}

export function useGuildsAndChannels(): UseGuildsAndChannelsResult {
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null);
  const [channels, setChannels] = useState<VoiceChannel[]>([]);
  const [showGuildPicker, setShowGuildPicker] = useState(false);
  const [showChannelPicker, setShowChannelPicker] = useState(false);

  const selectGuild = useCallback(async (guildId: string) => {
    await DiscordAPI.selectGuild(guildId);
    setSelectedGuildId(guildId);
    setShowGuildPicker(false);

    const channelsRes = await DiscordAPI.getVoiceChannels(guildId);
    if (channelsRes.success) {
      setChannels(channelsRes.channels);
      setShowChannelPicker(true);
    }
  }, []);

  const loadChannels = useCallback(
    async (voiceState: VoiceStateResponse | null) => {
      const guildId = selectedGuildId || voiceState?.guild_id || undefined;
      const result = await DiscordAPI.getVoiceChannels(guildId);
      if (result.success) {
        setChannels(result.channels);
        setShowChannelPicker(true);
      }
    },
    [selectedGuildId]
  );

  const joinChannel = useCallback(
    async (
      channelId: string,
      onSuccess: (voiceState: VoiceStateResponse) => void
    ) => {
      const result = await DiscordAPI.joinVoiceChannel(channelId);
      if (result.success) {
        setShowChannelPicker(false);
        const voice = await DiscordAPI.getVoiceState();
        if (voice.success) onSuccess(voice);
      }
    },
    []
  );

  return {
    guilds,
    selectedGuildId,
    channels,
    showGuildPicker,
    showChannelPicker,
    setGuilds,
    setSelectedGuildId,
    setChannels,
    setShowGuildPicker,
    setShowChannelPicker,
    selectGuild,
    loadChannels,
    joinChannel,
  };
}
