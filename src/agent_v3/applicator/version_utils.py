"""
Utilitários para versionamento de protocolos.

Formato de versão: MAJOR.MINOR.PATCH (semantic versioning)
Formato de timestamp: DD-MM-YYYY-HHMM (padrão Daktus Studio)
"""

import re
from typing import Tuple, Optional
from datetime import datetime


def extract_version_from_protocol(protocol_json: dict) -> Optional[str]:
    """
    Extrai versão do metadata do protocolo.
    
    Args:
        protocol_json: Protocolo JSON
        
    Returns:
        Versão no formato "MAJOR.MINOR.PATCH" ou None se não encontrado
    """
    metadata = protocol_json.get("metadata", {})
    version = metadata.get("version")
    
    if version:
        # Garantir formato MAJOR.MINOR.PATCH
        if isinstance(version, str):
            # Remover 'v' prefix se existir
            version = version.lstrip('v')
            # Verificar se está no formato correto
            parts = version.split('.')
            if len(parts) == 3:
                try:
                    # Validar que são números
                    int(parts[0])
                    int(parts[1])
                    int(parts[2])
                    return version
                except ValueError:
                    pass
    
    return None


def increment_version(version: str, increment_type: str = "patch") -> str:
    """
    Incrementa versão no formato MAJOR.MINOR.PATCH.
    
    Args:
        version: Versão atual (ex: "0.1.1" ou "1.2.3")
        increment_type: Tipo de incremento ("major", "minor", "patch")
        
    Returns:
        Nova versão incrementada (ex: "0.1.2")
    """
    # Remover 'v' prefix se existir
    version = version.lstrip('v')
    
    try:
        parts = version.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        if increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment_type == "minor":
            minor += 1
            patch = 0
        else:  # patch (default)
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    except (ValueError, IndexError) as e:
        # Fallback: retornar versão padrão
        return "0.1.1"


def extract_version_from_filename(filename: str) -> Optional[str]:
    """
    Extrai versão do nome do arquivo.
    
    Formato esperado: nome_v0.1.2_DD-MM-YYYY-HHMM.json
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Versão no formato "MAJOR.MINOR.PATCH" ou None
    """
    # Padrão: v0.1.2 ou 0.1.2
    match = re.search(r'[v]?(\d+\.\d+\.\d+)', filename)
    if match:
        return match.group(1)
    return None


def generate_daktus_timestamp() -> str:
    """
    Gera timestamp no formato Daktus Studio: DD-MM-YYYY-HHMM
    
    Returns:
        Timestamp formatado (ex: "01-12-2025-1430")
    """
    now = datetime.now()
    return now.strftime("%d-%m-%Y-%H%M")


def generate_output_filename(
    protocol_json: dict,
    protocol_path: str,
    suffix: str = "RECONSTRUCTED"
) -> Tuple[str, str]:
    """
    Gera nome de arquivo de saída seguindo padrão Daktus Studio.
    
    Formato: {company}_{name}_v{version}_{timestamp}.json
    
    Args:
        protocol_json: Protocolo JSON (para extrair metadata)
        protocol_path: Caminho do protocolo original
        suffix: Sufixo para adicionar (ex: "RECONSTRUCTED") - não usado mais, mantido para compatibilidade
        
    Returns:
        Tupla (nome_arquivo, versão_incrementada)
    """
    from pathlib import Path
    
    metadata = protocol_json.get("metadata", {})
    company = metadata.get("company", "unknown")
    name = metadata.get("name", "protocol")
    
    # Extrair versão do protocolo
    current_version = extract_version_from_protocol(protocol_json)
    if not current_version:
        # Tentar extrair do filename
        current_version = extract_version_from_filename(Path(protocol_path).stem)
    
    if not current_version:
        current_version = "0.1.1"  # Fallback
    
    # Incrementar versão (PATCH para reconstruções)
    new_version = increment_version(current_version, increment_type="patch")
    
    # Gerar timestamp no formato Daktus: DD-MM-YYYY-HHMM
    timestamp = generate_daktus_timestamp()
    
    # Gerar nome do arquivo (sem sufixo RECONSTRUCTED, seguindo padrão Daktus)
    filename = f"{company}_{name}_v{new_version}_{timestamp}.json"
    
    return filename, new_version


def update_protocol_version(protocol_json: dict, new_version: str) -> dict:
    """
    Atualiza versão no metadata do protocolo.
    
    Args:
        protocol_json: Protocolo JSON
        new_version: Nova versão (formato "MAJOR.MINOR.PATCH")
        
    Returns:
        Protocolo com versão atualizada
    """
    if "metadata" not in protocol_json:
        protocol_json["metadata"] = {}
    
    protocol_json["metadata"]["version"] = new_version
    return protocol_json

