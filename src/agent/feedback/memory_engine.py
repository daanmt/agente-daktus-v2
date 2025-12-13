"""
Memory Engine V2 - Sistema de Memória Estruturada com Filtros Semânticos

Este módulo transforma memory_qa.md de um log textual em uma base de conhecimento
estruturada que previne sugestões repetidas através de:
- Regras de aceitação/rejeição persistentes
- Filtros semânticos para sugestões similares
- Integração transparente com Enhanced Analyzer e Feedback Collector

Fase: Enhancement da Fase 2 (Sistema de Feedback)
Status: ✅ Implementado
"""

import sys
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
current_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from ..core.logger import logger
from ..core.llm_client import LLMClient

# Embeddings for semantic similarity - DISABLED
# Using simple text-based Jaccard similarity instead (always works offline)
# The sentence_transformers library causes network issues even with HF_HUB_OFFLINE=1
# because it still tries to validate cached models against remote servers

_EMBEDDINGS_AVAILABLE = False
SentenceTransformer = None
np = None


@dataclass
class MemoryRule:
    """
    Regra de memória estruturada para aceitação/rejeição de sugestões.
    """
    rule_id: str
    text: str  # Texto da sugestão (normalizado)
    decision: str  # "accepted" ou "rejected"
    protocol_id: str
    model_id: str
    timestamp: str
    comment: Optional[str] = None
    suggestion_id: Optional[str] = None  # ID original da sugestão
    category: Optional[str] = None
    priority: Optional[str] = None
    keywords: Optional[List[str]] = None  # Keywords para agrupamento (opcional)


