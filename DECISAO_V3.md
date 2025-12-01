# 🎯 Decisão de Estratégia V3

**Criado**: 2025-12-01
**Decisão Necessária**: Como estruturar desenvolvimento da V3

---

## 🤔 Opções Avaliadas

### Opção 1: Novo Repositório (SUA PROPOSTA)
```
AgenteV2/         (v2 - produção)
AgenteV3/         (v3 - desenvolvimento)
```

**Prós**:
- ✅ Isolamento completo
- ✅ Sem risco de quebrar v2
- ✅ Liberdade total para experimentar

**Contras**:
- ❌ Duplicação de código/histórico
- ❌ Difícil sincronizar fixes v2 → v3
- ❌ Dois .env, dois setups, duas configs
- ❌ Perda de contexto git (PRs, issues, history)
- ❌ Complica rollout gradual (v2+v3 paralelo)

---

### Opção 2: Branch no Mesmo Repo (RECOMENDAÇÃO)
```
main              (v2 - produção)
  ↓
v3-mvp            (v3 - desenvolvimento)
  ↓
feature/json-compactor
feature/auto-apply
```

**Prós**:
- ✅ Histórico git preservado
- ✅ Fácil cherry-pick de fixes v2 → v3
- ✅ Um único .env, setup unificado
- ✅ PRs comparáveis (v2 vs v3)
- ✅ Rollout gradual simples (merge quando pronto)
- ✅ Menos overhead operacional

**Contras**:
- ⚠️ Cuidado para não quebrar main (mas temos branch)
- ⚠️ Imports podem colidir (mas resolvível com namespacing)

---

### Opção 3: Monorepo com Workspaces
```
AgenteV2/
├── packages/
│   ├── agent-v2/
│   └── agent-v3/
```

**Prós**:
- ✅ Isolamento + compartilhamento seletivo
- ✅ Código comum reusável

**Contras**:
- ❌ Complexidade de setup (lerna/npm workspaces)
- ❌ Overhead desnecessário para projeto Python simples
- ❌ Não é padrão Python

---

## 🎯 Recomendação Final: **OPÇÃO 2 - Branch no Mesmo Repo**

### Por quê?
1. **Simplicidade**: Menos overhead, foco no código
2. **Flexibilidade**: Fácil mover código v2 → v3 quando necessário
3. **Git Flow padrão**: Usado por milhões de projetos
4. **Rollout gradual**: v2 (stable) + v3 (alpha) coexistindo

### Como implementar?

#### Passo 1: Criar Branch V3
```bash
cd "C:\Users\daanm\AgenteV2"
git checkout -b v3-mvp
```

#### Passo 2: Estrutura de Código V3
```
src/
├── agent_v2/         # V2 - Produção (não tocar)
│   ├── pipeline.py
│   ├── llm_client.py
│   └── ...
│
├── agent_v3/         # V3 - Novo código aqui
│   ├── __init__.py
│   ├── pipeline.py   # Orquestrador v3
│   ├── json_compactor/
│   ├── applicator/
│   ├── validator/
│   └── ...
│
├── cli/
│   ├── run_qa_cli.py      # V2 CLI (existente)
│   └── run_qa_v3_cli.py   # V3 CLI (novo)
```

#### Passo 3: Namespacing Claro
```python
# V2 (produção - não mexer)
from agent_v2.pipeline import analyze

# V3 (desenvolvimento - novo)
from agent_v3.pipeline import analyze_and_fix
```

#### Passo 4: Workflow Git
```bash
# Desenvolvimento v3
git checkout v3-mvp
# ... fazer mudanças ...
git add .
git commit -m "feat(v3): implementa JSONCompactor"
git push origin v3-mvp

# Merge de hotfix v2 → v3 (se necessário)
git checkout v3-mvp
git merge main  # Traz fixes de v2 para v3

# Quando v3 estiver pronto
git checkout main
git merge v3-mvp  # Traz v3 para produção
git tag v3.0.0-alpha
```

---

## 📅 Cronograma com Branch Strategy

### Fase 1: Setup (HOJE)
- [ ] Criar branch `v3-mvp`
- [ ] Criar estrutura `src/agent_v3/`
- [ ] Atualizar .gitignore se necessário
- [ ] Commit inicial: "feat(v3): setup estrutura base"

### Fase 2: Desenvolvimento (DIAS 1-13)
- [ ] Trabalhar apenas em branch `v3-mvp`
- [ ] Commits frequentes
- [ ] Se houver hotfix urgente em v2:
  - Fazer em `main`
  - Merge `main` → `v3-mvp` para trazer fix

### Fase 3: Review e Merge (DIA 14)
- [ ] Apresentação para stakeholders
- [ ] Se aprovado:
  - PR `v3-mvp` → `main` (review completo)
  - Merge após aprovação
  - Tag `v3.0.0-alpha`
  - Deploy gradual (v2+v3 coexistindo)

---

## ⚠️ Se Você Ainda Preferir Novo Repo

Se realmente quiser novo repositório, aqui está como fazer:

```bash
# 1. Clonar v2 como base
git clone C:\Users\daanm\AgenteV2 C:\Users\daanm\AgenteV3
cd C:\Users\daanm\AgenteV3

# 2. Limpar histórico (se quiser começar do zero)
rm -rf .git
git init
git add .
git commit -m "Initial commit - V3 based on V2"

# 3. Criar repo remoto
# (no GitHub/GitLab)

# 4. Push
git remote add origin <URL_NOVO_REPO>
git push -u origin main
```

**Mas ainda recomendo branch por ser mais prático.**

---

## 🎯 Decisão Necessária AGORA

**Escolha UMA das opções abaixo:**

### A) Branch no Mesmo Repo (RECOMENDADO) ✅
```bash
cd "C:\Users\daanm\AgenteV2"
git checkout -b v3-mvp
mkdir -p src/agent_v3
```

### B) Novo Repositório (SUA PROPOSTA)
```bash
# Copiar v2 para novo diretório
cp -r "C:\Users\daanm\AgenteV2" "C:\Users\daanm\AgenteV3"
cd "C:\Users\daanm\AgenteV3"
# ... setup git ...
```

---

## 💡 Minha Sugestão Final

**COMECE COM BRANCH (Opção A)**

Por quê?
- Você pode sempre criar repo separado depois se precisar
- Começar com branch é reversível
- Começar com repo separado é mais difícil de voltar atrás
- MVP em 2 semanas → simplicidade é crítica

**Se após 2 semanas quiser separar:**
- Sempre pode criar novo repo e copiar código v3
- Mas mantenha v2 no repo original para facilitar manutenção

---

**Qual sua decisão?**
