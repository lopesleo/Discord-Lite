import { useState, useEffect, useCallback } from "react";
import { ButtonItem, SliderField, Focusable } from "@decky/ui";
import type { VoiceMember, TranslationKey } from "../types/index";
import { theme } from "../styles/theme";
import { styles } from "../styles/component-styles";

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

export function MemberItem({
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
  const [headerFocused, setHeaderFocused] = useState(false);

  // Sync with backend
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
