# Discord Lite for Steam Deck 🎮💬

<div align="center">

![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Steam Deck](https://img.shields.io/badge/Steam%20Deck-1B2838?style=for-the-badge&logo=steam&logoColor=white)
![Decky Loader](https://img.shields.io/badge/Decky%20Loader-Plugin-orange?style=for-the-badge)
![Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-5A67D8?style=for-the-badge&logo=anthropic&logoColor=white)

**A lightweight Discord voice chat integration for Steam Deck**

_Control your Discord voice calls directly from the Quick Access Menu_

[English](#english) | [Português](#português)

</div>

---

## English

### ✨ Features

| Feature                    | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| 🎤 **Voice Chat Controls** | Join/leave voice channels, mute/deafen yourself                          |
| 📢 **Channel Browsing**    | Browse servers, channels, and see online members                         |
| 🔊 **Volume Control**      | Per-user volume adjustment with memory                                   |
| ⏱️ **Call Timer**          | See how long you've been in the call                                     |
| 🎮 **Game Activity**       | Automatically updates Discord status with the Steam game you are playing |
| 🔔 **Notification Toggle** | Disable notifications during games                                       |
| 🔗 **Auto-Connect**        | Automatically connect to Discord on startup                              |
| 🌐 **Multi-Language**      | English and Portuguese support                                           |
| 🎨 **Discord Theme**       | Beautiful Discord-inspired UI                                            |

### 🆕 What's New (v1.2.1)

| Update                          | Description                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------ |
| 🔐 **PKCE OAuth2**              | Secure authentication without client_secret - enhanced security                                  |
| 🔊 **Improved Volume Control**  | Fixed self-user volume control (redirects to output volume when adjusting your own audio)        |
| 🎮 **Enhanced Game Sync**       | Better Discord Rich Presence integration with Steam games - smarter caching and polling          |
| ⚡ **Discord RPC Improvements** | More reliable IPC connection, better error handling, and improved socket path detection          |
| 🎨 **UI Tweaks**                | Refined user interface elements for better usability and visual consistency                      |
| 🛠️ **Build & Deploy Refactor** | Streamlined deployment process for both Windows (PowerShell) and Linux/Mac (Bash) environments |

### 📸 Screenshots

<details>
<summary>Click to view screenshots</summary>

_Screenshots coming soon!_

</details>

### 📋 Requirements

- Steam Deck with [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) installed
- Discord desktop app installed on the Deck (via Flatpak recommended)
- Discord must be running in the background

### 🚀 Installation

#### From Decky Plugin Store (Recommended)

1. Open the Quick Access Menu on your Steam Deck
2. Navigate to the Decky plugin tab (🔌)
3. Open the Plugin Store
4. Search for "Discord Lite"
5. Click Install

#### Manual Installation

1. Download the latest release from [Releases](../../releases)
2. Extract to `~/homebrew/plugins/`
3. Restart Decky Loader

### 📖 Usage

1. **Start Discord** - Open Discord on your Steam Deck (either desktop mode or via gaming mode)
2. **Open Plugin** - Access Discord Lite from the Quick Access Menu (... button)
3. **Connect** - Click "Connect to Discord" to establish the connection
4. **Browse & Join** - Navigate through your servers and join voice channels
5. **Control** - Adjust volumes, mute yourself, and manage your voice settings

### ⚙️ Settings

| Setting           | Description                                     |
| ----------------- | ----------------------------------------------- |
| **Notifications** | Toggle toast notifications for voice events     |
| **Auto-Connect**  | Automatically connect when the plugin loads     |
| **Language**      | Choose between English (EN) and Portuguese (PT) |

### 🔧 Troubleshooting

<details>
<summary>Discord not connecting?</summary>

1. Make sure Discord is running on your Steam Deck
2. Discord must be the desktop version (not web)
3. Try restarting Discord and the plugin
4. Check if another application is using Discord RPC

</details>

<details>
<summary>Voice channel not showing members?</summary>

1. Wait a few seconds after joining - data may take time to sync
2. Check if you have permission to view members in that channel
3. Try leaving and rejoining the channel

</details>

---

## Português

### ✨ Funcionalidades

| Funcionalidade                | Descrição                                                           |
| ----------------------------- | ------------------------------------------------------------------- |
| 🎤 **Controles de Voz**       | Entrar/sair de canais, mutar/ensurdecer                             |
| 📢 **Navegação de Canais**    | Navegar servidores, canais e ver membros online                     |
| 🔊 **Controle de Volume**     | Ajuste de volume por usuário com memória                            |
| ⏱️ **Tempo na Call**          | Veja quanto tempo você está na chamada                              |
| 🎮 **Atividade de Jogo**      | Atualiza automaticamente o status do Discord com o jogo Steam atual |
| 🔔 **Toggle de Notificações** | Desative notificações durante jogos                                 |
| 🔗 **Auto-Conectar**          | Conecte automaticamente ao Discord ao iniciar                       |
| 🌐 **Multi-Idioma**           | Suporte a Inglês e Português                                        |
| 🎨 **Tema Discord**           | Interface bonita inspirada no Discord                               |

### 🆕 Novidades (v1.2.1)

| Atualização                      | Descrição                                                                                           |
| -------------------------------- | --------------------------------------------------------------------------------------------------- |
| 🔐 **OAuth2 PKCE**               | Autenticação segura sem client_secret - segurança aprimorada                                        |
| 🔊 **Controle de Volume Melhorado** | Correção do controle de volume próprio (redireciona para volume de saída ao ajustar seu próprio áudio) |
| 🎮 **Sincronização de Jogo Aprimorada** | Melhor integração Discord Rich Presence com jogos Steam - cache e polling mais inteligentes    |
| ⚡ **Melhorias no Discord RPC**  | Conexão IPC mais confiável, melhor tratamento de erros e detecção de caminhos de socket aprimorada |
| 🎨 **Ajustes de Interface**      | Elementos de interface refinados para melhor usabilidade e consistência visual                     |
| 🛠️ **Refatoração Build & Deploy** | Processo de deploy otimizado para ambientes Windows (PowerShell) e Linux/Mac (Bash)              |

### 📸 Capturas de Tela

<details>
<summary>Clique para ver capturas de tela</summary>

_Capturas de tela em breve!_

</details>

### 📋 Requisitos

- Steam Deck com [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) instalado
- App Discord instalado no Deck (Flatpak recomendado)
- Discord deve estar rodando em segundo plano

### 🚀 Instalação

#### Da Loja de Plugins Decky (Recomendado)

1. Abra o Menu de Acesso Rápido no Steam Deck
2. Navegue até a aba de plugins Decky (🔌)
3. Abra a Loja de Plugins
4. Pesquise por "Discord Lite"
5. Clique em Instalar

#### Instalação Manual

1. Baixe a última versão de [Releases](../../releases)
2. Extraia para `~/homebrew/plugins/`
3. Reinicie o Decky Loader

### 📖 Uso

1. **Inicie o Discord** - Abra o Discord no Steam Deck
2. **Abra o Plugin** - Acesse o Discord Lite pelo Menu de Acesso Rápido (botão ...)
3. **Conecte** - Clique em "Conectar ao Discord"
4. **Navegue & Entre** - Navegue pelos servidores e entre em canais de voz
5. **Controle** - Ajuste volumes, mute-se e gerencie suas configurações de voz

### ⚙️ Configurações

| Configuração      | Descrição                                         |
| ----------------- | ------------------------------------------------- |
| **Notificações**  | Ativar/desativar notificações de eventos de voz   |
| **Auto-Conectar** | Conectar automaticamente quando o plugin carregar |
| **Idioma**        | Escolha entre Inglês (EN) e Português (PT)        |

### 🔧 Solução de Problemas

<details>
<summary>Discord não conecta?</summary>

1. Certifique-se de que o Discord está rodando no Steam Deck
2. Deve ser a versão desktop (não web)
3. Tente reiniciar o Discord e o plugin
4. Verifique se outro aplicativo está usando o Discord RPC

</details>

<details>
<summary>Canal de voz não mostra membros?</summary>

1. Aguarde alguns segundos após entrar - dados podem demorar a sincronizar
2. Verifique se você tem permissão para ver membros naquele canal
3. Tente sair e entrar novamente no canal

</details>

---

## 🛠️ Development

### Dependencies

- Node.js v16.14+
- pnpm v9
- Docker (for backend builds)

### Building

```bash
# Install dependencies
pnpm i

# Build frontend
pnpm run build

# Deploy to Steam Deck (configure .vscode/settings.json first)
# Windows:
.\deploy.ps1

# Linux/Mac:
./deploy.sh
```

### Project Structure

```
Discord-Lite/
├── src/
│   └── index.tsx       # Main frontend code
├── lib/
│   └── pypresence/     # Discord RPC library
├── main.py             # Python backend
├── plugin.json         # Plugin metadata
├── CLAUDE.md           # Claude Code project instructions
└── package.json        # Node dependencies
```

### Built with Claude Code

This project was developed with the assistance of [Claude Code](https://claude.ai/code) (Opus 4.5), leveraging AI-assisted development for:

- **Architecture Design**: RPC communication patterns, OAuth2 PKCE implementation
- **Code Optimization**: Volume control logic, game sync caching, IPC socket detection
- **Bug Fixes**: Self-user volume control, authentication flow improvements
- **Documentation**: Comprehensive inline comments and project documentation (CLAUDE.md)
- **Testing & Debugging**: Error handling, edge case detection, and reliability improvements

Claude Code helped streamline development while maintaining code quality and security best practices.

---

## � Security & Privacy

This plugin uses Discord's official OAuth2 RPC API to communicate with your Discord client. Here's what you should know:

- **Local Authentication**: All OAuth2 authentication happens locally between this plugin and your Discord desktop client
- **No External Servers**: Your tokens are stored locally on your Steam Deck and never sent to third-party servers
- **Limited Scope**: The plugin only requests permissions for voice control (no access to messages, friends, etc.)
- **Open Source**: You can review all the code to verify exactly what the plugin does

The OAuth2 credentials included in this plugin are for the Discord application registration only and cannot be used to access your account without your explicit authorization through Discord's popup.

---

## �📄 License

This project is licensed under the BSD-3-Clause License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) - Plugin framework
- [pypresence](https://github.com/qwertyquerty/pypresence) - Discord RPC library
- Discord - For the inspiration and API
- [Claude Code](https://claude.ai/code) by Anthropic - AI-assisted development with Claude Opus 4.5

---

<div align="center">

Made with ❤️ for the Steam Deck community

</div>