class MemoryEngine:
    """
    Motor de memória estruturada que previne sugestões repetidas.
    
    Responsabilidades:
    - Carregar e salvar regras estruturadas em memory_qa.md
    - Registrar feedback como regras reutilizáveis
    - Filtrar sugestões baseado em regras exatas e similaridade semântica
    """
    
    def __init__(self, memory_file: Optional[Path] = None):
        """
        Inicializa o Memory Engine.
        
        Args:
            memory_file: Caminho para memory_qa.md (padrão: project_root/memory_qa.md)
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.memory_file = memory_file or (project_root / "memory_qa.md")
        
        # Estado interno
        self.rules_accepted: List[MemoryRule] = []
        self.rules_rejected: List[MemoryRule] = []
        self.vector_index: List[Dict] = []  # Para futuras expansões com embeddings
        
        # Similarity threshold (ajustável)
        self.similarity_threshold = 0.85
        
        # Embeddings model para similaridade semântica (preferencial)
        self.embedder: Optional[Any] = None
        if _EMBEDDINGS_AVAILABLE:
            try:
                # Tentar carregar modelo (usando cache local - offline mode setado no topo do módulo)
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Embeddings model loaded from cache: all-MiniLM-L6-v2")
            except Exception as e:
                # Se não conseguir carregar (offline ou não cached), usa fallback
                logger.warning(f"SentenceTransformer not available (offline/no cache): {e}. Using text matching fallback.")
                self.embedder = None
        
        # LLM client para similaridade semântica (fallback se embeddings não disponível)
        self.llm_client: Optional[LLMClient] = None
        
        # Cache de embeddings para performance
        self._embedding_cache: Dict[str, Any] = {}
        
        logger.info(f"MemoryEngine initialized: {self.memory_file} (embeddings: {self.embedder is not None})")
    
    def _extract_json_block(self, content: str, section_name: str) -> List[Dict]:
        """
        Parser robusto baseado em delimitadores fixos (TASK 2).
        
        Args:
            content: Conteúdo completo do arquivo
            section_name: Nome da seção (RULES_ACCEPTED, RULES_REJECTED, VECTOR_INDEX)
            
        Returns:
            Lista de dicionários parseados (ou lista vazia em caso de erro)
        """
        start_marker = f"### {section_name}\n```json\n"
        end_marker = "\n```"
        
        try:
            start_idx = content.index(start_marker)
            start_idx += len(start_marker)
            end_idx = content.index(end_marker, start_idx)
            json_str = content[start_idx:end_idx]
            
            # Validar e parsear JSON
            parsed = json.loads(json_str)
            if not isinstance(parsed, list):
                logger.warning(f"{section_name} is not a list, converting...")
                parsed = [parsed] if parsed else []
            
            return parsed
        except ValueError:
            # Seção não encontrada - não é erro, pode não existir ainda
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {section_name} JSON: {e}. Returning empty list.")
            return []
        except Exception as e:
            logger.warning(f"Unexpected error parsing {section_name}: {e}. Returning empty list.")
            return []
    
    def load_memory(self) -> None:
        """
        Carrega regras estruturadas de memory_qa.md.
        
        Lê as seções:
        - ### RULES_ACCEPTED
        - ### RULES_REJECTED
        - ### VECTOR_INDEX (opcional)
        
        Se as seções não existirem, inicializa estrutura vazia.
        Usa parser robusto baseado em delimitadores fixos (TASK 2).
        """
        if not self.memory_file.exists():
            logger.info("memory_qa.md does not exist, will initialize on first save")
            self.rules_accepted = []
            self.rules_rejected = []
            self.vector_index = []
            return
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extrair seção RULES_ACCEPTED usando parser robusto
            try:
                rules_data = self._extract_json_block(content, "RULES_ACCEPTED")
                # Converter regras, tratando campos opcionais
                parsed_rules = []
                for rule in rules_data:
                    # Remover campos que não existem no dataclass
                    rule_clean = {k: v for k, v in rule.items() if k in ['rule_id', 'text', 'decision', 'protocol_id', 'model_id', 'timestamp', 'comment', 'suggestion_id', 'category', 'priority', 'keywords']}
                    parsed_rules.append(MemoryRule(**rule_clean))
                self.rules_accepted = parsed_rules
                logger.info(f"Loaded {len(self.rules_accepted)} accepted rules")
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to parse RULES_ACCEPTED: {e}")
                self.rules_accepted = []
            
            # Extrair seção RULES_REJECTED usando parser robusto
            try:
                rules_data = self._extract_json_block(content, "RULES_REJECTED")
                # Converter regras, tratando campos opcionais
                parsed_rules = []
                for rule in rules_data:
                    # Remover campos que não existem no dataclass
                    rule_clean = {k: v for k, v in rule.items() if k in ['rule_id', 'text', 'decision', 'protocol_id', 'model_id', 'timestamp', 'comment', 'suggestion_id', 'category', 'priority', 'keywords']}
                    parsed_rules.append(MemoryRule(**rule_clean))
                self.rules_rejected = parsed_rules
                logger.info(f"Loaded {len(self.rules_rejected)} rejected rules")
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to parse RULES_REJECTED: {e}")
                self.rules_rejected = []
            
            # Extrair seção VECTOR_INDEX (opcional)
            try:
                self.vector_index = self._extract_json_block(content, "VECTOR_INDEX")
                logger.info(f"Loaded {len(self.vector_index)} vector index entries")
            except Exception as e:
                logger.warning(f"Failed to parse VECTOR_INDEX: {e}")
                self.vector_index = []
            
            logger.info(
                f"Memory loaded: {len(self.rules_accepted)} accepted, "
                f"{len(self.rules_rejected)} rejected rules"
            )
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}", exc_info=True)
            # Degradação graciosa: inicializar com listas vazias
            self.rules_accepted = []
            self.rules_rejected = []
            self.vector_index = []
    
    def save_memory(self) -> None:
        """
        Salva regras estruturadas de volta em memory_qa.md (TASK 4 - preservação garantida).
        
        Preserva o histórico textual existente usando marcador fixo.
        Usa operação atômica para evitar corrupção de arquivo.
        """
        # Marcador fixo e padronizado para separar estrutura/histórico
        HISTORY_MARKER = "\n\n---\n## Feedback Histórico\n\n"
        
        try:
            # Ler conteúdo existente
            existing_content = ""
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # Extrair histórico existente (TASK 4 - preservação garantida)
            history_content = ""
            if HISTORY_MARKER in existing_content:
                # Histórico após marcador
                _, history_content = existing_content.split(HISTORY_MARKER, 1)
            elif "## Feedback Histórico" in existing_content:
                # Fallback: buscar histórico mesmo sem marcador exato
                history_idx = existing_content.find("## Feedback Histórico")
                history_content = existing_content[history_idx:]
            elif existing_content:
                # Se não tem marcador, tentar preservar tudo após seções estruturadas
                # Remover seções estruturadas se existirem
                content_without_structured = re.sub(
                    r'### RULES_ACCEPTED.*?```\s*\n',
                    '',
                    existing_content,
                    flags=re.DOTALL
                )
                content_without_structured = re.sub(
                    r'### RULES_REJECTED.*?```\s*\n',
                    '',
                    content_without_structured,
                    flags=re.DOTALL
                )
                content_without_structured = re.sub(
                    r'### VECTOR_INDEX.*?```\s*\n',
                    '',
                    content_without_structured,
                    flags=re.DOTALL
                )
                # Preservar conteúdo que não é seção estruturada
                if content_without_structured.strip():
                    history_content = content_without_structured.strip()
                    # Adicionar marcador se não tiver
                    if not history_content.startswith("## Feedback Histórico"):
                        history_content = "## Feedback Histórico\n\n" + history_content
            
            # Se não tem histórico, criar estrutura mínima
            if not history_content.strip():
                history_content = "---\n"
            
            # Construir novo conteúdo
            new_content = """# Memory QA - Feedback e Aprendizados do Agente Daktus QA

