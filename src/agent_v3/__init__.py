"""
Agent V3 - Correção Automatizada de Protocolos Clínicos

Transformação de auditoria passiva (v2) para correção ativa (v3).

Principais funcionalidades:
- Auto-apply de melhorias no JSON do protocolo
- Suporte a protocolos JSON massivos (>3k linhas)
- Prompt caching agressivo (reduz custo em 50-70%)
- Priorização de sugestões por impacto
- Validação estrutural automática
- Rastreabilidade completa de mudanças

Uso:
    from agent_v3.pipeline import analyze_and_fix

    resultado = analyze_and_fix(
        protocol_path="protocolo.json",
        playbook_path="playbook.md",
        auto_apply=True,
        confidence_threshold=0.90
    )
"""

__version__ = "3.0.0-alpha"
__author__ = "Daktus QA Team"

# Exports principais (serão implementados nas próximas fases)
# from .pipeline import analyze_and_fix
