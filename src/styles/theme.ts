// ==================== THEME ====================

export const theme = {
  colors: {
    primary: "#5865F2",
    primaryHover: "#4752C4",
    success: "#3BA55C",
    danger: "#ED4245",
    warning: "#FAA61A",
    background: {
      primary: "rgba(30, 31, 34, 0.95)",
      secondary: "rgba(43, 45, 49, 0.9)",
      tertiary: "rgba(54, 57, 63, 0.8)",
      hover: "rgba(79, 84, 92, 0.4)",
    },
    text: {
      primary: "#FFFFFF",
      secondary: "#B9BBBE",
      muted: "#72767D",
    },
    border: "rgba(255, 255, 255, 0.06)",
  },
  borderRadius: {
    sm: "4px",
    md: "8px",
    lg: "12px",
    full: "50%",
  },
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "20px",
  },
} as const;
