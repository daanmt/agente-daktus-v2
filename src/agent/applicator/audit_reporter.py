"""
Audit Reporter - Generates detailed audit reports for protocol reconstruction.

Wave 3 Enhancement - For compliance and QA auditing.

Generates a human-readable report of all changes applied during reconstruction.
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json

from ..core.logger import logger


class AuditReporter:
    """
    Generates detailed audit reports for protocol reconstruction.
    """
    
    @staticmethod
    def generate_audit_report(
        original_protocol: Dict,
        reconstructed_protocol: Dict,
        suggestions: List[Dict],
        changes_applied: List[Dict],
        detailed_changelog: Optional[List[Dict]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a detailed audit report.
        
        Args:
            original_protocol: Original protocol JSON
            reconstructed_protocol: Reconstructed protocol JSON
            suggestions: List of suggestions that were applied
            changes_applied: List of changes from reconstruction
            detailed_changelog: LLM-generated detailed changelog (preferred)
            output_path: Optional path to save the report
            
        Returns:
            Report content as string
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        protocol_name = original_protocol.get('name', original_protocol.get('protocol_name', 'Unknown'))
        
        lines = [
            "=" * 70,
            "📋 RELATÓRIO DE AUDITORIA - RECONSTRUÇÃO DE PROTOCOLO",
            "=" * 70,
            f"Data: {timestamp}",
            f"Protocolo: {protocol_name}",
            f"Sugestões Aplicadas: {len(suggestions)}",
            "",
        ]
        
        # Use LLM-generated changelog if available (preferred)
        if detailed_changelog and len(detailed_changelog) > 0:
            lines.append("=" * 70)
            lines.append("MUDANÇAS IMPLEMENTADAS (DETALHADO)")
            lines.append("=" * 70)
            lines.append("")
            
            for i, change in enumerate(detailed_changelog, 1):
                action = change.get('action', 'modificação').upper()
                node_id = change.get('node_id', 'N/A')
                node_label = change.get('node_label', '')
                target_type = change.get('target_type', 'N/A')
                target_id = change.get('target_id', '')
                before = change.get('description_before', 'N/A')
                after = change.get('description_after', 'N/A')
                sug_id = change.get('suggestion_id', 'N/A')
                
                lines.append(f"{i}. [{action}] {target_type.upper()}")
                lines.append(f"   Nodo: {node_label} ({node_id})")
                if target_id:
                    lines.append(f"   ID do item: {target_id}")
                if before and before != 'null' and before != 'N/A':
                    lines.append(f"   ANTES: {before}")
                lines.append(f"   DEPOIS: {after}")
                lines.append(f"   Sugestão: {sug_id}")
                lines.append("")
        else:
            # Fallback: basic comparison
            lines.append("=" * 70)
            lines.append("MUDANÇAS DETECTADAS (COMPARAÇÃO)")
            lines.append("=" * 70)
            
            original_nodes = {n.get('id'): n for n in original_protocol.get('nodes', [])}
            reconstructed_nodes = {n.get('id'): n for n in reconstructed_protocol.get('nodes', [])}
            
            modified_nodes = []
            for node_id, new_node in reconstructed_nodes.items():
                old_node = original_nodes.get(node_id)
                if old_node:
                    changes = AuditReporter._compare_nodes(old_node, new_node)
                    if changes:
                        modified_nodes.append((node_id, new_node.get('data', {}).get('label', node_id), changes))
            
            if modified_nodes:
                for node_id, label, changes in modified_nodes:
                    lines.append(f"\n🔹 Nodo: {label} ({node_id})")
                    for change in changes:
                        lines.append(f"   • {change['field']}: {change['type']}")
                        if change.get('details'):
                            lines.append(f"     {change['details']}")
        
        # List suggestions for reference
        lines.append("")
        lines.append("=" * 70)
        lines.append("SUGESTÕES APLICADAS")
        lines.append("=" * 70)
        
        for i, sug in enumerate(suggestions, 1):
            sug_id = sug.get('id', f'SUG{i:03d}')
            title = sug.get('title', sug.get('description', 'N/A'))[:80]
            category = sug.get('category', 'N/A')
            lines.append(f"{i}. [{sug_id}] {title}")
            lines.append(f"   Categoria: {category}")
        
        # Summary
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"RESUMO: {len(suggestions)} sugestões | {timestamp}")
        lines.append("=" * 70)
        
        report_content = "\n".join(lines)
        
        if output_path:
            Path(output_path).write_text(report_content, encoding='utf-8')
            logger.info(f"Audit report saved to: {output_path}")
        
        return report_content
    
    @staticmethod
    def _compare_nodes(old_node: Dict, new_node: Dict) -> List[Dict]:
        """Compare two nodes and return list of changes."""
        changes = []
        
        old_data = old_node.get('data', {})
        new_data = new_node.get('data', {})
        
        # Check questions
        old_questions = {q.get('uid', q.get('id', i)): q for i, q in enumerate(old_data.get('questions', []))}
        new_questions = {q.get('uid', q.get('id', i)): q for i, q in enumerate(new_data.get('questions', []))}
        
        for qid, new_q in new_questions.items():
            if qid not in old_questions:
                changes.append({
                    'field': f"pergunta '{new_q.get('nome', qid)}'",
                    'type': 'ADICIONADA',
                    'details': f"Tipo: {new_q.get('tipo', 'N/A')}"
                })
            else:
                old_q = old_questions[qid]
                # Check for expression/condition changes
                if old_q.get('expressao') != new_q.get('expressao'):
                    changes.append({
                        'field': f"condicional pergunta '{qid}'",
                        'type': 'MODIFICADA',
                        'details': f"Nova: {new_q.get('expressao', '')[:80]}"
                    })
                # Check for nome changes
                if old_q.get('nome') != new_q.get('nome'):
                    changes.append({
                        'field': f"texto pergunta '{qid}'",
                        'type': 'MODIFICADO',
                        'details': None
                    })
        
        # Check mensagem_alerta
        if old_data.get('mensagem_alerta') != new_data.get('mensagem_alerta'):
            if new_data.get('mensagem_alerta') and not old_data.get('mensagem_alerta'):
                changes.append({
                    'field': 'mensagem_alerta',
                    'type': 'ADICIONADA',
                    'details': f"Texto: {new_data.get('mensagem_alerta', '')[:100]}..."
                })
            elif new_data.get('mensagem_alerta'):
                changes.append({
                    'field': 'mensagem_alerta',
                    'type': 'MODIFICADA',
                    'details': None
                })
        
        # Check label
        if old_data.get('label') != new_data.get('label'):
            changes.append({
                'field': 'label',
                'type': 'MODIFICADO',
                'details': f"Novo: {new_data.get('label', '')}"
            })
        
        # Check description
        if old_data.get('descricao') != new_data.get('descricao'):
            changes.append({
                'field': 'descrição',
                'type': 'MODIFICADA',
                'details': None
            })
        
        return changes


def generate_reconstruction_audit(
    original_protocol: Dict,
    reconstructed_protocol: Dict,
    suggestions: List[Dict],
    changes_applied: List[Dict],
    detailed_changelog: Optional[List[Dict]] = None,
    output_path: Optional[str] = None
) -> str:
    """Convenience function to generate audit report."""
    return AuditReporter.generate_audit_report(
        original_protocol, reconstructed_protocol, suggestions, changes_applied,
        detailed_changelog, output_path
    )
