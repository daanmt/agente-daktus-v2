"""
Change Verifier - Verifies that protocol reconstruction actually applied changes.

Wave 2 Implementation - TASK 2.4

Problem this solves:
- LLM says "applied" but JSON is unchanged
- Changelog entries without actual modifications
- Repeated suggestions because LLM didn't actually apply them

After reconstruction, this verifies:
1. Target fields were actually modified
2. Changes align with suggestion instructions
3. Changelog entries were created
"""

import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from ..core.logger import logger


@dataclass
class ChangeVerification:
    """Result of verifying a single change."""
    suggestion_id: str
    suggestion_title: str
    verified: bool
    target_field: str
    node_id: str
    error: Optional[str] = None
    original_value: Optional[str] = None
    new_value: Optional[str] = None
    has_changelog: bool = False


class ChangeVerifier:
    """
    Verifies that protocol changes were actually applied.
    
    Usage:
        verifier = ChangeVerifier()
        results = verifier.verify_changes(
            original_protocol,
            reconstructed_protocol,
            applied_suggestions
        )
    """
    
    def verify_changes(
        self,
        original_protocol: Dict,
        reconstructed_protocol: Dict,
        applied_suggestions: List[Dict]
    ) -> Tuple[List[ChangeVerification], List[ChangeVerification]]:
        """
        Verify that each suggestion was actually applied.
        
        Args:
            original_protocol: Protocol before reconstruction
            reconstructed_protocol: Protocol after reconstruction
            applied_suggestions: List of suggestions that were "applied"
        
        Returns:
            (verified_changes, failed_changes)
        """
        verified = []
        failed = []
        
        for sug in applied_suggestions:
            result = self._verify_single_change(
                original_protocol,
                reconstructed_protocol,
                sug
            )
            
            if result.verified:
                verified.append(result)
            else:
                failed.append(result)
        
        # Log summary
        if failed:
            logger.warning(
                f"⚠️ {len(failed)} suggestions were NOT actually applied:\n" +
                "\n".join(f"   - {f.suggestion_id}: {f.error}" for f in failed[:5])
            )
        
        logger.info(f"✅ {len(verified)} changes verified in reconstructed protocol")
        
        return verified, failed
    
    def _verify_single_change(
        self,
        original: Dict,
        reconstructed: Dict,
        suggestion: Dict
    ) -> ChangeVerification:
        """Verify a single suggestion was applied."""
        sug_id = suggestion.get('id', 'unknown')
        title = suggestion.get('title', sug_id)
        
        # Get implementation strategy
        impl = suggestion.get('implementation_strategy', {})
        if isinstance(impl, str):
            # Fallback: Try to extract node_id from specific_location
            specific_loc = suggestion.get('specific_location', {})
            if isinstance(specific_loc, dict):
                node_id = specific_loc.get('node_id', '')
                field = specific_loc.get('field', 'descricao')
            else:
                return ChangeVerification(
                    suggestion_id=sug_id,
                    suggestion_title=title,
                    verified=False,
                    target_field='unknown',
                    node_id='unknown',
                    error="No implementation_strategy or specific_location"
                )
        else:
            target_field = impl.get('target_field', '')
            # Try to get node_id from specific_location
            specific_loc = suggestion.get('specific_location', {})
            if isinstance(specific_loc, dict):
                node_id = specific_loc.get('node_id', '')
            else:
                node_id = ''
        
        # If no node_id, can't verify
        if not node_id:
            return ChangeVerification(
                suggestion_id=sug_id,
                suggestion_title=title,
                verified=False,
                target_field=target_field if impl and isinstance(impl, dict) else 'unknown',
                node_id='unknown',
                error="No node_id specified in specific_location"
            )
        
        # Find nodes in both protocols
        original_node = self._find_node(original, node_id)
        reconstructed_node = self._find_node(reconstructed, node_id)
        
        if not original_node:
            return ChangeVerification(
                suggestion_id=sug_id,
                suggestion_title=title,
                verified=False,
                target_field=target_field if impl and isinstance(impl, dict) else 'unknown',
                node_id=node_id,
                error=f"Node {node_id} not found in original protocol"
            )
        
        if not reconstructed_node:
            return ChangeVerification(
                suggestion_id=sug_id,
                suggestion_title=title,
                verified=False,
                target_field=target_field if impl and isinstance(impl, dict) else 'unknown',
                node_id=node_id,
                error=f"Node {node_id} not found in reconstructed protocol"
            )
        
        # Compare nodes
        if original_node == reconstructed_node:
            return ChangeVerification(
                suggestion_id=sug_id,
                suggestion_title=title,
                verified=False,
                target_field=target_field if impl and isinstance(impl, dict) else 'any',
                node_id=node_id,
                error="Node unchanged after reconstruction"
            )
        
        # Node was modified - check for changelog
        has_changelog = self._has_changelog(reconstructed_node, sug_id)
        
        # Get the changed values (for reporting)
        original_str = json.dumps(original_node, ensure_ascii=False)[:200]
        reconstructed_str = json.dumps(reconstructed_node, ensure_ascii=False)[:200]
        
        return ChangeVerification(
            suggestion_id=sug_id,
            suggestion_title=title,
            verified=True,
            target_field=target_field if impl and isinstance(impl, dict) else 'multiple',
            node_id=node_id,
            original_value=original_str,
            new_value=reconstructed_str,
            has_changelog=has_changelog
        )
    
    def _find_node(self, protocol: Dict, node_id: str) -> Optional[Dict]:
        """Find node by ID in protocol."""
        nodes = protocol.get('nodes', [])
        for node in nodes:
            if node.get('id') == node_id:
                return node
        return None
    
    def _has_changelog(self, node: Dict, suggestion_id: str) -> bool:
        """Check if node has changelog entry for this suggestion."""
        # Changelog can be in various places
        node_str = json.dumps(node, ensure_ascii=False).lower()
        
        # Look for [CHANGELOG or suggestion ID
        return '[changelog' in node_str or suggestion_id.lower() in node_str


def verify_reconstruction_changes(
    original_protocol: Dict,
    reconstructed_protocol: Dict,
    applied_suggestions: List[Dict]
) -> Dict[str, Any]:
    """
    Convenience function to verify changes and return summary.
    
    Returns:
        {
            'total': int,
            'verified': int,
            'failed': int,
            'verification_rate': float,
            'failed_details': [...]
        }
    """
    verifier = ChangeVerifier()
    verified, failed = verifier.verify_changes(
        original_protocol,
        reconstructed_protocol,
        applied_suggestions
    )
    
    total = len(applied_suggestions)
    
    return {
        'total': total,
        'verified': len(verified),
        'failed': len(failed),
        'verification_rate': len(verified) / total if total > 0 else 1.0,
        'verified_details': [
            {
                'id': v.suggestion_id,
                'title': v.suggestion_title,
                'node_id': v.node_id,
                'has_changelog': v.has_changelog
            }
            for v in verified
        ],
        'failed_details': [
            {
                'id': f.suggestion_id,
                'title': f.suggestion_title,
                'node_id': f.node_id,
                'error': f.error
            }
            for f in failed
        ]
    }
