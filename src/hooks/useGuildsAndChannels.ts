import { useState, useCallback } from "react";
import type { Guild, VoiceChannel, VoiceStateResponse } from "../types/index";
import * as DiscordAPI from "../api/discord-api";

interface UseGuildsAndChannelsResult {
  guilds: Guild[];
  selectedGuildId: string | null;
  channels: VoiceChannel[];
  showChannelPicker: boolean;
  isLoadingChannels: boolean;
  isJoiningChannel: boolean;
  setGuilds: React.Dispatch<React.SetStateAction<Guild[]>>;
  setSelectedGuildId: React.Dispatch<React.SetStateAction<string | null>>;
  setChannels: React.Dispatch<React.SetStateAction<VoiceChannel[]>>;
  setShowChannelPicker: React.Dispatch<React.SetStateAction<boolean>>;
  selectGuild: (guildId: string) => Promise<void>;
  loadChannels: (voiceState: VoiceStateResponse | null) => Promise<void>;
  joinChannel: (channelId: string, onSuccess: (voiceState: VoiceStateResponse) => void) => Promise<void>;
}

export function useGuildsAndChannels(): UseGuildsAndChannelsResult {
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(null);
  const [channels, setChannels] = useState<VoiceChannel[]>([]);
  const [showChannelPicker, setShowChannelPicker] = useState(false);
  const [isLoadingChannels, setIsLoadingChannels] = useState(false);
  const [isJoiningChannel, setIsJoiningChannel] = useState(false);

  const selectGuild = useCallback(async (guildId: string) => {
    setIsLoadingChannels(true);
    try {
      await DiscordAPI.selectGuild(guildId);
      setSelectedGuildId(guildId);

      const channelsRes = await DiscordAPI.getVoiceChannels(guildId);
      if (channelsRes.success) {
        setChannels(channelsRes.channels);
        setShowChannelPicker(true);
      }
    } finally {
      setIsLoadingChannels(false);
    }
  }, []);

  const loadChannels = useCallback(
    async (voiceState: VoiceStateResponse | null) => {
      setIsLoadingChannels(true);
      try {
        const guildId = selectedGuildId || voiceState?.guild_id || undefined;
        const result = await DiscordAPI.getVoiceChannels(guildId);
        if (result.success) {
          setChannels(result.channels);
          setShowChannelPicker(true);
        }
      } finally {
        setIsLoadingChannels(false);
      }
    },
    [selectedGuildId]
  );

  const joinChannel = useCallback(
    async (
      channelId: string,
      onSuccess: (voiceState: VoiceStateResponse) => void
    ) => {
      setIsJoiningChannel(true);
      try {
        const result = await DiscordAPI.joinVoiceChannel(channelId);
        if (result.success) {
          setShowChannelPicker(false);
          const voice = await DiscordAPI.getVoiceState();
          if (voice.success) onSuccess(voice);
        }
      } finally {
        setIsJoiningChannel(false);
      }
    },
    []
  );

  return {
    guilds,
    selectedGuildId,
    channels,
    showChannelPicker,
    isLoadingChannels,
    isJoiningChannel,
    setGuilds,
    setSelectedGuildId,
    setChannels,
    setShowChannelPicker,
    selectGuild,
    loadChannels,
    joinChannel,
  };
}
