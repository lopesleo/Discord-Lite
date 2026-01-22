import { useState, useEffect, useCallback } from "react";
import { toaster } from "@decky/api";
import type { VoiceStateResponse } from "../types/index";
import * as DiscordAPI from "../api/discord-api";

interface UseVoiceStateOptions {
  isAuthenticated: boolean;
  syncCompleteText?: string;
  membersInChannelText?: string;
}

interface UseVoiceStateResult {
  voiceState: VoiceStateResponse | null;
  setVoiceState: React.Dispatch<React.SetStateAction<VoiceStateResponse | null>>;
  toggleMute: () => Promise<void>;
  toggleDeafen: () => Promise<void>;
  setInputVolume: (value: number) => Promise<void>;
  setOutputVolume: (value: number) => Promise<void>;
  leaveVoice: () => Promise<void>;
  sync: () => Promise<void>;
}

export function useVoiceState(
  options: UseVoiceStateOptions
): UseVoiceStateResult {
  const { isAuthenticated, syncCompleteText, membersInChannelText } = options;
  const [voiceState, setVoiceState] = useState<VoiceStateResponse | null>(null);

  // Sync voice state periodically when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;

    const syncVoiceState = async () => {
      try {
        const voice = await DiscordAPI.getVoiceState();
        if (voice.success) setVoiceState(voice);
      } catch (e) {
        console.error("Error syncing voice state:", e);
      }
    };

    const intervalId = setInterval(syncVoiceState, 5000);
    return () => clearInterval(intervalId);
  }, [isAuthenticated]);

  const toggleMute = useCallback(async () => {
    const result = await DiscordAPI.toggleMute();
    if (result.success) {
      setVoiceState((prev) =>
        prev ? { ...prev, is_muted: result.is_muted } : null
      );
    }
  }, []);

  const toggleDeafen = useCallback(async () => {
    const result = await DiscordAPI.toggleDeafen();
    if (result.success) {
      setVoiceState((prev) =>
        prev
          ? {
              ...prev,
              is_deafened: result.is_deafened,
              is_muted: result.is_muted,
            }
          : null
      );
    }
  }, []);

  const setInputVolume = useCallback(async (value: number) => {
    const result = await DiscordAPI.setInputVolume(Math.round(value));
    if (result.success) {
      setVoiceState((prev) =>
        prev ? { ...prev, input_volume: result.volume ?? value } : null
      );
    } else {
      console.error("Failed to set input volume:", result.message);
    }
  }, []);

  const setOutputVolume = useCallback(async (value: number) => {
    const result = await DiscordAPI.setOutputVolume(Math.round(value));
    if (result.success) {
      setVoiceState((prev) =>
        prev ? { ...prev, output_volume: result.volume ?? value } : null
      );
    } else {
      console.error("Failed to set output volume:", result.message);
    }
  }, []);

  const leaveVoice = useCallback(async () => {
    const result = await DiscordAPI.leaveVoice();
    if (result.success) {
      setVoiceState((prev) =>
        prev
          ? { ...prev, in_voice: false, channel_name: null, members: [] }
          : null
      );
    }
  }, []);

  const sync = useCallback(async () => {
    try {
      const fullState = await DiscordAPI.syncFullState();
      if (fullState.success) {
        setVoiceState(fullState);
        toaster.toast({
          title: `✅ ${syncCompleteText || "Synced"}`,
          body: `${fullState.members?.length || 0} ${membersInChannelText || "members in channel"}`,
          duration: 2000,
        });
      }
    } catch {
      console.error("Sync error");
    }
  }, [syncCompleteText, membersInChannelText]);

  return {
    voiceState,
    setVoiceState,
    toggleMute,
    toggleDeafen,
    setInputVolume,
    setOutputVolume,
    leaveVoice,
    sync,
  };
}
