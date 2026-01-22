import type { Language, Translations } from "../types/index";

// ==================== TRANSLATIONS ====================

export const translations: Record<Language, Translations> = {
  en: {
    // General
    loading: "Loading...",
    sync: "SYNC",
    disconnect: "DISCONNECT",
    connect: "CONNECT",
    connecting: "Connecting...",
    connected: "Connected",
    connectedAs: "Connected as",
    notConnected: "Not connected",
    error: "Error",
    success: "Success",

    // Discord status
    discordNotInstalled: "Discord not installed",
    installDiscord:
      "Install Discord via Discover (Flatpak) to use this plugin.",
    discordNotRunning: "Discord is not running",
    launchDiscord: "LAUNCH DISCORD",
    launching: "Launching...",
    openDiscord: "Discord open! Click to connect",
    connectToDiscord: "CONNECT TO DISCORD",
    authWindow: "A window will appear in Discord to authorize",

    // Voice controls
    controls: "Controls",
    muted: "MUTED",
    micActive: "MIC ACTIVE",
    deafened: "DEAFENED",
    audioActive: "AUDIO ACTIVE",
    microphone: "Microphone",
    volume: "Volume",

    // Server & Channel
    server: "Server",
    changeServer: "CHANGE SERVER",
    noServers: "No servers found",
    close: "CLOSE",
    voiceChannel: "Voice Channel",
    selectChannel: "SELECT CHANNEL",
    noChannels: "No voice channels",
    leaveChannel: "LEAVE CHANNEL",

    // Members
    members: "Members",
    userVolume: "Volume",
    unmuteUser: "Unmute user",
    muteUser: "Mute user",

    // Settings
    settings: "Settings",
    showSettings: "SHOW",
    hideSettings: "HIDE",
    notifications: "Notifications",
    notificationsDesc: "Show toasts when members join/leave",
    autoConnect: "Auto-connect",
    autoConnectDesc: "Connect automatically when Discord is open",
    language: "Language",
    steamSync: "Steam Game Sync",
    steamSyncDesc: "Show current game in Discord status",

    // Call time
    inCall: "In call",
    callTime: "Call time",

    // Toasts
    joined: "joined",
    left: "left",
    theCall: "the call",
    syncComplete: "Synced",
    membersInChannel: "members in channel",
  },
  pt: {
    // General
    loading: "Carregando...",
    sync: "SINCRONIZAR",
    disconnect: "DESCONECTAR",
    connect: "CONECTAR",
    connecting: "Conectando...",
    connected: "Conectado",
    connectedAs: "Conectado como",
    notConnected: "Não conectado",
    error: "Erro",
    success: "Sucesso",

    // Discord status
    discordNotInstalled: "Discord não instalado",
    installDiscord:
      "Instale o Discord pelo Discover (Flatpak) para usar este plugin.",
    discordNotRunning: "Discord não está aberto",
    launchDiscord: "ABRIR DISCORD",
    launching: "Iniciando...",
    openDiscord: "Discord aberto! Clique para conectar",
    connectToDiscord: "CONECTAR AO DISCORD",
    authWindow: "Uma janela aparecerá no Discord para autorizar",

    // Voice controls
    controls: "Controles",
    muted: "MUTADO",
    micActive: "MICROFONE ATIVO",
    deafened: "SURDO",
    audioActive: "ÁUDIO ATIVO",
    microphone: "Microfone",
    volume: "Volume",

    // Server & Channel
    server: "Servidor",
    changeServer: "TROCAR SERVIDOR",
    noServers: "Nenhum servidor encontrado",
    close: "FECHAR",
    voiceChannel: "Canal de Voz",
    selectChannel: "ESCOLHER CANAL",
    noChannels: "Nenhum canal de voz",
    leaveChannel: "SAIR DO CANAL",

    // Members
    members: "Membros",
    userVolume: "Volume",
    unmuteUser: "Desmutar usuário",
    muteUser: "Mutar usuário",

    // Settings
    settings: "Configurações",
    showSettings: "MOSTRAR",
    hideSettings: "OCULTAR",
    notifications: "Notificações",
    notificationsDesc: "Mostrar toasts quando membros entram/saem",
    autoConnect: "Auto-conectar",
    autoConnectDesc: "Conectar automaticamente quando Discord estiver aberto",
    language: "Idioma",
    steamSync: "Sincronizar Jogo Steam",
    steamSyncDesc: "Mostrar jogo atual no status do Discord",

    // Call time
    inCall: "Na call",
    callTime: "Tempo na call",

    // Toasts
    joined: "entrou",
    left: "saiu",
    theCall: "da call",
    syncComplete: "Sincronizado",
    membersInChannel: "membros no canal",
  },
};
