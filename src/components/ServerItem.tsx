import { useState } from "react";
import { Focusable } from "@decky/ui";
import type { Guild } from "../types/index";
import { theme } from "../styles/theme";
import { styles } from "../styles/component-styles";

interface ServerItemProps {
  guild: Guild;
  selected: boolean;
  onSelect: () => void;
}

export function ServerItem({ guild, selected, onSelect }: ServerItemProps) {
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
