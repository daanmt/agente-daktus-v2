"""
Script de Migração de Feedback Histórico para Memory Engine V2

Este script analisa o memory_qa.md e extrai todas as sugestões rejeitadas
dos feedbacks históricos, convertendo-as em regras estruturadas para o
Memory Engine.

Uso:
    python -m agent.feedback.migrate_historical_feedback
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..core.logger import logger
from .memory_engine import MemoryEngine


def extract_rejected_suggestions_from_memory_qa(memory_qa_path: Path) -> List[Dict]:
    """
    Extrai todas as sugestões rejeitadas do memory_qa.md.
    
    Args:
        memory_qa_path: Caminho para memory_qa.md
        
    Returns:
        Lista de dicionários com sugestões rejeitadas e seus comentários
    """
    if not memory_qa_path.exists():
        logger.warning(f"memory_qa.md não encontrado em {memory_qa_path}")
        return []
    
    content = memory_qa_path.read_text(encoding='utf-8')
    rejected_suggestions = []
    
    # Padrão para encontrar seções de feedback
    feedback_pattern = r'## Feedback - (\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
    feedback_sections = list(re.finditer(feedback_pattern, content))
    
    for i, match in enumerate(feedback_sections):
        start_pos = match.end()
        # Pegar até o próximo feedback ou fim do arquivo
        if i + 1 < len(feedback_sections):
            end_pos = feedback_sections[i + 1].start()
        else:
            end_pos = len(content)
        
        section_content = content[start_pos:end_pos]
        
        # Extrair protocolo e modelo
        protocol_match = re.search(r'\*\*Protocolo:\*\* (.+)', section_content)
        model_match = re.search(r'\*\*Modelo:\*\* (.+)', section_content)
        
        protocol_id = protocol_match.group(1).strip() if protocol_match else "unknown"
        model_id = model_match.group(1).strip() if model_match else "unknown"
        timestamp_str = match.group(1)
        
        # Extrair sugestões rejeitadas
        rejected_section = re.search(
            r'### Sugestões Rejeitadas.*?\n(.*?)(?=\n---|\n##|$)',
            section_content,
            re.DOTALL
        )
        
        if rejected_section:
            rejected_text = rejected_section.group(1)
            
            # Padrão para extrair sugestões individuais
            # Formato: - **sug_XXX:** comentário
            sug_pattern = r'- \*\*([^\*]+):\*\* (.+?)(?=\n- \*\*|\n\n|$)'
            suggestions = re.findall(sug_pattern, rejected_text, re.DOTALL)
            
            for sug_id, comment in suggestions:
                sug_id = sug_id.strip()
                comment = comment.strip()
                
                # Tentar extrair título/descrição de reports se disponível
                # Por enquanto, vamos usar o comentário como base
                rejected_suggestions.append({
                    'suggestion_id': sug_id,
                    'comment': comment,
                    'protocol_id': protocol_id,
                    'model_id': model_id,
                    'timestamp': timestamp_str,
                    'text': comment  # Usar comentário como texto principal
                })
    
    logger.info(f"Extraídas {len(rejected_suggestions)} sugestões rejeitadas do histórico")
    return rejected_suggestions


def extract_patterns_from_insights(memory_qa_path: Path) -> List[Dict]:
    """
    Extrai padrões de rejeição dos insights e aprendizados.
    
    Args:
        memory_qa_path: Caminho para memory_qa.md
        
    Returns:
        Lista de padrões extraídos
    """
    if not memory_qa_path.exists():
        return []
    
    content = memory_qa_path.read_text(encoding='utf-8')
    patterns = []
    
    # Padrão para encontrar seções de aprendizados
    learning_pattern = r'## Aprendizados - (\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
    learning_sections = list(re.finditer(learning_pattern, content))
    
    for match in learning_sections:
        start_pos = match.end()
        # Pegar até o próximo ## ou fim
        next_section = re.search(r'\n## ', content[start_pos:])
        if next_section:
            end_pos = start_pos + next_section.start()
        else:
            end_pos = len(content)
        
        section_content = content[start_pos:end_pos]
        
        # Extrair padrões individuais
        pattern_pattern = r'### Padrão: (.+?)\n\n\*\*Descrição:\*\* (.+?)\n\n\*\*Severidade:\*\* (.+?)\n\*\*Frequência:\*\* (\d+)'
        pattern_matches = re.finditer(pattern_pattern, section_content, re.DOTALL)
        
        for pm in pattern_matches:
            name = pm.group(1).strip()
            description = pm.group(2).strip()
            severity = pm.group(3).strip()
            frequency = int(pm.group(4))
            
            # Extrair exemplos
            examples_match = re.search(r'\*\*Exemplos:\*\*\n(.*?)(?=\n---|\n###|$)', section_content[pm.end():], re.DOTALL)
            examples = []
            if examples_match:
                examples_text = examples_match.group(1)
                example_lines = [e.strip('- ').strip() for e in examples_text.split('\n') if e.strip() and e.strip().startswith('-')]
                examples = example_lines[:3]  # Limitar a 3 exemplos
            
            patterns.append({
                'name': name,
                'description': description,
                'severity': severity,
                'frequency': frequency,
                'examples': examples
            })
    
    logger.info(f"Extraídos {len(patterns)} padrões de aprendizados")
    return patterns


def create_rules_from_rejected_suggestions(rejected_suggestions: List[Dict]) -> List[Dict]:
    """
    Converte sugestões rejeitadas em regras estruturadas.
    
    Args:
        rejected_suggestions: Lista de sugestões rejeitadas
        
    Returns:
        Lista de regras no formato do Memory Engine
    """
    rules = []
    
    for sug in rejected_suggestions:
        # Criar texto normalizado para comparação
        text = sug.get('text', sug.get('comment', ''))
        
        # Gerar rule_id estável
        rule_id = hashlib.md5(
            f"{text}_{sug.get('protocol_id', 'unknown')}".encode('utf-8')
        ).hexdigest()[:12]
        
        # Tentar extrair palavras-chave do comentário
        keywords = []
        comment_lower = text.lower()
        
        # Padrões comuns de rejeição
        if 'playbook' in comment_lower or 'não consta' in comment_lower:
            keywords.append('fora_playbook')
        if 'tooltip' in comment_lower:
            keywords.append('tooltip')
        if 'critério médico' in comment_lower or 'critério medico' in comment_lower:
            keywords.append('autonomia_medica')
        if 'critérios de exclusão' in comment_lower or 'criterios de exclusao' in comment_lower:
            keywords.append('criterios_exclusao')
        if 'desnecessário' in comment_lower or 'desnecessario' in comment_lower:
            keywords.append('desnecessario')
        if 'já ocorre' in comment_lower or 'ja ocorre' in comment_lower or 'já implementado' in comment_lower:
            keywords.append('ja_implementado')
        if 'estrutural' in comment_lower or 'função' in comment_lower or 'funcao' in comment_lower:
            keywords.append('mudanca_estrutural')
        if 'especialista' in comment_lower:
            keywords.append('contexto_especialista')
        
        rule = {
            'rule_id': rule_id,
            'text': text,
            'decision': 'rejected',
            'protocol_id': sug.get('protocol_id', 'unknown'),
            'model_id': sug.get('model_id', 'unknown'),
            'comment': sug.get('comment', ''),
            'timestamp': sug.get('timestamp', datetime.now().isoformat()),
            'keywords': keywords,
            'suggestion_id': sug.get('suggestion_id', 'unknown')
        }
        
        rules.append(rule)
    
    return rules


def migrate_historical_feedback():
    """
    Função principal de migração.
    """
    logger.info("Iniciando migração de feedback histórico para Memory Engine V2...")
    
    # Caminhos
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    memory_qa_path = project_root / "memory_qa.md"
    
    # Inicializar Memory Engine
    memory = MemoryEngine()
    memory.load_memory()
    
    # Extrair sugestões rejeitadas
    rejected_suggestions = extract_rejected_suggestions_from_memory_qa(memory_qa_path)
    
    if not rejected_suggestions:
        logger.warning("Nenhuma sugestão rejeitada encontrada no histórico")
        return
    
    # Converter em regras
    rules = create_rules_from_rejected_suggestions(rejected_suggestions)
    
    logger.info(f"Criadas {len(rules)} regras a partir do histórico")
    
    # Adicionar regras ao Memory Engine
    for rule in rules:
        # Verificar se já existe
        existing_rejected = [r for r in memory.rules_rejected if r.get('rule_id') == rule['rule_id']]
        if not existing_rejected:
            memory.rules_rejected.append(rule)
            logger.debug(f"Adicionada regra rejeitada: {rule['rule_id']} - {rule['text'][:50]}...")
    
    # Extrair padrões de aprendizados
    patterns = extract_patterns_from_insights(memory_qa_path)
    
    # Adicionar padrões como regras genéricas
    for pattern in patterns:
        # Criar regra genérica baseada no padrão
        pattern_text = f"{pattern['name']}: {pattern['description']}"
        rule_id = hashlib.md5(pattern_text.encode('utf-8')).hexdigest()[:12]
        
        # Verificar se já existe
        existing = [r for r in memory.rules_rejected if r.get('rule_id') == rule_id]
        if not existing:
            rule = {
                'rule_id': rule_id,
                'text': pattern_text,
                'decision': 'rejected',
                'protocol_id': 'pattern',
                'model_id': 'pattern',
                'comment': f"Padrão identificado: {pattern['name']} (frequência: {pattern['frequency']}, severidade: {pattern['severity']})",
                'timestamp': datetime.now().isoformat(),
                'keywords': [pattern['name'].lower().replace(' ', '_')],
                'pattern': True,
                'examples': pattern.get('examples', [])
            }
            memory.rules_rejected.append(rule)
            logger.debug(f"Adicionado padrão: {pattern['name']}")
    
    # Salvar
    memory.save_memory()
    
    logger.info(f"Migração concluída! Total de regras rejeitadas: {len(memory.rules_rejected)}")
    logger.info(f"  - Regras de sugestões específicas: {len([r for r in memory.rules_rejected if not r.get('pattern')])}")
    logger.info(f"  - Regras de padrões: {len([r for r in memory.rules_rejected if r.get('pattern')])}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    migrate_historical_feedback()

