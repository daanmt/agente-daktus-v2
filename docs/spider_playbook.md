# Playbook do Spider — Ferramenta de Modelagem de Protocolos Clínicos

Responsável: Conteúdo Daktus

## Visão Geral

O **Spider** é a ferramenta utilizada para modelar e editar protocolos clínicos dentro da Daktus.

Link: https://daktusspider.netlify.app/

---

## Estrutura de Protocolo

Um protocolo médico é formado por uma sequência de passos (nodos) conectados por arestas.

### Tipos de Nodos

| Tipo | Type (JSON) | Descrição |
|------|-------------|-----------|
| **Nodo de Coleta** | `custom` | Cadastra perguntas ao profissional de saúde |
| **Nodo de Conduta** | `conduct` | Define ações clínicas (exames, medicamentos, encaminhamentos) |
| **Nodo de Processamento** | `summary` | Expressões condicionais avançadas e aliases |

---

## Nodo de Coleta (type: custom)

### Campos Obrigatórios

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `nome` | A pergunta em si | "Paciente tem comorbidades?" |
| `User ID` (uid) | Identificador único para expressões | `paciente_comorbidade` |
| `tipo de pergunta` | Formato da resposta | Ver tipos abaixo |
| `condições de visibilidade` | Quando a pergunta aparece | `'trauma_nenhum' in trauma` |

### Tipos de Pergunta

| Tipo | Descrição |
|------|-----------|
| `string` | Texto livre |
| `numero` | Resposta numérica |
| `booleano` | Sim/Não |
| `data-hora` | Data e hora |
| `multipla-escolha` | Lista de opções (mono ou multi-seleção) |

### Opções de Múltipla Escolha

```json
{
  "id": "neuro_esclerose",
  "label": "Esclerose múltipla",
  "preselecionado": false,
  "excludente": false
}
```

- **preselecionado**: Opção vem marcada automaticamente
- **excludente**: Selecionar esta opção desmarca todas as outras

---

## Nodo de Conduta (type: conduct)

Define ações clínicas com lógica condicional:

```json
{
  "nome": "RM - Coluna cervical ou dorsal ou lombar",
  "condicao": "(cirurgia == False) and ('trauma_nenhum' in trauma)"
}
```

### Campos Típicos

- **exames**: Lista de exames a solicitar
- **medicamentos**: Prescrições
- **encaminhamentos**: Para especialidades
- **mensagem_alerta**: Alertas importantes para o profissional

---

## Nodo de Processamento (type: summary)

Expressões condicionais avançadas e aliases:

```json
{
  "nome": "selecionado_condicao_nenhum",
  "expressao": "'lombalgia_lombociatalgia_nenhum' in lombalgia_lombociatalgia"
}
```

---

## Expressões Lógicas

### Sintaxe Python

```python
# Verificar resposta selecionada
'lombalgia_lombociatalgia_nenhum' in lombalgia_lombociatalgia

# Verificar ausência de resposta
'red_flag_nenhum' not in red_flag

# Combinar condições
(cirurgia == False) and ('trauma_nenhum' in trauma) and ('radiculopatia_nenhuma' not in radiculopatia)
```

### Operadores Permitidos

| Operador | Uso |
|----------|-----|
| `in` | Verifica se valor está na resposta |
| `not in` | Verifica ausência |
| `==` | Igualdade |
| `!=` | Diferença |
| `and` | Condição E |
| `or` | Condição OU |
| `>`, `<`, `>=`, `<=` | Comparações numéricas |

---

## Padrões de Nomenclatura

### IDs de Perguntas (uid)

✅ **Correto:**
- `uso_antimicrobianos`
- `has_comorbidades`
- `paciente_comorbidades`
- `sintomas_generalizados_sem_sinais`

❌ **Evitar:**
- `pergunta1`, `p1` (genérico)
- `P1`, `P2` (maiúsculas)

### IDs de Alternativas (options.id)

