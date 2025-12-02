#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste V3 - Auto-Apply de Melhorias

Testa a etapa 2 do pipeline v3: aplicar melhorias automaticamente no JSON.
Usa relatório já gerado pela v2 + protocolo JSON original.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests

# Configurar encoding UTF-8 para o console (Windows)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Carregar .env
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

# Configurações
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_AUTO_APPLY = "x-ai/grok-4-fast"  # Grok 4 Fast (cheaper)

# Arquivos de entrada - TESTOSTERONA
REPORT_JSON_PATH = project_root / "reports" / "UNIMED_FORTALEZA_protocolo_solicitacao_testosterona_v0.1.2_22-09-2025-1840_20251129_190647.json"
PROTOCOL_JSON_PATH = project_root / "models_json" / "UNIMED_FORTALEZA_protocolo_solicitacao_testosterona_v0.1.2_22-09-2025-1840.json"

# Diretório de saída
OUTPUT_DIR = project_root / "src" / "agent_v3" / "output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Preços por modelo (USD por 1M tokens) - Atualizar conforme OpenRouter
MODEL_PRICING = {
    "anthropic/claude-sonnet-4.5": {"input": 3.0, "output": 15.0},
    "google/gemini-2.5-flash-preview-09-2025": {"input": 0.075, "output": 0.30},
    "x-ai/grok-code-fast-1": {"input": 0.50, "output": 1.50},
    "x-ai/grok-4-fast": {"input": 0.10, "output": 0.30},  # Grok 4 Fast
}


def estimate_tokens(text: str) -> int:
    """Estima número de tokens (aproximação: 1 token ≈ 4 chars)"""
    return len(text) // 4


def estimate_cost(prompt: str, model: str) -> dict:
    """Estima custo da chamada ao LLM"""
    input_tokens = estimate_tokens(prompt)
    # Estimativa conservadora: output = input * 1.2 (protocolo + overhead)
    output_tokens = int(input_tokens * 1.2)

    pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 3.0})  # Default fallback

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost
    }


def confirm_execution(cost_info: dict, model: str) -> bool:
    """Pergunta ao usuário se deseja continuar com a execução"""
    print("\n" + "="*80)
    print("ESTIMATIVA DE CUSTO")
    print("="*80)
    print(f"\nModelo: {model}")
    print(f"Tokens de entrada (estimado): {cost_info['input_tokens']:,}")
    print(f"Tokens de saída (estimado): {cost_info['output_tokens']:,}")
    print(f"\nCusto de entrada: ${cost_info['input_cost_usd']:.4f}")
    print(f"Custo de saída: ${cost_info['output_cost_usd']:.4f}")
    print(f"Custo total estimado: ${cost_info['total_cost_usd']:.4f}")
    print("="*80)

    # Auto-confirmar se não estiver em modo interativo (TTY)
    if not sys.stdin.isatty():
        print("\n✅ Auto-confirmando execução (modo não-interativo)")
        return True

    try:
        resposta = input("\nDeseja realizar a análise? (s/n): ").lower().strip()
        return resposta == 's'
    except EOFError:
        # Se input() falhar, auto-confirmar
        print("\n✅ Auto-confirmando execução (EOFError)")
        return True


def load_json(path: Path) -> dict:
    """Carrega arquivo JSON com limpeza de sintaxe extra"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Limpar semicolon extra no final (comum em exports)
    content = content.strip()
    if content.endswith('};'):
        content = content[:-1]  # Remove o ';'

    return json.loads(content)


def extract_suggestions_from_report(report_data: dict) -> list:
    """Extrai sugestões de melhoria do relatório v2"""
    # As sugestões estão em improvement_suggestions
    suggestions = report_data.get('improvement_suggestions', [])

    if not suggestions:
        # Fallback: tentar extrair de outros campos
        print("⚠️  Nenhuma sugestão encontrada em 'improvement_suggestions'")
        return []

    print(f"✅ {len(suggestions)} sugestões extraídas do relatório")
    return suggestions


def build_auto_apply_prompt(protocol_json: dict, suggestions: list) -> str:
    """Constrói prompt para auto-apply das melhorias"""

    # Formatar sugestões de forma clara
    suggestions_text = ""
    for i, sugg in enumerate(suggestions, 1):
        if isinstance(sugg, dict):
            priority = sugg.get('priority', 'medium')
            category = sugg.get('category', 'improvement')
            description = sugg.get('description', str(sugg))
        else:
            # Se for string simples
            priority = 'medium'
            category = 'improvement'
            description = str(sugg)

        suggestions_text += f"\n{i}. [{priority.upper()}] {description}\n"

    prompt = f"""Você é um sistema especializado em corrigir protocolos clínicos JSON.

