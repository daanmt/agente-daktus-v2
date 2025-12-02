"""
Simple Protocol Loader - Load JSON files only
No parsing, no validation, just file loading
"""

import json
from pathlib import Path
from typing import Dict, Optional

from .logger import logger


def load_protocol(protocol_path: str) -> Dict:
    """
    Load protocol JSON file.
    
    Simple file loading - NO parsing, NO validation.
    
    Args:
        protocol_path: Path to protocol JSON file
        
    Returns:
        Protocol as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(protocol_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
    
    logger.info(f"Loading protocol from: {protocol_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Remove trailing semicolons or other extra data
            content = content.strip().rstrip(';')
            protocol = json.loads(content)
        
        logger.info(f"Protocol loaded: {len(protocol.get('nodes', []))} nodes")
        return protocol
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in protocol {protocol_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading protocol {protocol_path}: {e}")
        raise


def load_playbook(playbook_path: str) -> str:
    """
    Load playbook file (markdown, text, or PDF).
    
    Simple file loading - NO parsing, NO extraction.
    
    Args:
        playbook_path: Path to playbook file
        
    Returns:
        Playbook content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(playbook_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Playbook file not found: {playbook_path}")
    
    logger.info(f"Loading playbook from: {playbook_path}")
    
    # Handle PDF files
    if path.suffix.lower() == '.pdf':
        try:
            import PyPDF2
            with open(path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                content = '\n\n'.join(text_parts)
        except ImportError:
            logger.warning("PyPDF2 not available, cannot read PDF")
            raise ImportError("PyPDF2 required for PDF playbooks. Install with: pip install PyPDF2")
        except Exception as e:
            logger.error(f"Error reading PDF {playbook_path}: {e}")
            raise
    else:
        # Handle text/markdown files
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error loading playbook {playbook_path}: {e}")
            raise
    
    logger.info(f"Playbook loaded: {len(content)} characters")
    return content

