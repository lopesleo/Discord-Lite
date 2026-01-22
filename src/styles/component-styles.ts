import { theme } from "./theme";

// ==================== COMPONENT STYLES ====================

export const styles = {
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
    border: "2px solid transparent",
    transition: "all 0.2s ease",
  },

  memberHeaderFocused: {
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    border: "2px solid white",
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
