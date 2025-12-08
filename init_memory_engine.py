#!/usr/bin/env python3
"""
Script simples para inicializar Memory Engine V2 com dados históricos.
Executa diretamente sem dependências complexas.
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

def extract_rejected_suggestions(memory_qa_path):
    """Extrai sugestões rejeitadas do memory_qa.md"""
    if not memory_qa_path.exists():
        return []
    
    content = memory_qa_path.read_text(encoding='utf-8')
    rejected = []
    
    # Padrão para encontrar seções de feedback
    feedback_pattern = r'## Feedback - (\d{4}-\d{2}-\d{2} \d{2}:\d{2})'
    feedback_sections = list(re.finditer(feedback_pattern, content))
    
    for i, match in enumerate(feedback_sections):
        start_pos = match.end()
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
            sug_pattern = r'- \*\*([^\*]+):\*\* (.+?)(?=\n- \*\*|\n\n|$)'
            suggestions = re.findall(sug_pattern, rejected_text, re.DOTALL)
            
            for sug_id, comment in suggestions:
                sug_id = sug_id.strip()
                comment = comment.strip()
                rejected.append({
                    'suggestion_id': sug_id,
                    'comment': comment,
                    'protocol_id': protocol_id,
                    'model_id': model_id,
                    'timestamp': timestamp_str,
                    'text': comment
                })
    
    return rejected

def create_rules(rejected_suggestions):
    """Converte sugestões rejeitadas em regras"""
    rules = []
    
    for sug in rejected_suggestions:
        text = sug.get('text', sug.get('comment', ''))
        rule_id = hashlib.md5(
            f"{text}_{sug.get('protocol_id', 'unknown')}".encode('utf-8')
        ).hexdigest()[:12]
        
        # Extrair keywords
        keywords = []
        comment_lower = text.lower()
        
        if 'playbook' in comment_lower or 'não consta' in comment_lower or 'fora do playbook' in comment_lower:
            keywords.append('fora_playbook')
        if 'tooltip' in comment_lower:
            keywords.append('tooltip')
        if 'critério médico' in comment_lower or 'critério medico' in comment_lower or 'a critério médico' in comment_lower:
            keywords.append('autonomia_medica')
        if 'critérios de exclusão' in comment_lower or 'criterios de exclusao' in comment_lower:
            keywords.append('criterios_exclusao')
        if 'desnecessário' in comment_lower or 'desnecessario' in comment_lower:
            keywords.append('desnecessario')
        if 'já ocorre' in comment_lower or 'ja ocorre' in comment_lower or 'já implementado' in comment_lower or 'já está' in comment_lower:
            keywords.append('ja_implementado')
        if 'estrutural' in comment_lower or 'função' in comment_lower or 'funcao' in comment_lower or 'daktus studio' in comment_lower:
            keywords.append('mudanca_estrutural')
        if 'especialista' in comment_lower:
            keywords.append('contexto_especialista')
        if 'complexidade' in comment_lower or 'baixo retorno' in comment_lower:
            keywords.append('complexidade_baixo_retorno')
        
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

def initialize_memory_engine():
    """Inicializa Memory Engine com dados históricos"""
    project_root = Path(__file__).resolve().parent
    memory_qa_path = project_root / "memory_qa.md"
    
    print("Inicializando Memory Engine V2...")
    print(f"Lendo: {memory_qa_path}")
    
    # Extrair sugestões rejeitadas
    rejected_suggestions = extract_rejected_suggestions(memory_qa_path)
    print(f"Extraídas {len(rejected_suggestions)} sugestões rejeitadas")
    
    # Converter em regras
    rules = create_rules(rejected_suggestions)
    print(f"Criadas {len(rules)} regras")
    
    # Ler conteúdo existente
    existing_content = ""
    if memory_qa_path.exists():
        existing_content = memory_qa_path.read_text(encoding='utf-8')
    
    # Verificar se já tem seções estruturadas
    has_rules_rejected = '### RULES_REJECTED' in existing_content
    has_rules_accepted = '### RULES_ACCEPTED' in existing_content
    
    if has_rules_rejected:
        print("Seções estruturadas já existem. Atualizando...")
        # Extrair regras existentes
        rejected_match = re.search(
            r'### RULES_REJECTED\s*\n```json\s*\n(.*?)\n```',
            existing_content,
            re.DOTALL
        )
        if rejected_match:
            try:
                existing_rules = json.loads(rejected_match.group(1))
                existing_rule_ids = {r.get('rule_id') for r in existing_rules}
                # Adicionar apenas regras novas
                new_rules = [r for r in rules if r['rule_id'] not in existing_rule_ids]
                rules = existing_rules + new_rules
                print(f"Adicionadas {len(new_rules)} novas regras")
            except:
                rules = rules  # Se falhar, usar apenas novas
    else:
        print("Criando seções estruturadas...")
    
    # Construir novo conteúdo
    rules_json = json.dumps(rules, indent=2, ensure_ascii=False)
    
    # Se não tem seções, adicionar no início
    if not has_rules_rejected and not has_rules_accepted:
        new_content = f"""# Memory QA - Feedback e Aprendizados do Agente Daktus QA

Este documento concentra todos os feedbacks e aprendizados do agente para refinar futuras análises.

## Memory Engine V2 - Regras Estruturadas

### RULES_ACCEPTED
```json
[]
```

### RULES_REJECTED
```json
{rules_json}
```

### VECTOR_INDEX
```json
[]
```

---

## Feedback Histórico

{existing_content.split('## Feedback Histórico', 1)[-1] if '## Feedback Histórico' in existing_content else existing_content}
"""
    else:
        # Atualizar seção RULES_REJECTED
        if has_rules_rejected:
            new_content = re.sub(
                r'(### RULES_REJECTED\s*\n```json\s*\n)(.*?)(\n```)',
                f'\\1{rules_json}\\3',
                existing_content,
                flags=re.DOTALL
            )
        else:
            # Adicionar seção antes do histórico
            history_marker = "## Feedback Histórico"
            if history_marker in existing_content:
                parts = existing_content.split(history_marker, 1)
                new_content = f"{parts[0]}\n### RULES_REJECTED\n```json\n{rules_json}\n```\n\n{history_marker}{parts[1]}"
            else:
                new_content = f"{existing_content}\n\n### RULES_REJECTED\n```json\n{rules_json}\n```\n"
    
    # Salvar
    memory_qa_path.write_text(new_content, encoding='utf-8')
    print(f"✅ Memory Engine V2 inicializado com {len(rules)} regras rejeitadas!")
    print(f"Arquivo salvo: {memory_qa_path}")

if __name__ == "__main__":
    initialize_memory_engine()

