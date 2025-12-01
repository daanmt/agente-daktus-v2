#!/usr/bin/env python3
"""
Validação Crítica DIA 1: Auto-Apply de Melhorias

Este script testa se Claude Sonnet 4.0 consegue aplicar automaticamente
as melhorias sugeridas pela v2 no JSON do protocolo.

Resultado esperado: >80% de sucesso para prosseguir com implementação v3
"""

import json
import os
from pathlib import Path
from datetime import datetime
from agent_v2.pipeline import analyze
from dotenv import load_dotenv

# Carregar .env
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

# Configurações
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_AUTO_APPLY = "anthropic/claude-sonnet-4.0"
PROTOCOLS_TO_TEST = 1  # Começar com 5 protocolos variados

def load_protocol(protocol_path: str) -> dict:
    """Carrega protocolo JSON"""
    with open(protocol_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_v2_analysis(protocol_path: str, playbook_path: str = None) -> dict:
    """Roda análise v2 para gerar sugestões"""
    print(f"\n🔍 Analisando protocolo com V2: {Path(protocol_path).name}")

    result = analyze(
        protocol_path=protocol_path,
        playbook_path=playbook_path,
        model="anthropic/claude-sonnet-4.0"
    )

    suggestions = result.get('improvement_suggestions', [])
    print(f"   ✅ {len(suggestions)} sugestões geradas")

    return result

def build_auto_apply_prompt(protocol_json: dict, suggestions: list) -> str:
    """Constrói prompt para auto-apply"""

    prompt = f"""Você é um sistema de correção automatizada de protocolos clínicos.

**TAREFA**: Aplicar as seguintes melhorias no protocolo JSON fornecido.

**PROTOCOLO ORIGINAL**:
```json
{json.dumps(protocol_json, indent=2, ensure_ascii=False)}
```

**MELHORIAS A APLICAR**:
{json.dumps(suggestions, indent=2, ensure_ascii=False)}

**INSTRUÇÕES**:
1. Aplique cada melhoria no JSON do protocolo de forma precisa
2. Mantenha toda a estrutura original intacta (não remova nada, apenas adicione/corrija)
3. Para cada mudança, adicione rastreabilidade no campo "_change_log" (se não existir, crie)
4. Preserve validação JSON (sintaxe correta)
5. Preserve lógica clínica (não altere fluxos existentes, apenas melhore)

**FORMATO DE SAÍDA**:
Retorne APENAS o JSON do protocolo corrigido, sem markdown, sem explicações.
O JSON deve ser válido e parseável.

**IMPORTANTE**:
- Se uma sugestão for ambígua ou arriscada, PULE ela (melhor não aplicar do que aplicar errado)
- Não invente informações clínicas que não estão nas sugestões
- Mantenha nomenclatura e estrutura existente"""

    return prompt

def apply_improvements_via_llm(protocol_json: dict, suggestions: list) -> tuple[dict, str]:
    """
    Aplica melhorias usando Claude Sonnet 4.0

    Returns:
        (protocol_fixed, raw_response)
    """
    import requests

    prompt = build_auto_apply_prompt(protocol_json, suggestions)

    print("\n🤖 Enviando para Claude Sonnet 4.0 para auto-apply...")

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
            "max_tokens": 32000
        },
        timeout=120
    )

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

    response_data = response.json()
    raw_response = response_data['choices'][0]['message']['content']

    # Tentar extrair JSON da resposta
    try:
        # Remover markdown se presente
        if "```json" in raw_response:
            start = raw_response.find("```json") + 7
            end = raw_response.rfind("```")
            json_str = raw_response[start:end].strip()
        elif "```" in raw_response:
            start = raw_response.find("```") + 3
            end = raw_response.rfind("```")
            json_str = raw_response[start:end].strip()
        else:
            json_str = raw_response.strip()

        protocol_fixed = json.loads(json_str)
        print("   ✅ JSON válido retornado")
        return protocol_fixed, raw_response

    except json.JSONDecodeError as e:
        print(f"   ❌ Erro ao parsear JSON: {e}")
        return None, raw_response

