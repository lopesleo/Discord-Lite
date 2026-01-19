# Manual de Deploy - Discord Lite

## Metodo 1: Script Automatico (Recomendado)

### Criar e testar o zip:

```powershell
.\create-zip.ps1
```

### Deploy no Steam Deck:

```powershell
.\deploy.ps1
```

## Metodo 2: Manual

### 1. Criar o zip:

```powershell
.\create-zip.ps1 -Version "v1.0.0"
```

### 2. Copiar para o Steam Deck:

```powershell
scp Discord-Lite-v1.0.0.zip deck@<IP_DO_DECK>:/home/deck/
```

### 3. Instalar no Steam Deck:

```bash
# Conectar via SSH
ssh deck@<IP_DO_DECK>

# Remover versão antiga
sudo rm -rf ~/homebrew/plugins/DiscordLite/*

# Extrair novo zip
sudo unzip -o ~/Discord-Lite-v1.0.0.zip -d ~/homebrew/plugins/DiscordLite/

# Corrigir permissões
sudo chown -R deck:deck ~/homebrew/plugins/DiscordLite/
sudo chmod -R 755 ~/homebrew/plugins/DiscordLite/

# Reiniciar Decky Loader
sudo systemctl restart plugin_loader

# Limpar
rm ~/Discord-Lite-v1.0.0.zip
```

## Metodo 3: Release no GitHub (Automatico)

### Pré-requisitos:

1. Obter GitHub Token em: https://github.com/settings/tokens
2. Selecionar scope: `repo`

### Criar release:

```powershell
.\create-release.ps1 -Token "ghp_seu_token_aqui"
```

Isso vai:

- ✅ Criar o zip automaticamente
- ✅ Criar o release no GitHub
- ✅ Fazer upload do zip
- ✅ Publicar com descrição completa

### Versão customizada:

```powershell
.\create-release.ps1 -Token "ghp_token" -Version "v1.0.1"
```

## Verificacao

### No Steam Deck:

```bash
# Verificar arquivos instalados
ls -la ~/homebrew/plugins/DiscordLite/

# Ver logs do plugin
journalctl -u plugin_loader -f | grep "Discord Lite"

# Status do Decky
sudo systemctl status plugin_loader
```

### Arquivos essenciais:

- ✅ main.py (backend Python)
- ✅ plugin.json (metadados)
- ✅ dist/index.js (frontend)
- ✅ lib/pypresence/ (dependências)

## Troubleshooting

### Plugin não aparece no Decky:

1. Verificar se todos os arquivos foram extraídos
2. Verificar permissões (devem ser `deck:deck`)
3. Verificar logs: `journalctl -u plugin_loader -n 50`
4. Reiniciar Decky: `sudo systemctl restart plugin_loader`

### Erro de permissão:

```bash
sudo chown -R deck:deck ~/homebrew/plugins/DiscordLite/
sudo chmod -R 755 ~/homebrew/plugins/DiscordLite/
```

### Erro de import:

- Verificar se a pasta `lib/` foi extraída corretamente
- Verificar se `lib/pypresence/` existe e tem todos os arquivos

## Estrutura do Plugin

```
DiscordLite/
├── main.py              # Backend Python
├── plugin.json          # Metadados do plugin
├── package.json         # Dependências Node
├── README.md
├── LICENSE
├── dist/
│   ├── index.js         # Frontend compilado
│   └── index.js.map
├── defaults/
│   └── defaults.txt     # Configurações padrão
├── lib/
│   └── pypresence/      # Biblioteca Discord RPC
└── assets/
    └── logo.png         # Logo do plugin
```

## Notas Importantes

1. **Sempre criar zip limpo**: Use `.\create-zip.ps1` para garantir que não há `__pycache__` ou arquivos temporários

2. **Permissões**: Arquivos devem pertencer a `deck:deck` e ter permissão `755`

3. **Reiniciar Decky**: Sempre reinicie após instalar: `sudo systemctl restart plugin_loader`

4. **Backups**: Faça backup antes de atualizar: `cp -r ~/homebrew/plugins/DiscordLite ~/DiscordLite.bak`
