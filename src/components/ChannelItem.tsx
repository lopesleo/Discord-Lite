import { useState } from "react";
import { Focusable } from "@decky/ui";
import type { VoiceChannel } from "../types/index";
import { theme } from "../styles/theme";
import { styles } from "../styles/component-styles";

interface ChannelItemProps {
  channel: VoiceChannel;
  selected: boolean;
  onSelect: () => void;
}

export function ChannelItem({ channel, selected, onSelect }: ChannelItemProps) {
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
