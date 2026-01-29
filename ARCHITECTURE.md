# Discord Lite Architecture

## Overview

Discord Lite uses a layered modular architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│                     src/index.tsx                            │
│  - UI Components (Buttons, Sliders, Modals)                 │
│  - Bilingual Support (EN/PT)                                 │
│  - State Management                                          │
└────────────────┬────────────────────────────────────────────┘
                 │ callable() API
                 │ (Decky IPC)
┌────────────────▼────────────────────────────────────────────┐
│                 PLUGIN LAYER (main.py)                       │
│                    Plugin Class                              │
│  - 30+ async methods exposed to frontend                    │
│  - Request routing to backend modules                       │
│  - State coordination                                        │
└────┬────────────┬──────────┬──────────┬──────────┬──────────┘
     │            │          │          │          │
     │            │          │          │          │
┌────▼────┐  ┌───▼────┐ ┌───▼────┐ ┌──▼─────┐ ┌──▼────┐
│ Discord │  │  Auth  │ │ Voice  │ │ Steam  │ │ Utils │
│   RPC   │  │        │ │        │ │        │ │       │
└────┬────┘  └───┬────┘ └───┬────┘ └──┬─────┘ └──┬────┘
     │            │          │          │          │
     │            │          │          │          │
┌────▼────────────▼──────────▼──────────▼──────────▼──────────┐
│                   BACKEND MODULES                             │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ discord_rpc/ │  │    auth/     │  │   voice/     │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ client.py    │  │ oauth.py     │  │ volume.py    │      │
│  │ protocol.py  │  │ token_mgr.py │  │ controller.py│      │
│  │ events.py    │  └──────────────┘  │ members.py   │      │
│  └──────────────┘                     └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   steam/     │  │  polling/    │  │    utils/    │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ game_det.py  │  │ voice_poll.py│  │ cache.py     │      │
│  │ activity.py  │  └──────────────┘  │ settings.py  │      │
│  └──────────────┘                     │ socket_find.py│     │
│                                       └──────────────┘      │
└───────────────────────────────────────────────────────────────┘
                         │
                         │ Unix Domain Socket
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                    DISCORD CLIENT                             │
│              (Native or Flatpak)                              │
│  - IPC Socket: /run/user/{uid}/discord-ipc-0                 │
│  - Handles RPC commands                                       │
│  - Returns voice state, members, channels                     │
└───────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### 1. User Mutes Microphone

```
User clicks mute button
    ↓
Frontend: callable('toggle_mute')
    ↓
Plugin.toggle_mute()
    ↓
VoiceController.toggle_mute()
    ↓
DiscordRPCClient.send_command('SET_VOICE_SETTINGS', {mute: true})
    ↓
encode_message() → Unix socket → Discord
    ↓
Discord response ← Unix socket ← decode_message()
    ↓
VoiceController updates state
    ↓
Return {success: true, is_muted: true}
    ↓
Frontend updates UI
```

### 2. Background Game Detection

```
VoicePoller (background thread, runs every 15s)
    ↓
ActivitySyncManager.sync()
    ↓
SteamGameDetector.detect_running_game()
    ↓
Scan /proc for SteamLaunch processes
    ↓
Extract AppID from cmdline
    ↓
Look up game name from manifest files
    ↓
Find Discord official app ID (if exists)
    ↓
DiscordRPCClient.send_command('SET_ACTIVITY', {...})
    ↓
Discord updates Rich Presence status
```

### 3. Voice Member Join/Leave Notification

```
VoicePoller (background thread)
    ↓
Plugin._check_voice_members_changes()
    ↓
VoiceController.get_selected_voice_channel()
    ↓
DiscordRPCClient.send_command('GET_SELECTED_VOICE_CHANNEL')
    ↓
MemberTracker.update_and_get_diff(current_members)
    ↓
Detect: user "Alice" joined, user "Bob" left
    ↓
VoicePoller.enqueue_event('VOICE_JOIN', {...})
    ↓
Frontend: callable('get_pending_events')
    ↓
Plugin.get_pending_events() returns events
    ↓
Frontend shows toast notification
```

## Module Responsibilities

### discord_rpc/
**Purpose**: Low-level Discord IPC communication

- **client.py**: Socket connection, command execution, event subscription
- **protocol.py**: Message encoding/decoding (struct + JSON)
- **events.py**: Speaking state tracking, event processing

**Key Operations**:
- Connect to `/run/user/{uid}/discord-ipc-0` socket
- Send handshake with client ID
- Execute RPC commands with nonce tracking
- Subscribe to SPEAKING_START/STOP events

### auth/
**Purpose**: OAuth2 authentication and token management

- **oauth.py**: PKCE flow implementation
- **token_manager.py**: Token persistence

**Key Operations**:
- Generate PKCE verifier/challenge pair
- Request authorization from Discord client
- Exchange code for access token (no client_secret needed)
- Save token to `discord_token.json`

### voice/
**Purpose**: Voice settings and channel management