def validate_fixed_protocol(original: dict, fixed: dict) -> dict:
    """
    Valida se protocolo corrigido é válido

    Returns:
        {
            "valid_json": bool,
            "structure_preserved": bool,
            "errors": []
        }
    """
    errors = []

    # Validação 1: É um dict válido?
    if not isinstance(fixed, dict):
        errors.append("Protocolo corrigido não é um dicionário JSON")
        return {"valid_json": False, "structure_preserved": False, "errors": errors}

    # Validação 2: Tem as chaves principais?
    original_keys = set(original.keys())
    fixed_keys = set(fixed.keys())

    missing_keys = original_keys - fixed_keys
    if missing_keys:
        errors.append(f"Chaves removidas indevidamente: {missing_keys}")

    # Validação 3: Estrutura básica preservada
    if "nodes" in original and "nodes" not in fixed:
        errors.append("Estrutura 'nodes' foi removida")

    structure_preserved = len(errors) == 0

    return {
        "valid_json": True,
        "structure_preserved": structure_preserved,
        "errors": errors
    }

def manual_review_prompt(protocol_name: str, suggestions_count: int):
    """Prompt para revisão manual"""
    print(f"\n📋 REVISÃO MANUAL NECESSÁRIA:")
    print(f"   Protocolo: {protocol_name}")
    print(f"   Sugestões aplicadas: {suggestions_count}")
    print(f"\n   Por favor, revise manualmente:")
    print(f"   1. Lógica clínica foi preservada?")
    print(f"   2. Mudanças fazem sentido clinicamente?")
    print(f"   3. Rastreabilidade está clara?")

    response = input("\n   ✅ Aprovado? (s/n): ").lower().strip()
    return response == 's'

def run_validation_experiment():
    """Executa experimento de validação completo"""

    print("="*80)
    print("🧪 VALIDAÇÃO CRÍTICA DIA 1: AUTO-APPLY DE MELHORIAS")
    print("="*80)

    # Buscar protocolos para testar
    protocols_dir = project_root / "models_json"
    protocol_files = sorted(list(protocols_dir.glob("*.json")))[:PROTOCOLS_TO_TEST]

    if len(protocol_files) < PROTOCOLS_TO_TEST:
        print(f"\n⚠️  Apenas {len(protocol_files)} protocolos encontrados (esperado: {PROTOCOLS_TO_TEST})")

    results = []

    for i, protocol_path in enumerate(protocol_files, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}/{len(protocol_files)}: {protocol_path.name}")
        print('='*80)

        try:
            # 1. Carregar protocolo
            protocol_original = load_protocol(str(protocol_path))

            # 2. Rodar v2 para gerar sugestões
            # Buscar playbook correspondente (se existir)
            playbook_candidates = list(protocols_dir.glob(f"*{protocol_path.stem[:20]}*.md"))
            playbook_path = str(playbook_candidates[0]) if playbook_candidates else None

            v2_result = run_v2_analysis(str(protocol_path), playbook_path)
            suggestions = v2_result.get('improvement_suggestions', [])

            if len(suggestions) == 0:
                print("   ⏭️  Sem sugestões para aplicar, pulando...")
                results.append({
                    "protocol": protocol_path.name,
                    "status": "skipped",
                    "reason": "no_suggestions"
                })
                continue

            # 3. Aplicar melhorias via LLM
            protocol_fixed, raw_response = apply_improvements_via_llm(protocol_original, suggestions)

            if protocol_fixed is None:
                print("   ❌ Auto-apply FALHOU (JSON inválido)")
                results.append({
                    "protocol": protocol_path.name,
                    "status": "failed",
                    "reason": "invalid_json",
                    "suggestions_count": len(suggestions)
                })
                continue

            # 4. Validar protocolo corrigido
            validation = validate_fixed_protocol(protocol_original, protocol_fixed)

            if not validation['structure_preserved']:
                print(f"   ❌ Validação FALHOU: {validation['errors']}")
                results.append({
                    "protocol": protocol_path.name,
                    "status": "failed",
                    "reason": "structure_broken",
                    "errors": validation['errors'],
                    "suggestions_count": len(suggestions)
                })
                continue

            # 5. Salvar resultado para revisão manual
            output_dir = project_root / "reports" / "auto_apply_validation"
            output_dir.mkdir(exist_ok=True, parents=True)

            fixed_path = output_dir / f"{protocol_path.stem}_FIXED.json"
            with open(fixed_path, 'w', encoding='utf-8') as f:
                json.dump(protocol_fixed, f, indent=2, ensure_ascii=False)

            print(f"   💾 Protocolo corrigido salvo: {fixed_path}")

            # 6. Revisão manual
            approved = manual_review_prompt(protocol_path.name, len(suggestions))

            if approved:
                print("   ✅ Auto-apply BEM-SUCEDIDO")
                results.append({
                    "protocol": protocol_path.name,
                    "status": "success",
                    "suggestions_count": len(suggestions)
                })
            else:
                print("   ❌ Auto-apply REJEITADO (revisão manual)")
                results.append({
                    "protocol": protocol_path.name,
                    "status": "failed",
                    "reason": "manual_rejection",
                    "suggestions_count": len(suggestions)
                })

        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
            results.append({
                "protocol": protocol_path.name,
                "status": "error",
                "reason": str(e)
            })

    # Gerar relatório final
    generate_validation_report(results)

