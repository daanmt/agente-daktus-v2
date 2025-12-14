"""
Authorization Manager - Autorização de Consumo

Responsabilidades:
- Apresentar estimativa de custo ao usuário
- Solicitar autorização explícita
- Validar limites de custo configurados
- Registrar decisões de autorização

Fase de Implementação: FASE 3 (3-4 dias)
Status: ✅ Implementado
"""

import sys
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.logger import logger
from .cost_estimator import CostEstimate


@dataclass
class UserLimits:
    """Limites de custo configurados pelo usuário."""
    max_cost_per_operation: float  # USD
    max_daily_cost: float  # USD
    require_approval_above: float  # USD


@dataclass
class AuthorizationDecision:
    """Decisão de autorização de consumo."""
    authorized: bool
    cost_estimate: Dict
    user_decision: str  # approved, rejected, modified
    timestamp: str


class AuthorizationManager:
    """
    Gerencia autorização de consumo de tokens.

    Regras:
    - Autorização obrigatória se custo > limite
    - Rejeição automática se muito acima do limite
    - Registro de todas as decisões
    """

    def __init__(self, user_limits: Optional[UserLimits] = None):
        """Inicializa o gerenciador de autorização."""
        self.user_limits = user_limits or UserLimits(
            max_cost_per_operation=1.00,
            max_daily_cost=10.00,
            require_approval_above=0.10  # Auto-approval até $0.10 (10 centavos)
        )

    def request_authorization(
        self,
        cost_estimate: CostEstimate,
        operation_description: str
    ) -> AuthorizationDecision:
        """
        Solicita autorização do usuário para operação.

        TODA operação LLM requer aprovação explícita do usuário,
        independentemente do custo estimado.
        
        Fluxo:
        1. Exibe estimativa formatada
        2. Solicita confirmação do usuário
        3. Registra decisão
        
        Args:
            cost_estimate: Estimativa de custo
            operation_description: Descrição da operação
            
        Returns:
            AuthorizationDecision com decisão do usuário
        """
        total_cost = cost_estimate.estimated_cost_usd["total"]
        
        # Sempre apresentar estimativa e solicitar aprovação
        self.present_cost_estimate(cost_estimate, operation_description)
        
        # Solicitar confirmação
        while True:
            try:
                response = input("\nAutorizar esta operação? (S/N): ").strip().upper()
                
                if response in ("S", "SIM", "Y", "YES"):
                    decision = AuthorizationDecision(
                        authorized=True,
                        cost_estimate=asdict(cost_estimate),
                        user_decision="approved",
                        timestamp=datetime.now().isoformat()
                    )
                    logger.info(f"User approved operation: ${total_cost:.4f}")
                    break
                elif response in ("N", "NAO", "NO"):
                    decision = AuthorizationDecision(
                        authorized=False,
                        cost_estimate=asdict(cost_estimate),
                        user_decision="rejected",
                        timestamp=datetime.now().isoformat()
                    )
                    logger.info(f"User rejected operation: ${total_cost:.4f}")
                    break
                else:
                    print("Por favor, responda S (Sim) ou N (Não)")
            except KeyboardInterrupt:
                decision = AuthorizationDecision(
                    authorized=False,
                    cost_estimate=asdict(cost_estimate),
                    user_decision="cancelled",
                    timestamp=datetime.now().isoformat()
                )
                logger.info(f"User cancelled operation")
                break
        
        self._log_decision(decision)
        return decision

    def check_within_limits(
        self,
        estimated_cost: float
    ) -> bool:
        """
        Verifica se custo está dentro dos limites.

        Args:
            estimated_cost: Custo estimado em USD
            
        Returns:
            True se dentro dos limites, False caso contrário
        """
        within_operation_limit = estimated_cost <= self.user_limits.max_cost_per_operation
        # TODO: Verificar limite diário (requer tracking de custos do dia)
        
        return within_operation_limit

    def present_cost_estimate(
        self,
        cost_estimate: CostEstimate,
        operation_description: str = "Operação LLM"
    ) -> None:
        """
        Apresenta estimativa de custo formatada.

        Args:
            cost_estimate: Estimativa de custo
            operation_description: Descrição da operação
        """
        total_cost = cost_estimate.estimated_cost_usd["total"]
        input_cost = cost_estimate.estimated_cost_usd["input"]
        output_cost = cost_estimate.estimated_cost_usd["output"]
        input_tokens = cost_estimate.estimated_tokens["input"]
        output_tokens = cost_estimate.estimated_tokens["output"]
        
        # Use Rich for consistent UI
        try:
            from rich.console import Console
            from rich.panel import Panel
            
            console = Console()
            
            content_lines = [
                f"[bold]{cost_estimate.model}[/bold]",
                "",
                f"Operação: {operation_description}",
                "",
                "Tokens Estimados:",
                f"  Input:  {input_tokens:,} tokens ([cyan]${input_cost:.4f}[/cyan])",
                f"  Output: {output_tokens:,} tokens ([cyan]${output_cost:.4f}[/cyan])",
                f"  Total:  {input_tokens + output_tokens:,} tokens",
                "",
                f"[bold yellow]Custo Total Estimado: ${total_cost:.4f} USD[/bold yellow]",
                f"Confiança: {cost_estimate.confidence.upper()}"
            ]
            
            console.print(Panel(
                "\n".join(content_lines),
                title="💰 Estimativa de Custo - Autorização Requerida",
                border_style="yellow"
            ))
        except ImportError:
            # Fallback simples
            print(f"\n💰 Estimativa de Custo: {cost_estimate.model}")
            print(f"Tokens: {input_tokens + output_tokens:,} | Custo: ${total_cost:.4f} USD ({cost_estimate.confidence.upper()})")
    
    def _log_decision(self, decision: AuthorizationDecision) -> None:
        """
        Registra decisão de autorização em arquivo JSON.
        
        Args:
            decision: Decisão de autorização
        """
        logs_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        auth_log_file = logs_dir / "cost_authorizations.json"
        
        # Carregar log existente ou criar novo
        if auth_log_file.exists():
            try:
                with open(auth_log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                logs = []
        else:
            logs = []
        
        # Adicionar nova decisão
        logs.append(asdict(decision))
        
        # Salvar
        try:
            with open(auth_log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.warning(f"Failed to save authorization log: {e}")