- **volume.py**: Perceptual ↔ amplitude conversion functions
- **controller.py**: High-level voice operations
- **members.py**: Member join/leave detection

**Key Operations**:
- Convert volume values (UI uses perceptual, Discord uses amplitude)
- Toggle mute/deafen
- Set input/output volume
- Join/leave channels
- Track member changes with diff algorithm

### steam/
**Purpose**: Steam game detection and Discord integration

- **game_detector.py**: Find running Steam games
- **activity_sync.py**: Update Discord Rich Presence

**Key Operations**:
- Scan `/proc` for Steam game processes
- Extract AppID from cmdline
- Read game name from manifest files
- Query Discord detectable apps API (cached 24h)
- Match game to official Discord app ID
- Update activity via SET_ACTIVITY command

### polling/
**Purpose**: Background event polling

- **voice_poller.py**: Adaptive polling thread

**Key Operations**:
- Run callbacks every 15s (active) or 60s (idle)
- Check voice member changes
- Sync game status
- Queue events for frontend

### utils/
**Purpose**: Shared utilities

- **cache.py**: LRU cache implementation
- **settings.py**: JSON settings persistence
- **socket_finder.py**: Discord IPC socket detection

**Key Operations**:
- Maintain LRU cache with max size
- Save/load settings from JSON
- Find Discord socket in 3 possible locations

## Key Design Patterns

### 1. Dependency Injection
VoiceController receives DiscordRPCClient as constructor parameter:
```python
self.voice_controller = VoiceController(self.rpc_client)
```

### 2. Facade Pattern
Plugin class provides simple async methods that delegate to complex backend:
```python
async def toggle_mute(self) -> dict:
    return self.voice_controller.toggle_mute()
```

### 3. Observer Pattern
VoicePoller uses callbacks to notify of changes:
```python
self.voice_poller.start(
    check_members_callback=self._check_members,
    sync_game_callback=self._sync_game,
    is_active_callback=self._is_active
)
```

### 4. Strategy Pattern
ActivitySyncManager tries official app ID first, falls back to main RPC:
```python
if discord_app_id:
    if self._try_official_app_id(discord_app_id, activity):
        return
self._set_main_rpc_activity(activity)
```

## Performance Optimizations

### 1. Caching
- **Game names**: LRU cache (50 entries)
- **Discord app IDs**: LRU cache (100 entries)
- **Discord detectable apps**: Disk cache (24h TTL)

### 2. Adaptive Polling
- **Active** (in voice or game running): Poll every 15 seconds
- **Idle** (neither): Poll every 60 seconds
- **Error recovery**: Sleep 20 seconds after exception

### 3. Fast Process Scanning
```python
# Fast: List numeric PIDs only
pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

# Fast: String check before expensive regex
if 'SteamLaunch' not in cmdline:
    continue

# Only then: Use pre-compiled regex
match = self.GAME_ID_REGEX.search(cmdline)
```

### 4. Volume Conversion
Functions use direct math operations (no loops):
```python
amplitude = normalized_max * (10 ** (db / 20))
```

## Error Handling Strategy

### 1. Graceful Degradation
If official Discord app ID fails, fall back to main RPC:
```python
if not self._try_official_app_id(discord_app_id, activity):
    self._set_main_rpc_activity(activity)
```

### 2. Comprehensive Logging
Every operation logs context:
```python
decky.logger.info(f"Discord Lite: Setting volume perceptual={vol} amplitude={amp}")
```

### 3. Structured Errors
Return dictionaries with success flag:
```python
return {"success": False, "message": "Not authenticated"}
```

### 4. Try-Except at Boundaries
Callback functions catch all exceptions:
```python
try:
    self.check_members_callback()
except Exception as e:
    decky.logger.error(f"Error in callback: {e}")
```

## Thread Safety

### Background Thread (VoicePoller)
- **Daemon thread**: Exits automatically when main thread exits
- **No shared mutable state**: Only reads from Plugin via callbacks
- **Queue for events**: Thread-safe Queue for event passing

### No Locks Needed
- Single writer (poller thread) for events
- Single reader (frontend) for events via async method
- No race conditions on Plugin state (only accessed from main thread)

## Testing Strategy

Run verification script:
```bash
python verify_refactor.py
```

Tests:
- ✓ All modules importable
- ✓ Volume conversion roundtrip
- ✓ LRU cache eviction
- ✓ Directory structure

## Future Enhancements

1. **Full Async**: Replace threading with asyncio for better integration
2. **Type Safety**: Add mypy type checking
3. **Unit Tests**: pytest suite for each module
4. **Metrics**: Track RPC latency, error rates
5. **Plugin System**: Allow custom activity providers

## References

- [Discord RPC Documentation](https://discord.com/developers/docs/topics/rpc)
- [Decky Loader Plugin Guide](https://github.com/SteamDeckHomebrew/decky-loader)
- [OAuth2 PKCE RFC](https://datatracker.ietf.org/doc/html/rfc7636)
