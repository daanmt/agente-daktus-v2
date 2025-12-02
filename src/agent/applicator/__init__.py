"""
Applicator Module - Auto-Apply de Melhorias

Este módulo implementa a aplicação automática de melhorias no protocolo JSON.

Componentes:
- ImprovementApplicator: Motor principal de auto-apply (skeleton)
- ProtocolReconstructor: Reconstrução de protocolo JSON (MVP)
- LLMClient: Cliente LLM especializado (skeleton)
- version_utils: Utilitários para versionamento de protocolos
"""

from .improvement_applicator import ImprovementApplicator, ApplyResult
from .protocol_reconstructor import ProtocolReconstructor, ReconstructionResult
from .version_utils import (
    extract_version_from_protocol,
    increment_version,
    extract_version_from_filename,
    generate_daktus_timestamp,
    generate_output_filename,
    update_protocol_version
)

__all__ = [
    "ImprovementApplicator",
    "ApplyResult",
    "ProtocolReconstructor",
    "ReconstructionResult",
    "extract_version_from_protocol",
    "increment_version",
    "extract_version_from_filename",
    "generate_daktus_timestamp",
    "generate_output_filename",
    "update_protocol_version"
]