**TAREFA**: Aplicar as seguintes melhorias no protocolo clínico de Solicitação de Testosterona.

**PROTOCOLO ORIGINAL** (estrutura atual):
```json
{json.dumps(protocol_json, indent=2, ensure_ascii=False)}
```

**MELHORIAS A APLICAR**:
{suggestions_text}

**INSTRUÇÕES CRÍTICAS**:

1. **Mantenha a estrutura JSON intacta**:
   - Preserve todos os nodes existentes
   - Preserve todas as questions existentes
   - Preserve todos os IDs (node ids, question ids, option ids)
   - Preserve posicionamento (x, y) de nodes

2. **Aplique cada melhoria com precisão clínica**:
   - Adicione perguntas/opções onde necessário
   - Ajuste condições de visibilidade conforme sugerido
   - Adicione tratamentos/exames faltantes
   - Simplifique expressões condicionais quando indicado

3. **Para cada mudança implementada**:
   - Adicione comentário no campo "descricao" do elemento afetado
   - Formato: "MUDANÇA V3: [descrição breve da mudança]"
   - Isso garante rastreabilidade

4. **Validação clínica**:
   - Verifique que a lógica clínica faz sentido
   - Não invente informações que não estão nas sugestões
   - Se uma sugestão for ambígua, implemente de forma conservadora
   - Priorize mudanças CRITICAL e HIGH primeiro

5. **Priorização**:
   - CRITICAL: Implementar obrigatoriamente
   - HIGH: Implementar se possível sem quebrar estrutura
   - MEDIUM/LOW: Implementar apenas se trivial