def generate_validation_report(results: list):
    """Gera relatório de validação"""

    print("\n" + "="*80)
    print("📊 RELATÓRIO DE VALIDAÇÃO - AUTO-APPLY")
    print("="*80)

    total = len(results)
    success = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    skipped = len([r for r in results if r['status'] == 'skipped'])
    errors = len([r for r in results if r['status'] == 'error'])

    success_rate = (success / (total - skipped) * 100) if (total - skipped) > 0 else 0

    print(f"\n📈 MÉTRICAS:")
    print(f"   Total de protocolos testados: {total}")
    print(f"   ✅ Sucesso: {success}")
    print(f"   ❌ Falhou: {failed}")
    print(f"   ⏭️  Pulado (sem sugestões): {skipped}")
    print(f"   ⚠️  Erros: {errors}")
    print(f"\n   🎯 TAXA DE SUCESSO: {success_rate:.1f}%")

    print(f"\n🎯 DECISÃO:")
    if success_rate >= 80:
        print(f"   ✅ PROSSEGUIR COM IMPLEMENTAÇÃO V3")
        print(f"      Taxa de sucesso ({success_rate:.1f}%) atingiu meta (>80%)")
        print(f"\n   📅 Próximos passos:")
        print(f"      - DIAS 2-4: Implementar JSONCompactor")
        print(f"      - DIAS 5-7: Implementar ImprovementApplicator")
    elif success_rate >= 60:
        print(f"   ⚠️  REFINAR E ITERAR")
        print(f"      Taxa de sucesso ({success_rate:.1f}%) abaixo da meta (>80%)")
        print(f"\n   📅 Ações:")
        print(f"      - Analisar falhas")
        print(f"      - Refinar prompt de auto-apply")
        print(f"      - Repetir validação")
    else:
        print(f"   ❌ REAVALIAR ABORDAGEM")
        print(f"      Taxa de sucesso ({success_rate:.1f}%) muito baixa")
        print(f"\n   📅 Opções:")
        print(f"      - Considerar modo assistido (não totalmente automático)")
        print(f"      - Focar em correções específicas (não todas)")
        print(f"      - Priorizar apenas mudanças de alta confiança")

    # Salvar relatório
    report_path = project_root / "reports" / "auto_apply_validation" / "VALIDATION_REPORT.md"
    report_path.parent.mkdir(exist_ok=True, parents=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Relatório de Validação - Auto-Apply V3\n\n")
        f.write(f"**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Métricas\n\n")
        f.write(f"- Total: {total}\n")
        f.write(f"- Sucesso: {success}\n")
        f.write(f"- Falhou: {failed}\n")
        f.write(f"- Taxa de Sucesso: {success_rate:.1f}%\n\n")
        f.write(f"## Resultados Detalhados\n\n")
        for r in results:
            f.write(f"### {r['protocol']}\n")
            f.write(f"- Status: {r['status']}\n")
            if 'reason' in r:
                f.write(f"- Razão: {r['reason']}\n")
            if 'suggestions_count' in r:
                f.write(f"- Sugestões aplicadas: {r['suggestions_count']}\n")
            f.write("\n")

    print(f"\n📄 Relatório salvo: {report_path}")

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("❌ ERRO: OPENROUTER_API_KEY não configurado no .env")
        exit(1)

    run_validation_experiment()
