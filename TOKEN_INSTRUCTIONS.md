# Como obter um GitHub Token para criar releases automaticamente

## Passo a passo:

1. **Acesse o GitHub:**
   - Vá para https://github.com/settings/tokens

2. **Gere um novo token:**
   - Clique em "Generate new token" → "Generate new token (classic)"

3. **Configure o token:**
   - **Note**: `Discord-Lite Release Token`
   - **Expiration**: Escolha a validade (recomendado: 90 days)
   - **Scopes necessários:**
     - ✅ `repo` (Full control of private repositories)
       - Isso inclui: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`

4. **Gere e copie o token:**
   - Clique em "Generate token"
   - **⚠️ IMPORTANTE**: Copie o token AGORA! Você não poderá vê-lo novamente.

5. **Use o token:**
   ```powershell
   # Execute o script com o token
   .\create-release.ps1 -Token "ghp_seu_token_aqui"
   ```

## Alternativa: Salvar token como variável de ambiente (opcional)

Se quiser evitar digitar o token toda vez:

```powershell
# Temporário (apenas para a sessão atual)
$env:GITHUB_TOKEN = "ghp_seu_token_aqui"
.\create-release.ps1 -Token $env:GITHUB_TOKEN

# Permanente (Windows)
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_seu_token_aqui', 'User')
```

⚠️ **NUNCA** commite o token no Git! Ele já está protegido no `.gitignore`.

## Exemplo de uso completo:

```powershell
# Criar release v1.0.0
.\create-release.ps1 -Token "ghp_abc123..."

# Criar release com versão customizada
.\create-release.ps1 -Token "ghp_abc123..." -Version "v1.0.1"

# Customizar repositório
.\create-release.ps1 -Token "ghp_abc123..." -RepoOwner "seuusuario" -RepoName "seu-repo"
```

## O que o script faz:

1. ✅ Verifica se o arquivo zip existe (cria se não existir)
2. ✅ Cria o release no GitHub com descrição completa
3. ✅ Faz upload do arquivo zip automaticamente
4. ✅ Retorna a URL do release criado

## Segurança do token:

- O token dá acesso aos seus repositórios
- Mantenha-o seguro e privado
- Se comprometido, revogue-o imediatamente em https://github.com/settings/tokens
- O `.gitignore` já está configurado para ignorar arquivos com tokens
