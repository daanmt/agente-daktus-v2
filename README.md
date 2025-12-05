# 🔍 Agente Daktus | QA

> Sistema de validação e correção automatizada de protocolos clínicos usando IA

**Versão Atual**: 3.0-beta  
**Status**: Sistema de Aprendizado Contínuo Ativo  
**Última Atualização**: 2025-12-05

---

## 🎯 O Que Faz

Valida protocolos clínicos (JSON) contra playbooks médicos (texto/PDF) para garantir:

- ✅ Consistência da lógica clínica
- ✅ Cobertura completa de sintomas
- ✅ Caminhos diagnósticos apropriados
- ✅ Recomendações baseadas em evidências
- ✅ Identificação de gaps e oportunidades de melhoria
- ✅ **Correção automatizada** com feedback loop

**Entrada**: Protocolo clínico (JSON) + Playbook médico (Markdown/PDF)  
**Saída**: Relatório de validação + Sugestões priorizadas + Protocolo corrigido (opcional)

---

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar OpenRouter

Crie um arquivo `.env` na raiz:

```env
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
```

**Obter chave**: https://openrouter.ai/keys

### 3. Executar

```bash
# CLI Interativa V3 (recomendado)
python run_v3_cli.py

# CLI Standard
python run_qa_cli.py
```

---

## ⚙️ Funcionalidades Principais

### 📊 Análise Expandida
- **20-50 sugestões** por análise (vs 5-15 anteriormente)
- Cada sugestão com **scores de impacto** (Segurança 0-10, Economia L/M/A)
- **Rastreabilidade completa**: cada sugestão linkada à evidência do playbook
- **Estimativa de custo** para aplicar cada sugestão

### 🔄 Human-in-the-Loop
- Usuário revisa cada sugestão: Relevante | Irrelevante | Sair
- Sistema **detecta padrões** de erro e acerto
- **Aprendizado contínuo** via `memory_qa.md`
- Sugestões irrelevantes são filtradas em análises futuras

### 🛡️ Restrição ao Playbook
- **Playbook como única fonte de verdade**
- Validação multi-camada contra hallucinations
- 95%+ das sugestões verificáveis no playbook

### 🔧 Reconstrução Inteligente
- Aplica **apenas sugestões aprovadas** pelo usuário
- Versionamento semântico automático (MAJOR.MINOR.PATCH)
- Changelog documentado em cada nó modificado

---

## 📁 Estrutura do Projeto

```
AgenteV2/
├── src/
│   ├── agent/              # Módulos principais
│   │   ├── analysis/       # Análise expandida
│   │   ├── feedback/       # Sistema de aprendizado
│   │   ├── applicator/     # Reconstrução de protocolos
│   │   └── cost_control/   # Controle de custos
│   ├── agent_v3/           # CLI interativa avançada
│   └── cli/                # CLI standard
├── models_json/            # Protocolos e playbooks
├── reports/                # Relatórios gerados
├── memory_qa.md            # Memória de aprendizado
└── docs/                   # Documentação
```

---

## 🤖 Modelos Suportados

**Recomendados:**
- `x-ai/grok-4.1-fast:free` ⭐ (gratuito, contexto 2M tokens)
- `google/gemini-2.5-flash-preview-09-2025` (baixo custo)
- `anthropic/claude-sonnet-4.5` (alta qualidade)

**Outros:**
- `x-ai/grok-4.1-fast` ($0.20/$0.50 por MTok, contexto 2M)
- `google/gemini-2.5-flash`, `google/gemini-2.5-pro`
- `anthropic/claude-opus-4.5`

---

## 📊 Performance

| Métrica | Valor |
|---------|-------|
| Sugestões por análise | 20-50 |
| Latência típica | 30-90s |
| Custo por análise | $0.00-$0.50 |
| Taxa de sucesso | >95% |
| Verificabilidade playbook | >95% |

---

## 🔧 Solução de Problemas

### "API key não configurada"
```bash
# Verifique o .env
cat .env
# Deve conter: OPENROUTER_API_KEY=sk-or-v1-...
```

### "Nenhum arquivo de protocolo encontrado"
Adicione arquivos JSON em `models_json/`

### "Playbook muito grande"
Use modelos com contexto grande (Grok 4.1, Gemini 2.5)

---

## 📚 Documentação

| Arquivo | Descrição |
|---------|-----------|
| `README.md` | Este arquivo - visão geral e uso |
| `docs/roadmap.md` | Roadmap de desenvolvimento |
| `docs/dev_history.md` | Histórico de mudanças |
| `memory_qa.md` | Memória de aprendizado do agente |

---

## 🎯 Fluxo de Trabalho Típico

```
1. Selecionar protocolo JSON
       ↓
2. Selecionar playbook (opcional)
       ↓
3. Executar análise expandida
       ↓
4. Revisar sugestões (feedback)
       ↓
5. Agente aprende com feedback
       ↓
6. Reconstruir protocolo (opcional)
       ↓
7. Protocolo corrigido versionado
```

---

## 🔗 Links Úteis

- **OpenRouter**: https://openrouter.ai
- **Chaves de API**: https://openrouter.ai/keys
- **Catálogo de Modelos**: https://openrouter.ai/models

---

**Para o roadmap detalhado, veja [`docs/roadmap.md`](docs/roadmap.md)**  
**Para o histórico de desenvolvimento, veja [`docs/dev_history.md`](docs/dev_history.md)**
