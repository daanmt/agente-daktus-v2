"""
Feedback Storage - Armazenamento de Feedback

Responsabilidades:
- Persistir feedback em formato estruturado (JSON)
- Facilitar análise de feedback histórico
- Suportar queries para análise de padrões

Estrutura de Armazenamento:
feedback_sessions/
  ├─ 202512/
  │   ├─ session_20251201_001.json
  │   ├─ session_20251201_002.json
  │   └─ ...
  └─ 202601/
      └─ ...

Fase de Implementação: FASE 2 (5-7 dias)
Status: ✅ Implementado
"""

import sys
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# Add src to path for imports
current_dir = Path(__file__).resolve().parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from agent_v2.logger import logger


class FeedbackStorage:
    """
    Gerencia persistência de feedback estruturado.

    Este componente armazena todo o feedback coletado em formato JSON
    para análise posterior e detecção de padrões.

    Example:
        >>> storage = FeedbackStorage()
        >>> storage.save_feedback_session(session)
        >>> sessions = storage.load_feedback_sessions(month="202512")
        >>> print(f"Sessões carregadas: {len(sessions)}")
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Inicializa o storage de feedback.

        Args:
            base_path: Caminho base para armazenamento (padrão: feedback_sessions/)
        """
        # Use project root as base
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.base_path = base_path or (project_root / "feedback_sessions")
        self.base_path.mkdir(exist_ok=True)
        
        logger.info(f"FeedbackStorage initialized: {self.base_path}")

    def save_feedback_session(
        self,
        session: Dict
    ) -> Path:
        """
        Salva uma sessão de feedback.

        Args:
            session: Sessão de feedback estruturada (FeedbackSession como dict)

        Returns:
            Path do arquivo salvo
        """
        # Gerar ID de sessão se não existir
        if "session_id" not in session or not session["session_id"]:
            session["session_id"] = self._generate_session_id()
        
        # Obter timestamp se não existir
        if "timestamp" not in session:
            session["timestamp"] = datetime.now().isoformat()
        
        # Converter datetime para string se necessário
        if isinstance(session.get("timestamp"), datetime):
            session["timestamp"] = session["timestamp"].isoformat()
        
        # Obter diretório do mês
        timestamp = session.get("timestamp", datetime.now().isoformat())
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        month_dir = self._get_month_directory(dt)
        month_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar nome do arquivo
        session_id = session["session_id"]
        filename = f"session_{session_id}.json"
        file_path = month_dir / filename
        
        # Salvar JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Feedback session saved: {file_path}")
        return file_path

    def load_feedback_sessions(
        self,
        month: Optional[str] = None,
        protocol_name: Optional[str] = None,
        model_used: Optional[str] = None
    ) -> List[Dict]:
        """
        Carrega sessões de feedback com filtros opcionais.

        Args:
            month: Filtrar por mês (ex: "202512")
            protocol_name: Filtrar por nome do protocolo
            model_used: Filtrar por modelo LLM

        Returns:
            Lista de sessões de feedback
        """
        sessions = []
        
        # Determinar diretórios a buscar
        if month:
            # Buscar apenas no mês especificado
            month_dir = self.base_path / month
            if month_dir.exists():
                search_dirs = [month_dir]
            else:
                logger.warning(f"Month directory not found: {month_dir}")
                return []
        else:
            # Buscar em todos os diretórios de mês
            search_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and d.name.isdigit()]
        
        # Carregar sessões
        for month_dir in search_dirs:
            for json_file in month_dir.glob("session_*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        session = json.load(f)
                    
                    # Aplicar filtros
                    if protocol_name and session.get("protocol_name") != protocol_name:
                        continue
                    if model_used and session.get("model_used") != model_used:
                        continue
                    
                    sessions.append(session)
                except Exception as e:
                    logger.error(f"Error loading session {json_file}: {e}")
        
        logger.info(f"Loaded {len(sessions)} feedback sessions")
        return sessions

    def query_feedback(
        self,
        verdict: Optional[str] = None,
        suggestion_category: Optional[str] = None,
        min_quality_rating: Optional[int] = None
    ) -> List[Dict]:
        """
        Busca feedback com critérios específicos.

        Args:
            verdict: Filtrar por veredito (relevant, irrelevant)
            suggestion_category: Filtrar por categoria de sugestão
            min_quality_rating: Filtrar por rating mínimo

        Returns:
            Lista de feedbacks que atendem aos critérios
        """
        # Carregar todas as sessões
        all_sessions = self.load_feedback_sessions()
        
        results = []
        for session in all_sessions:
            # Filtrar por quality_rating
            if min_quality_rating is not None:
                rating = session.get("quality_rating")
                if rating is None or rating < min_quality_rating:
                    continue
            
            # Filtrar sugestões dentro da sessão
            suggestions_feedback = session.get("suggestions_feedback", [])
            filtered_suggestions = []
            
            for sug_fb in suggestions_feedback:
                # Filtrar por veredito
                if verdict and sug_fb.get("user_verdict") != verdict:
                    continue
                
                # Filtrar por categoria (precisa buscar na sugestão original)
                # Por enquanto, não temos categoria no feedback, então pulamos
                if suggestion_category:
                    # TODO: Adicionar categoria ao feedback quando coletado
                    pass
                
                filtered_suggestions.append(sug_fb)
            
            # Se há filtros de sugestão, criar sessão filtrada
            if verdict or suggestion_category:
                if filtered_suggestions:
                    filtered_session = session.copy()
                    filtered_session["suggestions_feedback"] = filtered_suggestions
                    results.append(filtered_session)
            else:
                # Sem filtros de sugestão, adicionar sessão completa
                results.append(session)
        
        logger.info(f"Query returned {len(results)} sessions")
        return results

    def get_feedback_statistics(
        self,
        period: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Calcula estatísticas agregadas de feedback.

        Args:
            period: Período para análise (ex: "202512")

        Returns:
            Dict com estatísticas:
            - total_sessions: Total de sessões
            - avg_quality_rating: Rating médio
            - relevant_rate: Taxa de relevância
            - irrelevant_rate: Taxa de irrelevância
            - most_rejected_categories: Categorias mais rejeitadas
        """
        sessions = self.load_feedback_sessions(month=period)
        
        if not sessions:
            return {
                "total_sessions": 0,
                "avg_quality_rating": 0.0,
                "relevant_rate": 0.0,
                "irrelevant_rate": 0.0,
                "most_rejected_categories": []
            }
        
        # Calcular estatísticas
        total_sessions = len(sessions)
        
        # Quality ratings
        ratings = [s.get("quality_rating") for s in sessions if s.get("quality_rating") is not None]
        avg_quality_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Veredictos
        total_suggestions = 0
        relevant_count = 0
        irrelevant_count = 0
        category_rejections = {}
        
        for session in sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                total_suggestions += 1
                verdict = sug_fb.get("user_verdict", "")
                
                if verdict == "relevant":
                    relevant_count += 1
                elif verdict == "irrelevant":
                    irrelevant_count += 1
                    # Contar rejeições por categoria (se disponível)
                    category = sug_fb.get("category")
                    if category:
                        category_rejections[category] = category_rejections.get(category, 0) + 1
        
        relevant_rate = (relevant_count / total_suggestions * 100) if total_suggestions > 0 else 0.0
        irrelevant_rate = (irrelevant_count / total_suggestions * 100) if total_suggestions > 0 else 0.0
        
        # Categorias mais rejeitadas
        most_rejected = sorted(
            category_rejections.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        stats = {
            "total_sessions": total_sessions,
            "avg_quality_rating": round(avg_quality_rating, 2),
            "relevant_rate": round(relevant_rate, 2),
            "irrelevant_rate": round(irrelevant_rate, 2),
            "most_rejected_categories": [{"category": cat, "count": count} for cat, count in most_rejected]
        }
        
        logger.info(f"Feedback statistics calculated: {stats}")
        return stats

    def _generate_session_id(self) -> str:
        """
        Gera ID único para sessão de feedback.

        Returns:
            Session ID (ex: "fb-20251201-001")
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        
        # Buscar último número do dia
        month_dir = self._get_month_directory(now)
        if month_dir.exists():
            existing_files = list(month_dir.glob(f"session_fb-{date_str}-*.json"))
            if existing_files:
                # Extrair números e encontrar o maior
                numbers = []
                for f in existing_files:
                    try:
                        # Formato: session_fb-YYYYMMDD-NNN.json
                        num_str = f.stem.split('-')[-1]
                        numbers.append(int(num_str))
                    except:
                        pass
                next_num = max(numbers) + 1 if numbers else 1
            else:
                next_num = 1
        else:
            next_num = 1
        
        session_id = f"fb-{date_str}-{next_num:03d}"
        return session_id

    def _get_month_directory(
        self,
        date: datetime
    ) -> Path:
        """
        Retorna diretório do mês para uma data.

        Args:
            date: Data de referência

        Returns:
            Path do diretório (ex: feedback_sessions/202512/)
        """
        month_str = date.strftime("%Y%m")
        month_dir = self.base_path / month_str
        return month_dir
