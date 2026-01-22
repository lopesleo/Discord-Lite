import { useState } from "react";
import { Focusable } from "@decky/ui";
import type { VoiceChannel } from "../types/index";
import { theme } from "../styles/theme";
import { styles } from "../styles/component-styles";

interface ChannelItemProps {
  channel: VoiceChannel;
  selected: boolean;
  onSelect: () => void;
  disabled?: boolean;
}

export function ChannelItem({ channel, selected, onSelect, disabled = false }: ChannelItemProps) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <Focusable
      style={{
        ...styles.channelItem(selected, isFocused),
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? 'none' : 'auto',
      }}
      onActivate={disabled ? undefined : onSelect}
      onFocus={() => !disabled && setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
    >
      <span style={styles.channelIcon(isFocused)}>
        {disabled ? "⏳" : "🔊"}
      </span>
      <span style={styles.channelText(selected, isFocused)}>
        {channel.name}
      </span>
      {isFocused && !disabled && (
        <span style={{ marginLeft: "auto", color: theme.colors.primary }}>
          →
        </span>
      )}
    </Focusable>
  );
}