Este documento concentra todos os feedbacks e aprendizados do agente para refinar futuras análises.

## Como Funciona

Antes de cada análise, o agente revisa este documento para entender:
- Quais tipos de sugestões foram rejeitadas e por quê
- Quais padrões de feedback indicam problemas recorrentes
- Como melhorar a qualidade e relevância das sugestões

---

## Memória Estruturada (Memory Engine V2)

As seções abaixo contêm regras estruturadas que são usadas para filtrar sugestões repetidas.

### RULES_ACCEPTED

```json
{accepted_rules_json}
```

### RULES_REJECTED

```json
{rejected_rules_json}
```

### VECTOR_INDEX

```json
{vector_index_json}
```

{history_marker}{history_content}
"""
            
            # Serializar regras
            accepted_rules_json = json.dumps(
                [asdict(rule) for rule in self.rules_accepted],
                indent=2,
                ensure_ascii=False
            )
            rejected_rules_json = json.dumps(
                [asdict(rule) for rule in self.rules_rejected],
                indent=2,
                ensure_ascii=False
            )
            vector_index_json = json.dumps(
                self.vector_index,
                indent=2,
                ensure_ascii=False
            )
            
            # Substituir placeholders
            new_content = new_content.format(
                accepted_rules_json=accepted_rules_json,
                rejected_rules_json=rejected_rules_json,
                vector_index_json=vector_index_json,
                history_marker=HISTORY_MARKER,
                history_content=history_content
            )
            
            # Backup antes de salvar (TASK 4 - segurança extra)
            if self.memory_file.exists():
                backup_file = self.memory_file.with_suffix('.md.backup')
                import shutil
                shutil.copy2(self.memory_file, backup_file)
                # Manter apenas último backup
                if backup_file.exists():
                    old_backup = self.memory_file.with_suffix('.md.backup.old')
                    if old_backup.exists():
                        old_backup.unlink()
                    backup_file.rename(old_backup)
                    shutil.copy2(self.memory_file, backup_file)
            
            # Operação atômica: escrever em arquivo temporário, depois mover
            temp_file = self.memory_file.with_suffix('.md.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Mover atomically
            import shutil
            shutil.move(str(temp_file), str(self.memory_file))
            
            logger.info(
                f"Memory saved: {len(self.rules_accepted)} accepted, "
                f"{len(self.rules_rejected)} rejected rules"
            )
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}", exc_info=True)
            # TASK 6: Degradação graciosa - não quebrar o pipeline
            logger.warning("Memory save failed, but continuing without saving")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparação (lowercase, remove pontuação extra).
        
        Args:
            text: Texto a normalizar
            
        Returns:
            Texto normalizado
        """
        # Lowercase
        normalized = text.lower()
        # Remove pontuação extra e espaços múltiplos
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()
    
    def _generate_rule_id(self, suggestion_text: str, protocol_id: str) -> str:
        """
        Gera ID estável para uma regra baseado no texto e protocolo.
        
        Args:
            suggestion_text: Texto da sugestão
            protocol_id: ID do protocolo
            
        Returns:
            Hash estável (rule_id)
        """
        normalized = self._normalize_text(suggestion_text)
        combined = f"{normalized}::{protocol_id}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    def register_feedback(
        self,
        suggestion: Union[Dict, Any],
        decision: str,
        comment: str,
        protocol_id: str,
        model_id: str
    ) -> None:
        """
        Registra feedback como regra estruturada.
        
        Args:
            suggestion: Objeto de sugestão (Dict ou objeto com atributos)
            decision: "S" (relevant/accepted) ou "N" (irrelevant/rejected)
            comment: Comentário opcional do usuário
            protocol_id: ID do protocolo
            model_id: ID do modelo usado
        """
        # Extrair dados da sugestão
        if isinstance(suggestion, dict):
            suggestion_id = suggestion.get('id', 'unknown')
            title = suggestion.get('title', '')
            description = suggestion.get('description', '')
            category = suggestion.get('category')
            priority = suggestion.get('priority')
        else:
            # Objeto com atributos
            suggestion_id = getattr(suggestion, 'id', 'unknown')
            title = getattr(suggestion, 'title', '')
            description = getattr(suggestion, 'description', '')
            category = getattr(suggestion, 'category', None)
            priority = getattr(suggestion, 'priority', None)
        
        # Combinar título e descrição para texto completo
        suggestion_text = f"{title}. {description}".strip()
        if not suggestion_text:
            logger.warning(f"Cannot register feedback: suggestion text is empty (id: {suggestion_id})")
            return
        
        # Gerar rule_id
        rule_id = self._generate_rule_id(suggestion_text, protocol_id)
        
        # Normalizar decisão
        decision_normalized = "accepted" if decision.upper() == "S" else "rejected"
        
        # Criar regra
        rule = MemoryRule(
            rule_id=rule_id,
            text=suggestion_text,
            decision=decision_normalized,
            protocol_id=protocol_id,
            model_id=model_id,
            timestamp=datetime.now().isoformat(),
            comment=comment or None,
            suggestion_id=suggestion_id,
            category=category,
            priority=priority
        )
        
        # Adicionar à lista apropriada
        if decision_normalized == "accepted":
            # Remover duplicatas (mesmo rule_id)
            self.rules_accepted = [r for r in self.rules_accepted if r.rule_id != rule_id]
            self.rules_accepted.append(rule)
            logger.info(f"Registered accepted rule: {rule_id} ({suggestion_id})")
        else:
            # Remover duplicatas (mesmo rule_id)
            self.rules_rejected = [r for r in self.rules_rejected if r.rule_id != rule_id]
            self.rules_rejected.append(rule)
            logger.info(f"Registered rejected rule: {rule_id} ({suggestion_id})")
    
    def _exact_match_filter(
        self,
        suggestion_text: str,
        rejected_rules: List[MemoryRule]
    ) -> Optional[MemoryRule]:
        """
        Verifica se sugestão corresponde exatamente a uma regra rejeitada.
        
        Args:
            suggestion_text: Texto da sugestão
            rejected_rules: Lista de regras rejeitadas
            
        Returns:
            Regra correspondente ou None
        """
        normalized_suggestion = self._normalize_text(suggestion_text)
        
        for rule in rejected_rules:
            normalized_rule = self._normalize_text(rule.text)
            
            # Match exato
            if normalized_suggestion == normalized_rule:
                return rule
            
            # Match de substring (sugestão contém regra ou vice-versa)
            if len(normalized_suggestion) > 20 and len(normalized_rule) > 20:
                if normalized_suggestion in normalized_rule or normalized_rule in normalized_suggestion:
                    return rule
        
        return None
    
    def _compute_similarity_embeddings(self, text1: str, text2: str) -> float:
        """
        Computa similaridade semântica usando embeddings (TASK 1 - método preferencial).
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score de similaridade (0.0-1.0) via cosine similarity
        """
        if not self.embedder:
            return 0.0
        
        try:
            # Cache de embeddings para performance
            cache_key1 = hashlib.md5(text1.encode('utf-8')).hexdigest()
            cache_key2 = hashlib.md5(text2.encode('utf-8')).hexdigest()
            
            if cache_key1 in self._embedding_cache:
                emb1 = self._embedding_cache[cache_key1]
            else:
                emb1 = self.embedder.encode(text1, convert_to_tensor=True)
                self._embedding_cache[cache_key1] = emb1
            
            if cache_key2 in self._embedding_cache:
                emb2 = self._embedding_cache[cache_key2]
            else:
                emb2 = self.embedder.encode(text2, convert_to_tensor=True)
                self._embedding_cache[cache_key2] = emb2
            
            # Cosine similarity
            similarity = float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
            return max(0.0, min(1.0, similarity))  # Clamp entre 0 e 1
            
        except Exception as e:
            logger.warning(f"Failed to compute embeddings similarity: {e}")
            return 0.0
    
    def _compute_similarity_llm(self, text1: str, text2: str) -> float:
        """
        Computa similaridade semântica usando LLM (fallback se embeddings não disponível).
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score de similaridade (0.0-1.0)
        """
        if not self.llm_client:
            try:
                # Usar modelo estável (Gemini) em vez de Grok
                self.llm_client = LLMClient(model="google/gemini-2.0-flash-exp:free")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                return 0.0
        
        prompt = f"""You are a similarity scorer. Compare these two texts and return ONLY a number between 0.0 and 1.0 representing their semantic similarity.

0.0 = completely different topics
1.0 = essentially the same meaning

TEXT1: {text1[:500]}

TEXT2: {text2[:500]}

Return ONLY the number, no explanation."""

        try:
            # Usar _run_with_auto_continue (método existe no LLMClient)
            response_text = self.llm_client._run_with_auto_continue(
                prompt,
                max_tokens=50  # We only need a number
            )
            
            # Extrair número da resposta
            match = re.search(r'0?\.\d+|1\.0|0', response_text.strip())
            if match:
                score = float(match.group(0))
                return max(0.0, min(1.0, score))  # Clamp entre 0 e 1
            else:
                logger.warning(f"Could not parse similarity score from LLM response: {response_text[:100]}")
                return 0.0
        except Exception as e:
            logger.warning(f"Failed to compute LLM similarity: {e}")
            return 0.0
    
    def _compute_similarity_text(self, text1: str, text2: str) -> float:
        """
        Computa similaridade usando matching de texto simples (fallback offline).
        
        Usa contagem de palavras em comum dividido pelo total de palavras únicas.
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score de similaridade (0.0-1.0) baseado em Jaccard de palavras
        """
        # Normalizar e tokenizar
        words1 = set(self._normalize_text(text1).split())
        words2 = set(self._normalize_text(text2).split())
        
        # Remover palavras muito curtas (stopwords)
        words1 = {w for w in words1 if len(w) > 2}
        words2 = {w for w in words2 if len(w) > 2}
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Computa similaridade semântica (TASK 1 - wrapper com fallback robusto).
        
        Tenta embeddings primeiro, depois LLM, depois texto simples.
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score de similaridade (0.0-1.0)
        """
        # Tentar embeddings primeiro (rápido e determinístico)
        if self.embedder:
            try:
                return self._compute_similarity_embeddings(text1, text2)
            except Exception as e:
                logger.debug(f"Embeddings similarity failed: {e}, trying fallbacks")
        
        # Fallback para LLM (se disponível e online)
        try:
            llm_score = self._compute_similarity_llm(text1, text2)
            if llm_score > 0:
                return llm_score
        except Exception as e:
            logger.debug(f"LLM similarity failed: {e}, using text fallback")
        
        # Fallback final: matching de texto simples (always works)
        return self._compute_similarity_text(text1, text2)
    
    def _semantic_similarity_filter(
        self,
        suggestion_text: str,
        rejected_rules: List[MemoryRule]
    ) -> Tuple[Optional[MemoryRule], float]:
        """
        Verifica se sugestão é semanticamente similar a uma regra rejeitada (TASK 1 - usa embeddings).
        
        Args:
            suggestion_text: Texto da sugestão
            rejected_rules: Lista de regras rejeitadas
        
        Returns:
            (Regra similar, score de similaridade) ou (None, 0.0)
        """
        if not rejected_rules:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for rule in rejected_rules:
            try:
                # Usar método unificado com fallback
                score = self._compute_similarity(suggestion_text, rule.text)
                if score > best_score:
                    best_score = score
                    best_match = rule if score >= self.similarity_threshold else None
            except Exception as e:
                # TASK 6: Degradação graciosa - se uma comparação falhar, continua
                logger.debug(f"Similarity computation failed for rule {rule.rule_id}: {e}")
                continue
        
        return best_match, best_score
    
    def filter_suggestions(
        self,
        suggestions: List[Union[Dict, Any]]
    ) -> Tuple[List[Union[Dict, Any]], Dict[str, Any]]:
        """
        Filtra sugestões baseado em regras de memória (TASK 6 - com degradação graciosa).
        
        Args:
            suggestions: Lista de sugestões a filtrar
        
        Returns:
            (sugestões_filtradas, debug_info)
            
        Sempre retorna uma lista válida, mesmo se houver erros.
        """
        if not suggestions:
            return [], {"filtered_count": 0, "exact_matches": [], "semantic_matches": [], "reinforced_by_memory": [], "errors": []}
        
        filtered = []
        debug_info = {
            "filtered_count": 0,
            "exact_matches": [],
            "semantic_matches": [],
            "reinforced_by_memory": [],
            "errors": []
        }
        
        for suggestion in suggestions:
            try:
                # Extrair texto da sugestão
                if isinstance(suggestion, dict):
                    suggestion_id = suggestion.get('id', 'unknown')
                    title = suggestion.get('title', '')
                    description = suggestion.get('description', '')
                else:
                    suggestion_id = getattr(suggestion, 'id', 'unknown')
                    title = getattr(suggestion, 'title', '')
                    description = getattr(suggestion, 'description', '')
                
                suggestion_text = f"{title}. {description}".strip()
                if not suggestion_text:
                    # Manter sugestões sem texto (não podemos filtrar)
                    filtered.append(suggestion)
                    continue
                
                # Filtro 1: Match exato
                exact_match = self._exact_match_filter(suggestion_text, self.rules_rejected)
                if exact_match:
                    debug_info["exact_matches"].append({
                        "suggestion_id": suggestion_id,
                        "rule_id": exact_match.rule_id,
                        "reason": "exact_match"
                    })
                    debug_info["filtered_count"] += 1
                    logger.debug(f"Filtered suggestion {suggestion_id}: exact match with rejected rule {exact_match.rule_id}")
                    continue
                
                # Filtro 2: Similaridade semântica (TASK 6 - com fallback)
                try:
                    semantic_match, similarity_score = self._semantic_similarity_filter(
                        suggestion_text,
                        self.rules_rejected
                    )
                    if semantic_match:
                        debug_info["semantic_matches"].append({
                            "suggestion_id": suggestion_id,
                            "rule_id": semantic_match.rule_id,
                            "similarity_score": similarity_score,
                            "reason": "semantic_similarity"
                        })
                        debug_info["filtered_count"] += 1
                        logger.debug(
                            f"Filtered suggestion {suggestion_id}: semantic similarity {similarity_score:.2f} "
                            f"with rejected rule {semantic_match.rule_id}"
                        )
                        continue
                except Exception as e:
                    # TASK 6: Degradação graciosa - se similaridade falhar, continua sem filtrar
                    logger.warning(f"Semantic similarity filter failed for suggestion {suggestion_id}: {e}")
                    debug_info.setdefault("errors", []).append(f"Similarity failed: {e}")
                
                # Verificar se é similar a regra aceita (para reforço, não filtro)
                try:
                    accepted_match, accepted_score = self._semantic_similarity_filter(
                        suggestion_text,
                        self.rules_accepted
                    )
                    if accepted_match and accepted_score >= 0.8:
                        debug_info["reinforced_by_memory"].append({
                            "suggestion_id": suggestion_id,
                            "rule_id": accepted_match.rule_id,
                            "similarity_score": accepted_score
                        })
                except Exception as e:
                    # Ignorar erro no reforço (não crítico)
                    logger.debug(f"Reinforcement check failed: {e}")
                
                # Passou todos os filtros
                filtered.append(suggestion)
            except Exception as e:
                # TASK 6: Se tudo falhar, passa a sugestão (degradação graciosa)
                logger.warning(f"Filter error for suggestion: {e}. Passing suggestion through.")
                debug_info["errors"].append(f"Filter error: {e}")
                filtered.append(suggestion)
        
        logger.info(
            f"Memory filtering: {len(suggestions)} → {len(filtered)} suggestions "
            f"({debug_info['filtered_count']} filtered: {len(debug_info['exact_matches'])} exact, "
            f"{len(debug_info['semantic_matches'])} semantic, {len(debug_info.get('errors', []))} errors)"
        )
        
        return filtered, debug_info

