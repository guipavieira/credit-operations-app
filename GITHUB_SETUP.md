# Guia de Upload para GitHub

## Passo a Passo Completo

### 1. Instalar o Git (se ainda não tiver)
Baixe e instale o Git do site oficial: https://git-scm.com/download/win

Após a instalação, abra um novo terminal PowerShell e verifique:
```powershell
git --version
```

### 2. Configurar o Git (primeira vez)
```powershell
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

### 3. Inicializar o Repositório Local
No diretório do projeto, execute:
```powershell
git init
git add .
git commit -m "Commit inicial: estrutura completa da aplicação"
```

### 4. Criar Repositório PRIVADO no GitHub

#### Opção A: Via Interface Web (Recomendado)
1. Acesse: https://github.com/new
2. Preencha:
   - **Repository name**: credit-operations-app (ou outro nome)
   - **Description**: Aplicação de Operações de Crédito - PMAE
   - **Visibility**: 🔒 **PRIVATE** (importante!)
3. NÃO marque "Initialize with README" (já temos um)
4. Clique em "Create repository"

#### Opção B: Via GitHub CLI (se instalado)
```powershell
gh repo create credit-operations-app --private --source=. --remote=origin
```

### 5. Conectar e Enviar ao GitHub

Após criar o repositório no GitHub, você verá uma URL como:
`https://github.com/seu-usuario/credit-operations-app.git`

Execute os comandos:
```powershell
# Adicionar o repositório remoto
git remote add origin https://github.com/seu-usuario/credit-operations-app.git

# Renomear branch para main (se necessário)
git branch -M main

# Enviar o código para o GitHub
git push -u origin main
```

### 6. Adicionar Colaboradores (Acesso Restrito)

1. Vá para: `https://github.com/seu-usuario/credit-operations-app/settings/access`
2. Clique em "Add people"
3. Digite o username ou email do GitHub do colaborador
4. Escolha a permissão:
   - **Read**: Apenas visualizar
   - **Write**: Visualizar e contribuir
   - **Admin**: Controle total
5. Clique em "Add [nome] to this repository"

### 7. Comandos Git Úteis para o Dia a Dia

```powershell
# Ver status dos arquivos
git status

# Adicionar todos os arquivos modificados
git add .

# Commit com mensagem
git commit -m "Descrição das alterações"

# Enviar alterações para o GitHub
git push

# Baixar alterações do GitHub
git pull

# Ver histórico de commits
git log --oneline

# Criar uma nova branch
git checkout -b nome-da-branch

# Alternar entre branches
git checkout main
```

### 8. Fluxo de Trabalho Recomendado

Para cada nova funcionalidade:
```powershell
# 1. Criar branch para a feature
git checkout -b feature/nova-funcionalidade

# 2. Fazer alterações e commits
git add .
git commit -m "Implementa nova funcionalidade"

# 3. Enviar branch para o GitHub
git push -u origin feature/nova-funcionalidade

# 4. No GitHub, criar Pull Request
# 5. Após revisão, fazer merge para main
```

### 9. Checklist de Segurança

✅ Repositório configurado como PRIVATE
✅ Arquivo .gitignore criado
✅ Arquivo .env NÃO está sendo versionado
✅ Apenas .env.example está no repositório
✅ Colaboradores adicionados individualmente
✅ Sem credenciais ou chaves no código

### 10. Resolução de Problemas Comuns

**Erro: "git não é reconhecido"**
- Instale o Git e reinicie o terminal

**Erro ao fazer push: "Permission denied"**
- Configure suas credenciais do GitHub
- Use Personal Access Token em vez de senha
- Gere em: https://github.com/settings/tokens

**Erro: "remote origin already exists"**
```powershell
git remote remove origin
git remote add origin https://github.com/seu-usuario/credit-operations-app.git
```

**Desfazer último commit (local)**
```powershell
git reset --soft HEAD~1
```

### 11. Recursos Adicionais

- Documentação Git: https://git-scm.com/doc
- GitHub Docs: https://docs.github.com
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf

---
**Importante:** Mantenha sempre o repositório PRIVADO e compartilhe acesso apenas com pessoas autorizadas!
