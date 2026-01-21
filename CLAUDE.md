# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Discord Lite is a Decky Loader plugin for Steam Deck that provides Discord voice chat controls from the Quick Access Menu. It enables voice channel management, member volume control, and game status synchronization.

## Build Commands

```bash
# Install dependencies (requires pnpm v9)
pnpm i

# Build frontend (TypeScript → JavaScript via Rollup)
pnpm run build

# Watch mode for development
pnpm run watch
```

## Deployment

```powershell
# Windows: Deploy to Steam Deck (requires .env with DECK_HOST, DECK_USER, DECK_PASS)
.\deploy.ps1 -Deploy

# Create release ZIP
.\create-zip.ps1 -Version "v1.2.1"
```

```bash
# Linux/Mac
./deploy.sh
./build.sh
```

## Architecture

### Frontend (src/index.tsx)
- React/TypeScript using @decky/ui components
- Communicates with backend via `callable()` from @decky/api
- Bilingual support (EN/PT) with inline translations

### Backend (main.py)
- Python async plugin for Decky Loader
- **DiscordRPC class**: Manages IPC socket connection to Discord client
- **Plugin class**: Exposes 30+ async methods callable from frontend
- OAuth2 PKCE authentication (no client_secret required)

### Communication Flow
```
Frontend (React) → callable("method_name") → Python async method → Discord IPC socket
```

### Key RPC Commands to Discord
- `GET_VOICE_SETTINGS` / `SET_VOICE_SETTINGS` - Volume and audio settings
- `GET_SELECTED_VOICE_CHANNEL` / `SELECT_VOICE_CHANNEL` - Channel management
- `SET_USER_VOICE_SETTINGS` - Per-user volume (0-200 range)
- `SET_ACTIVITY` - Game status sync

## Important Implementation Details

### Volume Control
Discord RPC expects values to be sent directly (0-100 for input, 0-200 for output). The Discord client handles perceptual-to-amplitude conversion internally.

### IPC Socket Paths (Linux/Steam Deck)
```
/run/user/{uid}/discord-ipc-{0-9}
/run/user/{uid}/app/com.discordapp.Discord/discord-ipc-{0-9}
/tmp/discord-ipc-{0-9}
```

### OAuth2 Scopes
```python
["rpc", "rpc.voice.read", "rpc.voice.write"]
```

## File Structure

| File | Purpose |
|------|---------|
| `main.py` | Python backend - DiscordRPC client + Plugin class |
| `src/index.tsx` | React frontend - UI components + RPC callables |
| `plugin.json` | Decky plugin metadata |
| `lib/pypresence/` | Vendored Discord RPC library |

## Debugging

```bash
# View plugin logs on Steam Deck
journalctl -u plugin_loader -f | grep "Discord Lite"
```

Backend logging uses `decky.logger.info()` and `decky.logger.error()`.
