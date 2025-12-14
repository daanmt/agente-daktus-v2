# Problema: Erros de Validação de Lógica Condicional

**Versão Afetada:** v3.2.0  
**Data:** 2025-12-14  
**Status:** PARCIALMENTE RESOLVIDO - Sistema estável com avisos

---

## 📋 Resumo Executivo

Durante a reconstrução de protocolos, o LLM (Gemini 2.5 Flash Lite) **continua gerando chamadas de função em expressões condicionais** apesar de instruções explícitas proibindo isso. O sistema agora:

- ✅ Aplica todas as mudanças com sucesso (100% taxa de aplicação)
- ⚠️ Gera 4-5 erros de validação de lógica condicional por reconstrução
- 🧠 Aprende automaticamente com os erros (salva lições na memória)
- 🧹 Sanitiza PARCIALMENTE as funções inválidas

**O protocolo reconstruído funciona, mas requer revisão manual das condicionais.**

---

## 🔍 Análise do Problema

### O Que O LLM Está Gerando (ERRADO)

```python
# Exemplo de expressão inválida gerada pelo LLM:
'exames_lab' in exames_avaliacao and not selected_only(exames_avaliacao, 'exames_lab')
```

**Funções inválidas detectadas:**
- `selected_only(var, value)` - NÃO EXISTE no Daktus Studio
- `contains(var, value)` - NÃO EXISTE
- `isEmpty(var)` - NÃO EXISTE
- `getAnswer(var)` - NÃO EXISTE

### O Que DEVERIA Ser (CORRETO)

```python
# Sintaxe válida do Daktus Studio (conforme spider_playbook.md):
'exames_lab' in exames_avaliacao
```

### Por Que Isso Acontece

1. **LLMs são probabilísticos**: Gemini 2.5 Flash Lite às vezes ignora instruções de sintaxe, especialmente quando:
   - O contexto do protocolo é muito grande (60k+ tokens)
   - Há muitas sugestões para aplicar (29-34 sugestões)
   - O modelo "alucina" funções de outras linguagens/frameworks

2. **Prompt Pollution**: O modelo pode estar "contaminado" por exemplos de JavaScript, Python padrão ou outras ferramentas que usam funções helper similares.

3. **Limite de Output Tokens**: O modelo está próximo do limite (8192 tokens) e pode degradar a qualidade da saída quando trunca.

---

## 🛠️ Soluções Implementadas (v3.2.0)

### 1. Sanitizador de Condicionais (PARCIAL)

**Arquivo:** `src/agent/validators/logic_validator.py`

```python
def sanitize_conditional_expression(expression: str) -> str:
    """Remove funções inválidas e converte para sintaxe Daktus."""
    # Padrão: "not selected_only(var, 'value')" → "" (remove)
    # Padrão: "selected_only(var, 'value')" → "'value' in var"
    # Padrão: "contains(var, 'value')" → "'value' in var"
    # etc.
```

**Funcionamento:** Aplicado em `_sanitize_protocol_conditionals()` após reconstrução.

**Limitação:** Regex-based - não pega todos os edge cases.

### 2. Prompt Melhorado (PARCIAL)

**Arquivo:** `src/agent/applicator/protocol_reconstructor.py`

Adicionado ao prompt de reconstrução:

```
🚫 FORBIDDEN IN CONDITIONALS (WILL CAUSE VALIDATION ERRORS):
- NO function calls: contains(), getAnswer(), hasOption(), isEmpty() → These DO NOT exist!
- NO method calls: variable.contains(), list.includes()

✅ CORRECT EXAMPLES:
- "'diabetes' in comorbidades"
- "idade >= 65"
- "(febre == True) and ('dispneia' in sintomas)"

❌ WRONG:
- "contains(comorbidades, 'diabetes')" → WRONG: function call
```

**Limitação:** LLM ignora em ~15-20% dos casos.

### 3. Aprendizado com Erros (IMPLEMENTADO)

**Arquivo:** `src/agent/learning/feedback_learner.py`

Nova função `learn_from_validation_errors()` que:
- Detecta erros de "Function calls not allowed"
- Extrai lições ("Condicionais NÃO suportam chamadas de função")
- Salva em `memory_qa.md` sob "🔍 Lições de Erros de Validação"

**Funcionamento:** Após cada reconstrução com erros, o sistema aprende automaticamente.

### 4. Parser JSON Melhorado (IMPLEMENTADO)

**Arquivo:** `src/agent/core/llm_client.py`

Três novas estratégias de parsing:

**Strategy 6:** Fix literal newlines
- LLM gera strings multi-linha com `\n` literal
- Converte para `\\n` escapado

**Strategy 7:** Repair truncated JSON
- Detecta JSON incompleto (braces desbalanceadas)
- Adiciona `}` e `]` faltantes automaticamente

**Limitação:** Funciona bem, mas não resolve o problema raiz das funções.

---

## ❌ Por Que Não Foi Totalmente Resolvido

1. **Sanitização Imperfeita**: O regex pode não capturar todas as variações de sintaxe que o LLM inventa
2. **Timing do Sanitizador**: Sanitização acontece APÓS validação inicial, mas alguns erros persistem
3. **LLM Creativity**: O modelo inventa novas variações de funções que o regex não prevê
4. **Edge Cases**: Expressões complexas com múltiplas funções aninhadas