```json
{
  "id": "neuro_esclerose",
  "label": "Esclerose múltipla"
}
```

- Minúsculas apenas
- Sem espaços ou acentos
- Usar `_` como separador
- Prefixo do grupo: `neuro_`, `trauma_`, `sintomas_`

---

## Títulos de Nodos

| Contexto | Sufixo | Exemplo |
|----------|--------|---------|
| Nodos de coleta antes de conduta | `- inicial` | "Anamnese - inicial" |
| Nodos sem break point | `- direta` | "Suspeita(s) principal(is) - direta" |
| Nodos de conduta com break point | `- avaliação` | "Conduta - avaliação" |
| Nodos após break point | `- reavaliação` | "Revisão - reavaliação" |

---

## Versionamento

Padrão: `MAJOR.MINOR` (ex: `1.0`, `1.1`, `2.0`)

### Incremento MAJOR (primeiro dígito)
- Criação de ≥ 2 nodos
- Criação ou mudança de ≥ 5 artefatos na conduta

### Incremento MINOR (segundo dígito)
- Criação de < 2 nodos
- Criação ou mudança de < 5 artefatos
- Mudanças de condicionais
- Correções de texto
- Mudança de nomes

---

## Banco de Variáveis Clínicas Daktus

Variáveis padronizadas que devem ser usadas:

| Categoria | Exemplo ID | Exemplo Nome |
|-----------|------------|--------------|
| Sintomas GI | `diarreia` | Diarreia |
| Sintomas GI | `nauseas` | Náuseas |
| Sintomas GI | `vomitos` | Vômitos |
| Sintomas GI | `melena` | Melena |
| Comorbidades | `has` | Hipertensão arterial sistêmica |
| Medicamentos | `metformina_uso_prolongado` | Uso prolongado de metformina |

### Regras

1. Verificar se variável existe no banco antes de criar nova
2. Se existir, usar exatamente o mesmo ID e nome
3. Se não existir, adicionar ao banco com CID-10 e SNOMED

---

## Campos Comuns no JSON

```json
{
  "nodes": [
    {
      "id": "node-1",
      "type": "custom",
      "data": {
        "label": "Anamnese - inicial",
        "description": "Coleta de sintomas",
        "questions": [
          {
            "id": "q-1",
            "uid": "sintomas",
            "nome": "Quais sintomas o paciente apresenta?",
            "tipo": "multipla-escolha",
            "options": [...],
            "expressao": "",
            "visibilidade": "visivel"
          }
        ]
      }
    },
    {
      "id": "node-2",
      "type": "conduct",
      "data": {
        "label": "Conduta - avaliação",
        "exames": [...],
        "medicamentos": [...],
        "mensagem_alerta": "ATENÇÃO: ..."
      }
    }
  ],
  "edges": [
    {
      "source": "node-1",
      "target": "node-2"
    }
  ]
}
```

---

## Referência para o Agente

### Campos Modificáveis em Sugestões

| Campo | Nodo Type | Descrição |
|-------|-----------|-----------|
| `data.questions[].nome` | custom | Texto da pergunta |
| `data.questions[].options` | custom | Opções de múltipla escolha |
| `data.questions[].expressao` | custom | Condição de visibilidade |
| `data.mensagem_alerta` | conduct | Alerta para o profissional |
| `data.exames` | conduct | Lista de exames |
| `data.medicamentos` | conduct | Prescrições |
| `data.condicao` | conduct | Condição para exibir conduta |
| `clinicalExpressions` | summary | Aliases de expressões |

### Sugestões Válidas vs Inválidas

✅ **Válidas:**
- Adicionar `mensagem_alerta` com texto específico
- Modificar `condicao` de um exame
- Adicionar opção a pergunta existente
- Criar expressão no summary

❌ **Inválidas:**
- "Adicionar tooltip" (funcionalidade do sistema)
- "Implementar nova tela" (mudança estrutural)
- "Mudar interface" (UI do Spider)
- Sugerir exames não mencionados no playbook clínico
