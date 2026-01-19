import os
import json
import ssl
import struct
import socket
import secrets
import subprocess
import asyncio
import threading
import time
import glob
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, List, Callable, Any
from queue import Queue, Empty

# The decky plugin module is located at decky-loader/plugin
import decky


class DiscordRPC:
    """Cliente Discord RPC com suporte a OAuth2"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.authenticated = False
        self.access_token: Optional[str] = None
        self.user: Optional[Dict] = None
        
        # Estado de voz
        self.is_muted = False
        self.is_deafened = False
        self.voice_channel_id: Optional[str] = None
        self.voice_channel_name: Optional[str] = None
        self.voice_guild_id: Optional[str] = None
        self.input_volume = 100
        self.output_volume = 100
        
        # Configurações de voz
        self.mode_type = "VOICE_ACTIVITY"  # VOICE_ACTIVITY ou PUSH_TO_TALK
        self.automatic_gain_control = True
        self.echo_cancellation = True
        self.noise_suppression = True
        self.qos = True
        self.silence_warning = False
        
        # Membros do canal
        self.voice_members: List[Dict] = []
        
        # Estado de quem está falando (user_id -> timestamp)
        self.speaking_users: Dict[str, float] = {}
    
    def get_ipc_path(self) -> Optional[str]:
        """Encontra o socket IPC do Discord"""
        uid = os.getuid()
        
        for i in range(10):
            for base_path in [
                f"/run/user/{uid}/discord-ipc-{i}",
                f"/run/user/{uid}/app/com.discordapp.Discord/discord-ipc-{i}",
                f"/tmp/discord-ipc-{i}",
            ]:
                if os.path.exists(base_path):
                    decky.logger.info(f"Discord Lite: Socket encontrado: {base_path}")
                    return base_path
        
        return None
    
    def encode_message(self, opcode: int, payload: dict) -> bytes:
        data = json.dumps(payload).encode('utf-8')
        header = struct.pack('<II', opcode, len(data))
        return header + data
    
    def decode_message(self, data: bytes) -> tuple:
        if len(data) < 8:
            return None, None
        opcode, length = struct.unpack('<II', data[:8])
        payload_data = data[8:8+length]
        try:
            payload = json.loads(payload_data.decode('utf-8'))
            return opcode, payload
        except:
            return opcode, None
    
    def connect(self) -> bool:
        ipc_path = self.get_ipc_path()
        if not ipc_path:
            decky.logger.error("Discord Lite: Socket IPC não encontrado")
            return False
        
        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.settimeout(60.0)
            self.socket.connect(ipc_path)
            
            handshake = {"v": 1, "client_id": self.client_id}
            self.socket.send(self.encode_message(0, handshake))
            
            response = self.socket.recv(4096)
            opcode, payload = self.decode_message(response)
            
            if payload and payload.get("cmd") == "DISPATCH" and payload.get("evt") == "READY":
                self.connected = True
                decky.logger.info("Discord Lite: Conectado ao Discord IPC")
                return True
            else:
                decky.logger.error(f"Discord Lite: Resposta inesperada: {payload}")
            
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao conectar: {e}")
        
        return False
    
    def send_command(self, cmd: str, args: dict = None, nonce: str = None) -> Optional[Dict]:
        if not self.socket:
            return None
        
        if nonce is None:
            nonce = secrets.token_hex(16)
        
        payload = {"cmd": cmd, "nonce": nonce}
        if args:
            payload["args"] = args
        
        try:
            self.socket.send(self.encode_message(1, payload))
            response = self.socket.recv(8192)
            opcode, result = self.decode_message(response)
            decky.logger.info(f"Discord Lite: Resposta {cmd}: {result}")
            return result
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro no comando {cmd}: {e}")
            return None
    
    def authorize(self, scopes: list) -> Optional[str]:
        result = self.send_command("AUTHORIZE", {
            "client_id": self.client_id,
            "scopes": scopes,
        })
        
        if result and result.get("data"):
            return result["data"].get("code")
        return None
    
    def authenticate(self, access_token: str) -> bool:
        result = self.send_command("AUTHENTICATE", {"access_token": access_token})
        
        if result and result.get("data"):
            self.authenticated = True
            self.user = result["data"].get("user")
            self.access_token = access_token
            decky.logger.info(f"Discord Lite: Autenticado como {self.user.get('username', 'unknown')}")
            return True
        
        decky.logger.error(f"Discord Lite: Falha ao autenticar: {result}")
        return False
    
    def get_voice_settings(self) -> Optional[Dict]:
        result = self.send_command("GET_VOICE_SETTINGS")
        if result and result.get("data"):
            data = result["data"]
            self.is_muted = data.get("mute", False)
            self.is_deafened = data.get("deaf", False)
            
            input_data = data.get("input", {})
            output_data = data.get("output", {})
            mode_data = data.get("mode", {})
            
            if isinstance(input_data, dict):
                self.input_volume = int(input_data.get("volume", 100))
            if isinstance(output_data, dict):
                self.output_volume = int(output_data.get("volume", 100))
            if isinstance(mode_data, dict):
                self.mode_type = mode_data.get("type", "VOICE_ACTIVITY")
            
            self.automatic_gain_control = data.get("automatic_gain_control", True)
            self.echo_cancellation = data.get("echo_cancellation", True)
            self.noise_suppression = data.get("noise_suppression", True)
            self.qos = data.get("qos", True)
            self.silence_warning = data.get("silence_warning", False)
            
            return data
        return None
    
    def set_voice_settings(self, **kwargs) -> dict:
        """Define configurações de voz e retorna resultado"""
        result = self.send_command("SET_VOICE_SETTINGS", kwargs)
        if result:
            if result.get("evt") == "ERROR":
                return {"success": False, "message": result.get("data", {}).get("message", "Erro")}
            return {"success": True, "data": result.get("data")}
        return {"success": False, "message": "Sem resposta"}
    
    def get_selected_voice_channel(self) -> Optional[Dict]:
        result = self.send_command("GET_SELECTED_VOICE_CHANNEL")
        if result and result.get("data"):
            data = result["data"]
            if data:
                self.voice_channel_id = data.get("id")
                self.voice_channel_name = data.get("name")
                self.voice_guild_id = data.get("guild_id")
                
                voice_states = data.get("voice_states", [])
                self.voice_members = []
                for vs in voice_states:
                    user = vs.get("user", {})
                    member = {
                        "user_id": user.get("id"),
                        "username": user.get("username", "Usuário"),
                        "avatar": user.get("avatar"),
                        "mute": vs.get("mute", False) or vs.get("self_mute", False),
                        "deaf": vs.get("deaf", False) or vs.get("self_deaf", False),
                        "volume": vs.get("volume", 100),
                    }
                    self.voice_members.append(member)
            else:
                self.voice_channel_id = None
                self.voice_channel_name = None
                self.voice_guild_id = None
                self.voice_members = []
            return data
        return None
    
    def select_voice_channel(self, channel_id: Optional[str], force: bool = False) -> bool:
        args = {"channel_id": channel_id}
        if force:
            args["force"] = True
        result = self.send_command("SELECT_VOICE_CHANNEL", args)
        return result is not None
    
    def get_channels(self, guild_id: str) -> List[Dict]:
        result = self.send_command("GET_CHANNELS", {"guild_id": guild_id})
        if result and result.get("data"):
            channels = result["data"].get("channels", [])
            voice_channels = [c for c in channels if c.get("type") == 2]
            return voice_channels
        return []
    
    def get_guilds(self) -> List[Dict]:
        result = self.send_command("GET_GUILDS")
        if result and result.get("data"):
            guilds = result["data"].get("guilds", [])
            # Adiciona URL do ícone para cada servidor
            for guild in guilds:
                guild_id = guild.get("id")
                icon_hash = guild.get("icon")
                if guild_id and icon_hash:
                    guild["icon_url"] = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png?size=64"
                else:
                    guild["icon_url"] = None
            return guilds
        return []
    
    def set_user_voice_settings(self, user_id: str, volume: int = None, mute: bool = None) -> bool:
        args = {"user_id": user_id}
        if volume is not None:
            args["volume"] = max(0, min(200, volume))
        if mute is not None:
            args["mute"] = mute
        
        result = self.send_command("SET_USER_VOICE_SETTINGS", args)
        return result is not None and result.get("cmd") == "SET_USER_VOICE_SETTINGS"
    
    def set_activity(self, activity: Dict) -> bool:
        """Define o status/atividade do usuário"""
        result = self.send_command("SET_ACTIVITY", {"pid": os.getpid(), "activity": activity})
        return result is not None
    
    def clear_activity(self) -> bool:
        """Limpa o status/atividade do usuário"""
        result = self.send_command("SET_ACTIVITY", {"pid": os.getpid(), "activity": None})
        return result is not None
    
    def clear_activity(self) -> bool:
        """Limpa o status/atividade do usuário"""
        result = self.send_command("SET_ACTIVITY", {"pid": os.getpid(), "activity": None})
        return result is not None
    
    def subscribe(self, event: str, args: dict = None) -> bool:
        """Inscreve-se em um evento do Discord"""
        payload = {"cmd": "SUBSCRIBE", "evt": event, "nonce": secrets.token_hex(16)}
        if args:
            payload["args"] = args
        
        try:
            self.socket.send(self.encode_message(1, payload))
            response = self.socket.recv(4096)
            opcode, result = self.decode_message(response)
            decky.logger.info(f"Discord Lite: SUBSCRIBE {event}: {result}")
            return result is not None and result.get("evt") == event
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao subscrever {event}: {e}")
            return False
    
    def receive_event(self, timeout: float = 0.1) -> Optional[Dict]:
        """Recebe evento do Discord (non-blocking)"""
        try:
            old_timeout = self.socket.gettimeout()
            self.socket.settimeout(timeout)
            response = self.socket.recv(4096)
            self.socket.settimeout(old_timeout)
            opcode, payload = self.decode_message(response)
            
            # Processa eventos de SPEAKING
            if payload and payload.get("evt") == "SPEAKING_START":
                data = payload.get("data", {})
                user_id = data.get("user_id")
                if user_id:
                    self.speaking_users[user_id] = time.time()
            elif payload and payload.get("evt") == "SPEAKING_STOP":
                data = payload.get("data", {})
                user_id = data.get("user_id")
                if user_id and user_id in self.speaking_users:
                    del self.speaking_users[user_id]
            
            return payload
        except socket.timeout:
            return None
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao receber evento: {e}")
            return None
    
    def subscribe_speaking_events(self, channel_id: str) -> bool:
        """Inscreve nos eventos de speaking de um canal"""
        try:
            self.subscribe("SPEAKING_START", {"channel_id": channel_id})
            self.subscribe("SPEAKING_STOP", {"channel_id": channel_id})
            decky.logger.info(f"Discord Lite: Inscrito em eventos de speaking para canal {channel_id}")
            return True
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao inscrever em speaking events: {e}")
            return False
    
    def get_speaking_users(self) -> List[str]:
        """Retorna lista de user_ids que estão falando atualmente"""
        now = time.time()
        # Remove entradas antigas (> 2 segundos sem atualização)
        self.speaking_users = {uid: ts for uid, ts in self.speaking_users.items() if now - ts < 2}
        return list(self.speaking_users.keys())
    
    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
        self.authenticated = False


class Plugin:
    """Discord Lite - Controle completo do Discord via Steam Deck"""
    
    CLIENT_ID = "1461502476401381446"
    CLIENT_SECRET = "KViXxKrEq_amyJY1CqHpGJmX8xpSzhFK"  # TODO: Move to settings file before publishing
    SCOPES = ["rpc", "rpc.voice.read", "rpc.voice.write"]
    
    rpc: Optional[DiscordRPC] = None
    access_token: Optional[str] = None
    auth_in_progress: bool = False
    
    # Servidores e canais em cache
    guilds_cache: List[Dict] = []
    selected_guild_id: Optional[str] = None
    
    # Cache de membros para detectar entrada/saída
    previous_members: Dict[str, dict] = {}  # user_id -> info
    initial_sync_done: bool = False  # Flag para evitar toasts ao conectar
    
    # Sistema de polling para eventos
    voice_polling_active: bool = False
    voice_polling_thread: Optional[threading.Thread] = None
    event_queue: Queue = Queue()
    last_poll_time: float = 0
    poll_interval: float = 5.0  # Segundos entre polls
    
    # Sistema de detecção de jogos Steam
    game_sync_enabled: bool = True
    current_game_appid: Optional[str] = None
    current_game_name: Optional[str] = None
    game_start_time: Optional[int] = None
    current_game_rpc: Optional[Any] = None  # Conexão RPC com App ID oficial
    
    # Cache de aplicativos detectáveis do Discord
    discord_detectable_apps: List[Dict] = []
    discord_apps_last_fetch: float = 0
    discord_apps_cache_duration: float = 86400  # 24 horas
    
    def get_token_path(self) -> str:
        return os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "discord_token.json")
    
    def get_settings_path(self) -> str:
        return os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "settings.json")
    
    def save_token(self, access_token: str):
        try:
            os.makedirs(decky.DECKY_PLUGIN_SETTINGS_DIR, exist_ok=True)
            with open(self.get_token_path(), 'w') as f:
                json.dump({"access_token": access_token}, f)
            decky.logger.info("Discord Lite: Token salvo")
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao salvar token: {e}")
    
    def load_token(self) -> Optional[str]:
        try:
            path = self.get_token_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    return self.access_token
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao carregar token: {e}")
        return None
    
    def save_settings(self, settings: dict):
        try:
            os.makedirs(decky.DECKY_PLUGIN_SETTINGS_DIR, exist_ok=True)
            current = self.load_settings()
            current.update(settings)
            with open(self.get_settings_path(), 'w') as f:
                json.dump(current, f)
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao salvar settings: {e}")
    
    def load_settings(self) -> dict:
        try:
            path = self.get_settings_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    # ==================== STEAM GAME DETECTION ====================
    
    def get_steam_game_info(self) -> Optional[Dict]:
        """Detecta o jogo Steam em execução e retorna informações"""
        try:
            found_games = []
            
            # Procurar por processos reaper (Steam game launcher)
            for proc_dir in glob.glob('/proc/[0-9]*'):
                try:
                    cmdline_path = os.path.join(proc_dir, 'cmdline')
                    if not os.path.exists(cmdline_path):
                        continue
                    
                    with open(cmdline_path, 'r') as f:
                        cmdline = f.read()
                    
                    # Procurar por SteamLaunch AppId=XXXXX
                    match = re.search(r'SteamLaunch.*?AppId=(\d+)', cmdline)
                    if match:
                        appid = match.group(1)
                        
                        # Ignorar o Discord (AppId comum: 3975918012 ou similar)
                        # Discord no Flatpak geralmente tem AppId muito alto
                        if 'discord' in cmdline.lower() or 'flatpak' in cmdline.lower():
                            continue
                        
                        found_games.append(appid)
                except (IOError, PermissionError):
                    continue
            
            # Pegar o primeiro jogo real encontrado
            if found_games:
                appid = found_games[0]
                
                # Tentar ler o nome do jogo do arquivo de manifesto
                game_name = self.get_game_name_from_appid(appid)
                if not game_name:
                    game_name = f"Game {appid}"
                
                return {
                    "appid": appid,
                    "name": game_name,
                    "image_url": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"
                }
            
            return None
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao detectar jogo Steam: {e}")
            return None
    
    def get_game_name_from_appid(self, appid: str) -> Optional[str]:
        """Tenta obter o nome do jogo a partir do AppID"""
        try:
            # Procurar em locais comuns do Steam
            steam_paths = [
                "/home/deck/.local/share/Steam/steamapps",
                "/home/deck/.steam/steam/steamapps",
                "/run/media/*/steamapps"
            ]
            
            for base_path in steam_paths:
                manifest_files = glob.glob(f"{base_path}/appmanifest_{appid}.acf")
                for manifest_path in manifest_files:
                    try:
                        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Procurar por "name" "Game Name"
                            match = re.search(r'"name"\s+"([^"]+)"', content)
                            if match:
                                return match.group(1)
                    except:
                        continue
            
            return None
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao obter nome do jogo: {e}")
            return None
    
    def get_cache_path(self) -> str:
        return os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "discord_apps_cache.json")

    def load_discord_detectable_apps(self):
        """Carrega lista de aplicativos detectáveis do Discord (com cache de 24h persistente)"""
        try:
            import ssl
            
            current_time = time.time()
            
            # 1. Verificar cache em memória
            if self.discord_detectable_apps and (current_time - self.discord_apps_last_fetch) < self.discord_apps_cache_duration:
                return self.discord_detectable_apps
            
            # 2. Verificar cache em disco (se memória estiver vazia ou expirada)
            cache_path = self.get_cache_path()
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        cache_data = json.load(f)
                        last_fetch = cache_data.get("last_fetch", 0)
                        
                        if (current_time - last_fetch) < self.discord_apps_cache_duration:
                            self.discord_detectable_apps = cache_data.get("apps", [])
                            self.discord_apps_last_fetch = last_fetch
                            decky.logger.info(f"Discord Lite: Carregados {len(self.discord_detectable_apps)} apps do cache em disco")
                            return self.discord_detectable_apps
                except Exception as e:
                    decky.logger.warning(f"Discord Lite: Erro ao ler cache em disco: {e}")
            
            # 3. Buscar da API do Discord (se cache inválido)
            decky.logger.info("Discord Lite: Buscando lista de apps detectáveis do Discord (Web)...")
            req = urllib.request.Request(
                "https://discord.com/api/v10/applications/detectable",
                headers={"User-Agent": "DiscordLite/1.0"}
            )
            
            # Criar contexto SSL que não verifica certificados (necessário no Steam Deck)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.discord_detectable_apps = data
                self.discord_apps_last_fetch = current_time
                
                # Salvar em disco
                try:
                    os.makedirs(decky.DECKY_PLUGIN_SETTINGS_DIR, exist_ok=True)
                    with open(cache_path, 'w') as f:
                        json.dump({
                            "last_fetch": current_time,
                            "apps": data
                        }, f)
                    decky.logger.info(f"Discord Lite: Cache salvo em disco com {len(data)} apps")
                except Exception as e:
                    decky.logger.error(f"Discord Lite: Erro ao salvar cache em disco: {e}")
                
                return data
        
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao buscar apps detectáveis: {e}")
            return self.discord_detectable_apps  # Retornar cache antigo se houver
    
    def find_discord_app_id(self, game_name: str) -> Optional[str]:
        """Busca o App ID oficial do Discord para um jogo pelo nome"""
        try:
            decky.logger.info(f"Discord Lite: Buscando App ID oficial para: {game_name}")
            apps = self.load_discord_detectable_apps()
            
            if not apps:
                decky.logger.warning("Discord Lite: Nenhum app detectável carregado")
                return None
            
            # Buscar match exato primeiro
            for app in apps:
                if app.get("name", "").lower() == game_name.lower():
                    app_id = app.get("id")
                    decky.logger.info(f"Discord Lite: Match exato encontrado! App ID: {app_id}")
                    return app_id
            
            # Buscar match parcial (contém)
            for app in apps:
                app_name = app.get("name", "").lower()
                if game_name.lower() in app_name or app_name in game_name.lower():
                    app_id = app.get("id")
                    decky.logger.info(f"Discord Lite: Match parcial encontrado! {app_name} → App ID: {app_id}")
                    return app_id
            
            decky.logger.info(f"Discord Lite: Nenhum App ID oficial encontrado para {game_name}")
            return None
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao buscar App ID do Discord: {e}")
            return None
    
    def sync_game_to_discord(self):
        """Sincroniza o jogo atual com o status do Discord"""
        if not self.rpc or not self.game_sync_enabled:
            return
        
        try:
            game_info = self.get_steam_game_info()
            
            # Se mudou o jogo
            if game_info and game_info["appid"] != self.current_game_appid:
                self.current_game_appid = game_info["appid"]
                self.current_game_name = game_info["name"]
                self.game_start_time = int(time.time())
                
                # Buscar App ID oficial do Discord para este jogo
                discord_app_id = self.find_discord_app_id(game_info["name"])
                
                # Definir textos da presença
                details = game_info["name"]
                state = "Playing on Steam Deck"
                
                # Se for usar app ID oficial, o nome do jogo já aparece no título
                if discord_app_id:
                    details = "Playing on Steam Deck"
                    state = None
                
                # Atualizar Rich Presence no Discord
                activity = {
                    "details": details,
                    "timestamps": {
                        "start": self.game_start_time
                    },
                    "assets": {
                        "large_image": game_info["image_url"],
                        "large_text": game_info["name"],
                        "small_image": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/8d/8dd66ce1b9590825cebdce861c372cc3f5187f2e_full.jpg",
                        "small_text": "Steam Deck"
                    }
                }
                
                # Adicionar state apenas se definido
                if state:
                    activity["state"] = state
                
                # Se encontrou App ID oficial, tentar usar ele
                if discord_app_id:
                    try:
                        decky.logger.info(f"Discord Lite: App ID oficial encontrado para {game_info['name']}: {discord_app_id}")
                        # Criar nova conexão RPC com o App ID oficial
                        official_rpc = DiscordRPC(discord_app_id)
                        if official_rpc.connect():
                            official_rpc.set_activity(activity)
                            
                            # Fechar conexão anterior e usar a nova
                            if hasattr(self, 'current_game_rpc') and self.current_game_rpc:
                                try:
                                    if self.current_game_rpc.socket:
                                        self.current_game_rpc.socket.close()
                                except:
                                    pass
                            
                            self.current_game_rpc = official_rpc
                            
                            # Limpar atividade do cliente principal para evitar duplicidade
                            try:
                                self.rpc.clear_activity()
                            except:
                                pass
                                
                            decky.logger.info(f"Discord Lite: Sincronizado jogo com App ID oficial: {game_info['name']}")
                        else:
                            raise Exception("Falha ao conectar RPC oficial")
                    except Exception as e:
                        decky.logger.warning(f"Discord Lite: Erro ao usar App ID oficial, usando fallback: {e}")
                        # Fallback: usar nosso App ID
                        self.rpc.set_activity(activity)
                        decky.logger.info(f"Discord Lite: Sincronizado jogo (fallback): {game_info['name']}")
                else:
                    # Usar nosso App ID (Deckord)
                    self.rpc.set_activity(activity)
                    decky.logger.info(f"Discord Lite: Sincronizado jogo: {game_info['name']}")
            
            # Se não há jogo rodando mas tinha antes
            elif not game_info and self.current_game_appid:
                self.current_game_appid = None
                self.current_game_name = None
                self.game_start_time = None
                
                # Fechar conexão do jogo se existir
                if hasattr(self, 'current_game_rpc') and self.current_game_rpc:
                    try:
                        self.current_game_rpc.close()
                        self.current_game_rpc = None
                    except:
                        pass
                
                self.rpc.clear_activity()
                decky.logger.info("Discord Lite: Jogo fechado, status limpo")
        
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao sincronizar jogo: {e}")
    
    # ==================== SETTINGS API ====================
    
    async def get_settings(self) -> dict:
        """Retorna as configurações do plugin"""
        settings = self.load_settings()
        return {
            "success": True,
            "settings": {
                "notifications_enabled": settings.get("notifications_enabled", True),
                "auto_connect": settings.get("auto_connect", False),
                "language": settings.get("language", "pt"),
                "user_volumes": settings.get("user_volumes", {}),
                "game_sync_enabled": settings.get("game_sync_enabled", True),
            }
        }
    
    async def save_settings_async(self, settings: dict) -> dict:
        """Salva as configurações do plugin"""
        try:
            self.save_settings(settings)
            
            # Se mudou game_sync_enabled
            if "game_sync_enabled" in settings:
                self.game_sync_enabled = settings["game_sync_enabled"]
                if not self.game_sync_enabled and self.rpc:
                    # Limpar status do Discord
                    self.rpc.clear_activity()
                    self.current_game_appid = None
                    self.current_game_name = None
                    self.game_start_time = None
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _main(self):
        decky.logger.info("Discord Lite: Iniciando...")
        self.load_token()
        settings = self.load_settings()
        self.selected_guild_id = settings.get("selected_guild_id")
        self.game_sync_enabled = settings.get("game_sync_enabled", True)
    
    async def _unload(self):
        decky.logger.info("Discord Lite: Descarregando...")
        self.stop_voice_polling()
        if self.rpc:
            self.rpc.disconnect()
    
    # ==================== VOICE POLLING SYSTEM ====================
    
    def start_voice_polling(self):
        """Inicia polling em background para detectar mudanças de membros"""
        if self.voice_polling_active:
            return
        
        # Inicializar previous_members com membros atuais para evitar toasts iniciais
        self.initial_sync_done = False
        if self.rpc and self.rpc.authenticated:
            try:
                self.rpc.get_selected_voice_channel()
                self.previous_members = {}
                for member in self.rpc.voice_members:
                    user_id = member.get("user_id")
                    if user_id:
                        self.previous_members[user_id] = {
                            "username": member.get("username", "Usuário"),
                            "avatar": member.get("avatar"),
                            "user_id": user_id
                        }
                decky.logger.info(f"Discord Lite: Sincronizados {len(self.previous_members)} membros iniciais")
            except Exception as e:
                decky.logger.error(f"Discord Lite: Erro ao sincronizar membros iniciais: {e}")
        
        self.initial_sync_done = True
        self.voice_polling_active = True
        self.voice_polling_thread = threading.Thread(target=self._voice_polling_loop, daemon=True)
        self.voice_polling_thread.start()
        decky.logger.info("Discord Lite: Polling de voz iniciado")
    
    def stop_voice_polling(self):
        """Para o polling em background"""
        self.voice_polling_active = False
        if self.voice_polling_thread:
            self.voice_polling_thread = None
        decky.logger.info("Discord Lite: Polling de voz parado")
    
    def _voice_polling_loop(self):
        """Loop de polling que roda em background"""
        while self.voice_polling_active:
            try:
                if self.rpc and self.rpc.authenticated:
                    self._check_voice_members_changes()
                    # Sincronizar jogo Steam com Discord
                    self.sync_game_to_discord()
            except Exception as e:
                decky.logger.error(f"Discord Lite: Erro no polling: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_voice_members_changes(self):
        """Verifica mudanças nos membros do canal de voz"""
        try:
            # Não emitir eventos se a sincronização inicial não foi concluída
            if not self.initial_sync_done:
                return
            
            self.rpc.get_selected_voice_channel()
            
            current_members = {}
            for member in self.rpc.voice_members:
                user_id = member.get("user_id")
                if user_id:
                    current_members[user_id] = {
                        "username": member.get("username", "Usuário"),
                        "avatar": member.get("avatar"),
                        "user_id": user_id
                    }
            
            # Detectar quem entrou (apenas após sync inicial)
            for user_id, info in current_members.items():
                if user_id not in self.previous_members:
                    decky.logger.info(f"Discord Lite: {info['username']} entrou no canal")
                    self.event_queue.put({
                        "type": "VOICE_JOIN",
                        "user_id": user_id,
                        "username": info["username"],
                        "avatar": info.get("avatar")
                    })
            
            # Detectar quem saiu
            for user_id, info in self.previous_members.items():
                if user_id not in current_members:
                    decky.logger.info(f"Discord Lite: {info['username']} saiu do canal")
                    self.event_queue.put({
                        "type": "VOICE_LEAVE",
                        "user_id": user_id,
                        "username": info["username"],
                        "avatar": info.get("avatar")
                    })
            
            self.previous_members = current_members
            
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao verificar membros: {e}")
    
    async def get_pending_events(self) -> dict:
        """Retorna eventos pendentes da fila (chamado pelo frontend)"""
        events = []
        try:
            while True:
                event = self.event_queue.get_nowait()
                events.append(event)
        except Empty:
            pass
        
        return {"success": True, "events": events}
    
    def _exchange_code_sync(self, code: str) -> dict:
        import urllib.request
        import urllib.parse
        import base64
        import ssl
        
        decky.logger.info("Discord Lite: Trocando código por token...")
        
        credentials = base64.b64encode(
            f"{self.CLIENT_ID}:{self.CLIENT_SECRET}".encode()
        ).decode()
        
        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code
        }).encode()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            req = urllib.request.Request(
                "https://discord.com/api/oauth2/token",
                data=data,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {credentials}",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "application/json",
                }
            )
            
            with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
                result = json.loads(resp.read().decode())
                access_token = result.get("access_token")
                
                if access_token:
                    decky.logger.info("Discord Lite: Token obtido!")
                    return {"success": True, "access_token": access_token}
                    
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro: {e}")
            return {"success": False, "message": str(e)}
        
        return {"success": False, "message": "Falha ao trocar código"}
    
    # ==================== DISCORD LAUNCHER ====================
    
    async def check_discord_installed(self) -> dict:
        """Verifica se Discord está instalado"""
        flatpak_path = os.path.expanduser("~/.var/app/com.discordapp.Discord")
        flatpak_installed = os.path.exists(flatpak_path)
        
        native_paths = ["/usr/bin/discord", "/usr/bin/Discord", os.path.expanduser("~/Discord/Discord")]
        native_installed = any(os.path.exists(p) for p in native_paths)
        
        return {
            "success": True,
            "installed": flatpak_installed or native_installed,
            "flatpak": flatpak_installed,
            "native": native_installed
        }
    
    async def launch_discord(self) -> dict:
        """Inicia o Discord"""
        try:
            flatpak_path = os.path.expanduser("~/.var/app/com.discordapp.Discord")
            if os.path.exists(flatpak_path):
                subprocess.Popen(
                    ["flatpak", "run", "com.discordapp.Discord"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return {"success": True, "message": "Discord iniciado (Flatpak)"}
            
            for path in ["/usr/bin/discord", "/usr/bin/Discord"]:
                if os.path.exists(path):
                    subprocess.Popen(
                        [path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    return {"success": True, "message": "Discord iniciado"}
            
            return {"success": False, "message": "Discord não encontrado"}
            
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro ao iniciar Discord: {e}")
            return {"success": False, "message": str(e)}
    
    async def check_discord_running(self) -> dict:
        """Verifica se Discord está rodando"""
        rpc = DiscordRPC(self.CLIENT_ID)
        ipc_path = rpc.get_ipc_path()
        return {"success": True, "running": ipc_path is not None}
    
    # ==================== AUTO AUTH ====================
    
    async def auto_auth(self) -> dict:
        decky.logger.info("Discord Lite: Iniciando auto_auth...")
        
        if self.auth_in_progress:
            return {"success": False, "authenticated": False, "message": "Autorização em andamento..."}
        
        self.auth_in_progress = True
        
        try:
            self.rpc = DiscordRPC(self.CLIENT_ID)
            
            if not self.rpc.connect():
                return {"success": False, "authenticated": False, "message": "Discord não está aberto"}
            
            if self.access_token:
                if self.rpc.authenticate(self.access_token):
                    username = self.rpc.user.get('username', 'usuário') if self.rpc.user else 'usuário'
                    # Iniciar polling após autenticação
                    self.start_voice_polling()
                    return {
                        "success": True,
                        "authenticated": True,
                        "user": self.rpc.user,
                        "message": f"Conectado como {username}"
                    }
                else:
                    self.access_token = None
            
            code = self.rpc.authorize(self.SCOPES)
            
            if not code:
                return {"success": False, "authenticated": False, "message": "Autorização não concedida"}
            
            exchange_result = self._exchange_code_sync(code)
            
            if not exchange_result.get("success"):
                return {
                    "success": False,
                    "authenticated": False,
                    "message": exchange_result.get("message", "Falha ao obter token")
                }
            
            access_token = exchange_result.get("access_token")
            
            self.rpc.disconnect()
            self.rpc = DiscordRPC(self.CLIENT_ID)
            
            if not self.rpc.connect():
                return {"success": False, "authenticated": False, "message": "Falha ao reconectar"}
            
            if self.rpc.authenticate(access_token):
                self.access_token = access_token
                self.save_token(access_token)
                username = self.rpc.user.get('username', 'usuário') if self.rpc.user else 'usuário'
                # Iniciar polling após autenticação
                self.start_voice_polling()
                return {
                    "success": True,
                    "authenticated": True,
                    "user": self.rpc.user,
                    "message": f"Conectado como {username}"
                }
            
            return {"success": False, "authenticated": False, "message": "Falha na autenticação"}
            
        except Exception as e:
            decky.logger.error(f"Discord Lite: Erro em auto_auth: {e}")
            return {"success": False, "authenticated": False, "message": str(e)}
        finally:
            self.auth_in_progress = False
    
    # ==================== STATUS & VOZ ====================
    
    async def check_status(self) -> dict:
        if not self.rpc or not self.rpc.connected:
            return {
                "success": False,
                "connected": False,
                "authenticated": False,
                "message": "Não conectado"
            }
        
        return {
            "success": True,
            "connected": True,
            "authenticated": self.rpc.authenticated,
            "user": self.rpc.user if self.rpc.authenticated else None,
            "message": "Conectado" if self.rpc.authenticated else "Não autorizado"
        }
    
    async def logout(self) -> dict:
        self.access_token = None
        
        try:
            path = self.get_token_path()
            if os.path.exists(path):
                os.remove(path)
        except:
            pass
        
        if self.rpc:
            self.rpc.authenticated = False
            self.rpc.access_token = None
        
        return {"success": True, "message": "Desconectado"}
    
    async def get_voice_state(self) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado", "authenticated": False}
        
        self.rpc.get_voice_settings()
        self.rpc.get_selected_voice_channel()
        
        # Pega quem está falando atualmente
        speaking_users = self.rpc.get_speaking_users() if hasattr(self.rpc, 'get_speaking_users') else []
        
        return {
            "success": True,
            "authenticated": True,
            "is_muted": self.rpc.is_muted,
            "is_deafened": self.rpc.is_deafened,
            "input_volume": self.rpc.input_volume,
            "output_volume": self.rpc.output_volume,
            "channel_id": self.rpc.voice_channel_id,
            "channel_name": self.rpc.voice_channel_name,
            "guild_id": self.rpc.voice_guild_id,
            "in_voice": self.rpc.voice_channel_id is not None,
            "members": self.rpc.voice_members,
            "speaking_users": speaking_users,
            "mode_type": self.rpc.mode_type,
            "noise_suppression": self.rpc.noise_suppression,
            "echo_cancellation": self.rpc.echo_cancellation,
            "automatic_gain_control": self.rpc.automatic_gain_control,
        }
    
    async def toggle_mute(self) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        self.rpc.get_voice_settings()
        new_state = not self.rpc.is_muted
        
        result = self.rpc.set_voice_settings(mute=new_state)
        if result.get("success"):
            self.rpc.is_muted = new_state
            return {"success": True, "is_muted": new_state}
        
        return {"success": False, "message": result.get("message", "Falha ao mutar")}
    
    async def toggle_deafen(self) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        self.rpc.get_voice_settings()
        new_state = not self.rpc.is_deafened
        
        result = self.rpc.set_voice_settings(deaf=new_state)
        if result.get("success"):
            self.rpc.is_deafened = new_state
            if new_state:
                self.rpc.is_muted = True
            return {"success": True, "is_deafened": new_state, "is_muted": self.rpc.is_muted}
        
        return {"success": False, "message": result.get("message", "Falha")}
    
    async def set_input_volume(self, volume: int) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        volume = max(0, min(100, volume))
        result = self.rpc.set_voice_settings(input={"volume": volume})
        if result.get("success"):
            self.rpc.input_volume = volume
            return {"success": True, "volume": volume}
        
        return {"success": False, "message": result.get("message", "Falha")}
    
    async def set_output_volume(self, volume: int) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        volume = max(0, min(200, volume))
        result = self.rpc.set_voice_settings(output={"volume": volume})
        if result.get("success"):
            self.rpc.output_volume = volume
            return {"success": True, "volume": volume}
        
        return {"success": False, "message": result.get("message", "Falha")}
    
    async def leave_voice(self) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        if self.rpc.select_voice_channel(None):
            self.rpc.voice_channel_id = None
            self.rpc.voice_channel_name = None
            return {"success": True}
        
        return {"success": False, "message": "Falha"}
    
    # ==================== SERVIDORES E CANAIS ====================
    
    async def get_guilds(self) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado", "guilds": []}
        
        self.guilds_cache = self.rpc.get_guilds()
        return {
            "success": True,
            "guilds": self.guilds_cache,
            "selected_guild_id": self.selected_guild_id
        }
    
    async def select_guild(self, guild_id: str) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        self.selected_guild_id = guild_id
        self.save_settings({"selected_guild_id": guild_id})
        
        return {"success": True, "guild_id": guild_id}
    
    async def get_voice_channels(self, guild_id: str = None) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado", "channels": []}
        
        if not guild_id:
            guild_id = self.selected_guild_id
        
        if not guild_id:
            self.rpc.get_selected_voice_channel()
            guild_id = self.rpc.voice_guild_id
        
        if not guild_id:
            return {"success": False, "message": "Selecione um servidor", "channels": []}
        
        channels = self.rpc.get_channels(guild_id)
        return {"success": True, "guild_id": guild_id, "channels": channels}
    
    async def join_voice_channel(self, channel_id: str) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        if self.rpc.select_voice_channel(channel_id, force=True):
            self.rpc.get_selected_voice_channel()
            return {
                "success": True,
                "channel_id": self.rpc.voice_channel_id,
                "channel_name": self.rpc.voice_channel_name
            }
        
        return {"success": False, "message": "Falha"}
    
    # ==================== VOLUME INDIVIDUAL ====================
    
    async def set_user_volume(self, user_id: str, volume: int) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        volume = max(0, min(200, volume))
        if self.rpc.set_user_voice_settings(user_id, volume=volume):
            return {"success": True, "user_id": user_id, "volume": volume}
        
        return {"success": False, "message": "Falha"}
    
    async def mute_user(self, user_id: str, mute: bool) -> dict:
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        if self.rpc.set_user_voice_settings(user_id, mute=mute):
            return {"success": True, "user_id": user_id, "muted": mute}
        
        return {"success": False, "message": "Falha"}
    
    # ==================== CONFIGURAÇÕES AVANÇADAS ====================
    
    async def set_voice_mode(self, mode_type: str) -> dict:
        """Define modo de voz: VOICE_ACTIVITY ou PUSH_TO_TALK"""
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        if mode_type not in ["VOICE_ACTIVITY", "PUSH_TO_TALK"]:
            return {"success": False, "message": "Modo inválido"}
        
        result = self.rpc.set_voice_settings(mode={"type": mode_type})
        if result.get("success"):
            self.rpc.mode_type = mode_type
            return {"success": True, "mode_type": mode_type}
        
        return {"success": False, "message": result.get("message", "Falha")}
    
    async def set_ptt_shortcut(self, key_type: int, key_code: int, key_name: str) -> dict:
        """Define o botão de Push-to-Talk
        key_type: 0=KEYBOARD_KEY, 1=MOUSE_BUTTON, 2=KEYBOARD_MODIFIER_KEY, 3=GAMEPAD_BUTTON
        """
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        shortcut = [{"type": key_type, "code": key_code, "name": key_name}]
        result = self.rpc.set_voice_settings(mode={
            "type": "PUSH_TO_TALK",
            "shortcut": shortcut,
            "delay": 100.0  # 100ms delay
        })
        
        if result.get("success"):
            self.rpc.mode_type = "PUSH_TO_TALK"
            return {"success": True, "shortcut": key_name}
        
        return {"success": False, "message": result.get("message", "Falha ao configurar PTT")}
    
    async def set_noise_suppression(self, enabled: bool) -> dict:
        """Ativa/desativa supressão de ruído"""
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        decky.logger.info(f"Discord Lite: Alterando noise_suppression para {enabled}")
        result = self.rpc.set_voice_settings(noise_suppression=enabled)
        decky.logger.info(f"Discord Lite: Resultado: {result}")
        
        if result.get("success"):
            self.rpc.noise_suppression = enabled
            return {"success": True, "enabled": enabled}
        
        return {"success": False, "message": result.get("message", "Falha ao alterar supressão de ruído")}
    
    async def set_echo_cancellation(self, enabled: bool) -> dict:
        """Ativa/desativa cancelamento de eco"""
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        result = self.rpc.set_voice_settings(echo_cancellation=enabled)
        if result.get("success"):
            self.rpc.echo_cancellation = enabled
            return {"success": True, "enabled": enabled}
        
        return {"success": False, "message": result.get("message", "Falha")}
    
    async def set_automatic_gain_control(self, enabled: bool) -> dict:
        """Ativa/desativa controle automático de ganho"""
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        result = self.rpc.set_voice_settings(automatic_gain_control=enabled)
        if result.get("success"):
            self.rpc.automatic_gain_control = enabled
            return {"success": True, "enabled": enabled}
        
        return {"success": False, "message": result.get("message", "Falha")}
    
    # ==================== MEMBER TRACKING ====================
    
    async def get_voice_members_diff(self) -> dict:
        """Retorna membros que entraram/saíram desde a última verificação"""
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        self.rpc.get_selected_voice_channel()
        current_members = {}
        
        for member in self.rpc.voice_members:
            user_id = member.get("user_id")
            if user_id:
                current_members[user_id] = {
                    "username": member.get("username", "Usuário"),
                    "avatar": member.get("avatar"),
                    "user_id": user_id
                }
        
        # Calcular diferenças
        current_set = set(current_members.keys())
        previous_set = set(self.previous_members.keys())
        
        joined_ids = current_set - previous_set
        left_ids = previous_set - current_set
        
        joined_info = [current_members[uid] for uid in joined_ids]
        left_info = [self.previous_members[uid] for uid in left_ids]
        
        # Atualizar cache
        self.previous_members = current_members
        
        return {
            "success": True,
            "joined": joined_info,
            "left": left_info,
            "current_count": len(current_members)
        }
    
    async def sync_full_state(self) -> dict:
        """Sincroniza estado completo incluindo servidor atual"""
        if not self.rpc or not self.rpc.authenticated:
            return {"success": False, "message": "Não autenticado"}
        
        # Obter configurações de voz
        self.rpc.get_voice_settings()
        
        # Obter canal de voz atual
        self.rpc.get_selected_voice_channel()
        
        # Se estiver em um canal, atualizar o servidor selecionado
        if self.rpc.voice_guild_id:
            self.selected_guild_id = self.rpc.voice_guild_id
            self.save_settings({"selected_guild_id": self.rpc.voice_guild_id})
        
        # Atualizar cache de membros (como dict)
        self.previous_members = {}
        for m in self.rpc.voice_members:
            uid = m.get("user_id")
            if uid:
                self.previous_members[uid] = {
                    "username": m.get("username", "Usuário"),
                    "avatar": m.get("avatar"),
                    "user_id": uid
                }
        
        # Obter lista de servidores
        self.guilds_cache = self.rpc.get_guilds()
        
        return {
            "success": True,
            "authenticated": True,
            "is_muted": self.rpc.is_muted,
            "is_deafened": self.rpc.is_deafened,
            "input_volume": self.rpc.input_volume,
            "output_volume": self.rpc.output_volume,
            "channel_id": self.rpc.voice_channel_id,
            "channel_name": self.rpc.voice_channel_name,
            "guild_id": self.rpc.voice_guild_id,
            "in_voice": self.rpc.voice_channel_id is not None,
            "members": self.rpc.voice_members,
            "mode_type": self.rpc.mode_type,
            "noise_suppression": self.rpc.noise_suppression,
            "echo_cancellation": self.rpc.echo_cancellation,
            "automatic_gain_control": self.rpc.automatic_gain_control,
            "guilds": self.guilds_cache,
            "selected_guild_id": self.selected_guild_id,
            "game_sync_enabled": self.game_sync_enabled,
            "current_game": {
                "appid": self.current_game_appid,
                "name": self.current_game_name
            } if self.current_game_appid else None,
        }