---

## ✅ Soluções Possíveis (Próximas Versões)

### Solução 1: Usar Modelo Mais Potente (RECOMENDADO)

**Opção A: Gemini 2.0 Flash (standard)**
- Limite maior de output tokens (8192 → potencialmente mais)
- Melhor seguimento de instruções
- Custo: ~2x mais caro que Flash Lite

**Opção B: Gemini 1.5 Pro**
- Excelente seguimento de instruções
- Limite de 32k output tokens
- Custo: ~5x mais caro

**Implementação:**
```python
# Em protocol_reconstructor.py
model = "google/gemini-2.0-flash"  # ou "google/gemini-1.5-pro"
```

### Solução 2: Few-Shot Examples no Prompt (MÉDIO ESFORÇO)

Adicionar exemplos concretos de antes/depois:

```python
EXAMPLES:
WRONG: "selected_only(diabetes, 'tipo1')"
CORRECT: "'tipo1' in diabetes"

WRONG: "contains(sintomas, 'febre')"
CORRECT: "'febre' in sintomas"
```

**Estimativa:** Redução de 20% → 5% de erros

### Solução 3: Sanitizador AST-Based (ALTO ESFORÇO)

Trocar regex por AST parsing:

```python
import ast

def sanitize_with_ast(expression: str) -> str:
    """Parse AST, detecta ast.Call nodes, substitui por operadores válidos."""
    tree = ast.parse(expression, mode='eval')
    # Visitor pattern para substituir Call nodes
    # Mais robusto que regex
```

**Vantagem:** Pega 99% dos casos  
**Desvantagem:** Complexidade alta, pode introduzir bugs

### Solução 4: Validação + Re-prompt (BAIXO ESFORÇO, ALTO CUSTO)

Se erros de validação > 0:
1. Detectar quais nodes têm erros
2. Re-enviar APENAS esses nodes ao LLM
3. Pedir correção específica

**Estimativa:** 100% de precisão, mas dobra o custo

### Solução 5: Post-Processing Agressivo (MÉDIO ESFORÇO)

Após reconstrução:
1. Extrair TODAS as expressões condicionais
2. Validar cada uma
3. Se inválida → aplicar sanitização + validar novamente
4. Se ainda inválida → REMOVER a condicional (tornar sempre visível)

**Implementação:**
```python
def aggressive_sanitize(protocol: Dict) -> Dict:
    for node in protocol["nodes"]:
        for question in node.get("data", {}).get("questions", []):
            expr = question.get("expressao", "")
            if expr and not is_valid_conditional(expr):
                # Tentar sanitizar
                sanitized = sanitize_conditional_expression(expr)
                if not is_valid_conditional(sanitized):
                    # Última opção: remover condicional
                    question["expressao"] = ""
                    question["condicional"] = "visivel"
```

---

## 📊 Comparação de Soluções

| Solução | Efetividade | Custo | Esforço | Risco |
|---------|-------------|-------|---------|-------|
| Modelo Potente | 95% | +100% custo | Baixo | Baixo |
| Few-Shot Examples | 80% | 0% | Médio | Baixo |
| AST Sanitizer | 99% | 0% | Alto | Médio |
| Re-prompt | 100% | +100% custo | Baixo | Baixo |
| Post-Process Agressivo | 100% | 0% | Médio | Médio |

---

## 🎯 Recomendação para v3.3

**Abordagem Híbrida:**

1. **Curto Prazo (v3.2.1):**
   - ✅ Adicionar few-shot examples ao prompt
   - ✅ Melhorar sanitizador com mais padrões regex
   - ✅ Manter aprendizado automático

2. **Médio Prazo (v3.3):**
   - 🔄 Migrar para Gemini 2.0 Flash (standard)
   - 🔄 Implementar validação + re-prompt opcional
   - 🔄 Adicionar flag `--strict-validation` para post-processing agressivo

3. **Longo Prazo (v4.0):**
   - 🚀 Implementar sanitizador AST-based
   - 🚀 Sistema de correção automática iterativa
   - 🚀 Testes de validação pré-reconstrução

---

## 📝 Status Atual (v3.2.0)

- ✅ Sistema está **estável e funcional**
- ⚠️ Gera **4-5 avisos de validação** por reconstrução
- 🧠 **Aprende automaticamente** com os erros
- 🧹 **Sanitiza parcialmente** (regex-based)
- 📊 **Taxa de aplicação: 100%**
- ⚡ **Custo médio: $0.07 por reconstrução**

**Conclusão:** O sistema está em **produção com avisos conhecidos**. Protocolo reconstruído é utilizável mas requer revisão manual das 4-5 condicionais com erros.

---

## 🔗 Referências

- `docs/spider_playbook.md` - Sintaxe oficial do Daktus Studio
- `src/agent/validators/logic_validator.py` - Validador e sanitizador
- `src/agent/applicator/protocol_reconstructor.py` - Prompt de reconstrução
- `src/agent/learning/feedback_learner.py` - Aprendizado automático
- `memory_qa.md` - Memória de lições aprendidas