**FORMATO DE SAÍDA**:
Retorne APENAS o JSON do protocolo corrigido.
- Sem markdown (```json)
- Sem explicações antes ou depois
- JSON válido e parseável
- Estrutura completa (não parcial)

**IMPORTANTE**:
- Mantenha nomenclatura consistente (português brasileiro)
- Preserve formatação de campos HTML (<p>, <strong>)
- Teste mentalmente que as condições lógicas funcionam
- Se dúvida, melhor não aplicar do que aplicar errado"""

    return prompt


def apply_improvements_via_llm(protocol_json: dict, suggestions: list) -> tuple:
    """
    Aplica melhorias usando Claude Sonnet 4.0

    Returns:
        (protocol_fixed, raw_response, success)
    """

    prompt = build_auto_apply_prompt(protocol_json, suggestions)

    # Estimar custo e confirmar execução
    cost_info = estimate_cost(prompt, MODEL_AUTO_APPLY)

    if not confirm_execution(cost_info, MODEL_AUTO_APPLY):
        print("\n❌ Execução cancelada pelo usuário.")
        return None, "Cancelado pelo usuário", False

    print("\n" + "="*80)
    print(f"APLICANDO MELHORIAS VIA {MODEL_AUTO_APPLY}")
    print("="*80)
    print(f"\nTamanho do prompt: {len(prompt)} caracteres")
    print(f"Sugestões a aplicar: {len(suggestions)}")
    print("\nEnviando para OpenRouter API...")

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_AUTO_APPLY,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,  # Baixo para consistência
                "max_tokens": 1000000  # 1M tokens - prevenir truncamento
            },
            timeout=180  # 3 minutos
        )

        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return None, response.text, False

        response_data = response.json()
        raw_response = response_data['choices'][0]['message']['content']

        print(f"✅ Resposta recebida: {len(raw_response)} caracteres")

        # Tentar extrair JSON da resposta
        json_str = raw_response.strip()

        # Remover markdown se presente
        if "```json" in json_str:
            start = json_str.find("```json") + 7  # Pular "```json"
            # Encontrar o fechamento - pode ter newline ou não
            closing_start = json_str.find("```", start)
            if closing_start != -1:
                json_str = json_str[start:closing_start].strip()
            else:
                # Sem fechamento - remover só o início
                json_str = json_str[start:].strip()
                print("⚠️  Markdown sem fechamento - removido apenas o início")
        elif "```" in json_str:
            start = json_str.find("```") + 3
            closing_start = json_str.find("```", start)
            if closing_start != -1:
                json_str = json_str[start:closing_start].strip()
            else:
                # Sem fechamento - remover só o início
                json_str = json_str[start:].strip()
                print("⚠️  Markdown sem fechamento - removido apenas o início")

        # Debug: mostrar tamanho do JSON extraído
        print(f"📏 JSON extraído: {len(json_str)} caracteres")

        if len(json_str) == 0:
            print(f"❌ JSON vazio após extração!")
            print(f"\nPrimeiros 1000 chars da resposta raw:\n{raw_response[:1000]}")
            return None, raw_response, False

        # Parsear JSON
        try:
            protocol_fixed = json.loads(json_str)
            print("✅ JSON parseado com sucesso")
            return protocol_fixed, raw_response, True
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear JSON: {e}")
            print(f"\nPrimeiros 500 chars do JSON extraído:\n{json_str[:500]}")
            print(f"\nÚltimos 500 chars do JSON extraído:\n{json_str[-500:]}")
            return None, raw_response, False

    except requests.Timeout:
        print("❌ Timeout na chamada ao LLM (>3 minutos)")
        return None, "Timeout", False
    except Exception as e:
        print(f"❌ Erro na chamada ao LLM: {str(e)}")
        return None, str(e), False


def validate_fixed_protocol(original: dict, fixed: dict) -> dict:
    """
    Valida protocolo corrigido

    Returns:
        {
            "valid_json": bool,
            "structure_preserved": bool,
            "changes_detected": bool,
            "errors": [],
            "warnings": []
        }
    """
    errors = []
    warnings = []

    # 1. É um dict válido?
    if not isinstance(fixed, dict):
        errors.append("Protocolo corrigido não é um dicionário JSON")
        return {
            "valid_json": False,
            "structure_preserved": False,
            "changes_detected": False,
            "errors": errors,
            "warnings": warnings
        }

    # 2. Tem as chaves principais?
    if "metadata" not in fixed:
        errors.append("Campo 'metadata' ausente")
    if "nodes" not in fixed:
        errors.append("Campo 'nodes' ausente")

    # 3. Estrutura de nodes preservada
    original_nodes = original.get('nodes', [])
    fixed_nodes = fixed.get('nodes', [])

    if len(fixed_nodes) < len(original_nodes):
        errors.append(f"Nodes removidos: {len(original_nodes)} → {len(fixed_nodes)}")
    elif len(fixed_nodes) > len(original_nodes):
        warnings.append(f"Nodes adicionados: {len(original_nodes)} → {len(fixed_nodes)}")

    # 4. Verificar IDs de nodes preservados
    original_node_ids = {node.get('id') for node in original_nodes}
    fixed_node_ids = {node.get('id') for node in fixed_nodes}

    missing_ids = original_node_ids - fixed_node_ids
    if missing_ids:
        errors.append(f"Node IDs removidos: {missing_ids}")

    # 5. Detectar mudanças
    changes_detected = (json.dumps(original, sort_keys=True) != json.dumps(fixed, sort_keys=True))

    structure_preserved = len(errors) == 0

    return {
        "valid_json": True,
        "structure_preserved": structure_preserved,
        "changes_detected": changes_detected,
        "errors": errors,
        "warnings": warnings
    }


def increment_version(version_str: str) -> str:
    """Incrementa versão no formato MAJOR.MINOR.PATCH"""
    import re
    match = re.search(r'v(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        major, minor, patch = map(int, match.groups())
        patch += 1  # Incrementar PATCH para correções/melhorias
        return f"v{major}.{minor}.{patch}"
    return "v0.1.1"  # Fallback se não encontrar versão


def generate_output_filename(input_path: Path) -> tuple:
    """Gera nome de arquivo de saída baseado no input com versão incrementada"""
    import re

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = input_path.stem  # Nome sem extensão

    # Extrair partes: nome_base + versão + timestamp_original
    # Exemplo: UNIMED_FORTALEZA_protocolo_solicitacao_testosterona_v0.1.2_22-09-2025-1840
    match = re.match(r'(.+?)_(v\d+\.\d+\.\d+)_(.+)', filename)

    if match:
        base_name = match.group(1)  # UNIMED_FORTALEZA_protocolo_solicitacao_testosterona
        version = match.group(2)     # v0.1.2
        # Incrementar versão
        new_version = increment_version(version)
    else:
        # Fallback: usar nome completo e adicionar versão
        base_name = filename
        new_version = "v0.1.1"

    # Gerar nome: base_v0.1.3_20251201_104143.json
    output_filename = f"{base_name}_{new_version}_{timestamp}.json"
    return output_filename, new_version, timestamp


def save_outputs(protocol_fixed: dict, validation: dict, suggestions: list):
    """Salva outputs do teste"""

    # Gerar nome de arquivo correto com versão incrementada
    output_filename, new_version, timestamp = generate_output_filename(PROTOCOL_JSON_PATH)

    # 1. Salvar protocolo corrigido
    fixed_path = OUTPUT_DIR / output_filename
    with open(fixed_path, 'w', encoding='utf-8') as f:
        json.dump(protocol_fixed, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Protocolo corrigido salvo: {fixed_path}")
    print(f"   Nova versão: {new_version}")

    # 2. Salvar relatório de validação
    report_path = OUTPUT_DIR / f"validation_report_{timestamp}.json"
    report_data = {
        "timestamp": timestamp,
        "model_used": MODEL_AUTO_APPLY,
        "suggestions_applied": len(suggestions),
        "validation": validation,
        "files": {
            "original": str(PROTOCOL_JSON_PATH),
            "report": str(REPORT_JSON_PATH),
            "fixed": str(fixed_path)
        }
    }
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Relatório de validação salvo: {report_path}")

    # 3. Salvar relatório em texto legível
    txt_path = OUTPUT_DIR / f"validation_report_{timestamp}.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RELATÓRIO DE VALIDAÇÃO V3 - AUTO-APPLY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Data: {timestamp}\n")
        f.write(f"Modelo: {MODEL_AUTO_APPLY}\n")
        f.write(f"Sugestões aplicadas: {len(suggestions)}\n\n")
        f.write("VALIDAÇÃO\n")
        f.write("-"*80 + "\n")
        f.write(f"JSON válido: {'✅ Sim' if validation['valid_json'] else '❌ Não'}\n")
        f.write(f"Estrutura preservada: {'✅ Sim' if validation['structure_preserved'] else '❌ Não'}\n")
        f.write(f"Mudanças detectadas: {'✅ Sim' if validation['changes_detected'] else '⚠️ Não (sem mudanças)'}\n\n")

        if validation['errors']:
            f.write("ERROS:\n")
            for err in validation['errors']:
                f.write(f"  ❌ {err}\n")
            f.write("\n")

        if validation['warnings']:
            f.write("AVISOS:\n")
            for warn in validation['warnings']:
                f.write(f"  ⚠️ {warn}\n")
            f.write("\n")

        f.write("="*80 + "\n")
    print(f"✅ Relatório em texto salvo: {txt_path}")


def main():
    """Execução principal do teste"""

    print("="*80)
    print("TESTE V3 - AUTO-APPLY DE MELHORIAS")
    print("="*80)

    # 1. Verificar API key
    if not OPENROUTER_API_KEY:
        print("❌ ERRO: OPENROUTER_API_KEY não configurado no .env")
        return

    # 2. Carregar relatório v2
    print(f"\n📄 Carregando relatório v2...")
    print(f"   {REPORT_JSON_PATH}")

    if not REPORT_JSON_PATH.exists():
        print(f"❌ ERRO: Relatório não encontrado")
        return

    report_data = load_json(REPORT_JSON_PATH)
    print(f"   ✅ Relatório carregado")

    # 3. Extrair sugestões
    suggestions = extract_suggestions_from_report(report_data)

    if not suggestions:
        print("❌ ERRO: Nenhuma sugestão encontrada no relatório")
        return

    print(f"\n📋 Sugestões encontradas:")
    for i, sugg in enumerate(suggestions[:3], 1):  # Mostrar apenas primeiras 3
        if isinstance(sugg, dict):
            desc = sugg.get('description', str(sugg))[:100]
        else:
            desc = str(sugg)[:100]
        print(f"   {i}. {desc}...")
    if len(suggestions) > 3:
        print(f"   ... e mais {len(suggestions) - 3} sugestões")

    # 4. Carregar protocolo original
    print(f"\n📄 Carregando protocolo JSON original...")
    print(f"   {PROTOCOL_JSON_PATH}")

    if not PROTOCOL_JSON_PATH.exists():
        print(f"❌ ERRO: Protocolo não encontrado")
        return

    protocol_original = load_json(PROTOCOL_JSON_PATH)
    print(f"   ✅ Protocolo carregado ({len(json.dumps(protocol_original))} bytes)")

    # 5. Aplicar melhorias via LLM
    protocol_fixed, raw_response, success = apply_improvements_via_llm(
        protocol_original,
        suggestions
    )

    if not success or protocol_fixed is None:
        print("\n❌ FALHA: Não foi possível aplicar as melhorias")
        print(f"\nResposta do LLM (primeiros 1000 chars):\n{raw_response[:1000]}")
        return

    # 6. Validar protocolo corrigido
    print("\n🔍 Validando protocolo corrigido...")
    validation = validate_fixed_protocol(protocol_original, protocol_fixed)

    print(f"\n📊 RESULTADOS DA VALIDAÇÃO:")
    print(f"   JSON válido: {'✅ Sim' if validation['valid_json'] else '❌ Não'}")
    print(f"   Estrutura preservada: {'✅ Sim' if validation['structure_preserved'] else '❌ Não'}")
    print(f"   Mudanças detectadas: {'✅ Sim' if validation['changes_detected'] else '⚠️ Não'}")

    if validation['errors']:
        print(f"\n   ❌ ERROS ({len(validation['errors'])}):")
        for err in validation['errors']:
            print(f"      - {err}")

    if validation['warnings']:
        print(f"\n   ⚠️ AVISOS ({len(validation['warnings'])}):")
        for warn in validation['warnings']:
            print(f"      - {warn}")

    # 7. Salvar outputs
    print("\n💾 Salvando outputs...")
    save_outputs(protocol_fixed, validation, suggestions)

    # 8. Resultado final
    print("\n" + "="*80)
    if validation['structure_preserved'] and validation['changes_detected']:
        print("✅ SUCESSO: Melhorias aplicadas com sucesso!")
        print("   - Estrutura JSON preservada")
        print("   - Mudanças detectadas")
        print("   - Protocolo corrigido salvo")
    elif validation['structure_preserved'] and not validation['changes_detected']:
        print("⚠️ ATENÇÃO: Estrutura preservada mas sem mudanças detectadas")
        print("   - Verificar se as melhorias foram realmente aplicadas")
    else:
        print("❌ FALHA: Validação não passou")
        print("   - Estrutura JSON pode estar corrompida")
    print("="*80)

    print(f"\n📁 Outputs salvos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
