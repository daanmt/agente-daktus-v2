"""
Cost Tracker - Real-time tracking of actual API costs.

Wave 3 Implementation - TASK 3.1

Problem solved:
- Estimates were showing ~$0.07, actual was ~$1.00
- No visibility into cumulative session costs
- No comparison of estimate vs actual
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..core.logger import logger


@dataclass
class APICallRecord:
    """Record of a single API call."""
    timestamp: str
    model: str
    operation: str  # "analysis", "reconstruction", "feedback"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int = 0


@dataclass
class SessionMetrics:
    """Cumulative metrics for a session."""
    session_id: str
    start_time: str
    model: str
    protocol_name: str = ""
    
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    
    calls: List[APICallRecord] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'model': self.model,
            'protocol_name': self.protocol_name,
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
            'total_cost_usd': self.total_cost_usd,
            'breakdown': [
                {'op': c.operation, 'tokens': c.total_tokens, 'cost': c.cost_usd}
                for c in self.calls
            ]
        }


class CostTracker:
    """
    Singleton tracker for real-time API costs.
    
    Usage:
        tracker = CostTracker.get_instance()
        tracker.start_session("anthropic/claude-sonnet-4.5", "protocol_name")
        tracker.record_usage("analysis", usage_dict, latency_ms)
        summary = tracker.get_session_summary()
    """
    
    _instance = None
    
    # Model pricing (USD per 1M tokens)
    MODEL_PRICING = {
        "google/gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
        "google/gemini-2.5-flash": {"input": 0.30, "output": 2.50},
        "google/gemini-2.5-flash-preview-09-2025": {"input": 0.30, "output": 2.50},
        "google/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
        "anthropic/claude-sonnet-4.5": {"input": 3.0, "output": 15.0},
        "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "anthropic/claude-opus-4.5": {"input": 5.0, "output": 25.0},
        "x-ai/grok-4.1-fast": {"input": 0.20, "output": 0.50},
    }
    
    @classmethod
    def get_instance(cls) -> 'CostTracker':
        if cls._instance is None:
            cls._instance = CostTracker()
        return cls._instance
    
    @classmethod
    def reset(cls):
        cls._instance = None
    
    def __init__(self):
        self.current_session: Optional[SessionMetrics] = None
    
    def start_session(self, model: str, protocol_name: str = ""):
        """Start a new tracking session."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            model=model,
            protocol_name=protocol_name
        )
        logger.info(f"💰 Cost tracking started: {session_id}")
    
    def record_usage(self, operation: str, usage: Dict, latency_ms: int = 0, model: str = None):
        """Record usage from an API call."""
        if not self.current_session:
            self.start_session(model or "unknown")
        
        model = model or self.current_session.model
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
        
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        record = APICallRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            operation=operation,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=latency_ms
        )
        
        self.current_session.calls.append(record)
        self.current_session.total_calls += 1
        self.current_session.total_prompt_tokens += prompt_tokens
        self.current_session.total_completion_tokens += completion_tokens
        self.current_session.total_tokens += total_tokens
        self.current_session.total_cost_usd += cost
        self.current_session.total_latency_ms += latency_ms
        
        # Live token counter with call progress
        print(f"🔢 Tokens: {self.current_session.total_tokens:,} ({self.current_session.total_calls} calls) | 💵 ${self.current_session.total_cost_usd:.4f}")
        
        logger.info(
            f"💵 [{operation}]: {total_tokens:,} tokens, ${cost:.4f} "
            f"(session: ${self.current_session.total_cost_usd:.4f})"
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD."""
        pricing = self.MODEL_PRICING.get(model)
        if not pricing:
            for key, value in self.MODEL_PRICING.items():
                if key in model or model in key:
                    pricing = value
                    break
        if not pricing:
            pricing = {"input": 3.0, "output": 15.0}
        
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def get_session_cost(self) -> float:
        if not self.current_session:
            return 0.0
        return self.current_session.total_cost_usd
    
    def get_session_summary(self) -> Dict:
        if not self.current_session:
            return {"error": "No active session"}
        return self.current_session.to_dict()
    
    def format_summary(self) -> str:
        """Format for CLI display using Rich Panel."""
        if not self.current_session:
            return "No active session"
        
        s = self.current_session
        
        # Return Rich-formatted string for Panel content
        content_lines = [
            f"[bold]Model:[/bold] {s.model}",
            f"[bold]Calls:[/bold] {s.total_calls}",
            f"[bold]Tokens:[/bold] {s.total_tokens:,} (in: {s.total_prompt_tokens:,}, out: {s.total_completion_tokens:,})",
            "",
            f"[bold green]💵 TOTAL COST: ${s.total_cost_usd:.4f} USD[/bold green]"
        ]
        return "\n".join(content_lines)
    
    def print_summary(self) -> None:
        """Print session summary using Rich Panel."""
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        content = self.format_summary()
        
        if content == "No active session":
            console.print(content)
        else:
            console.print(Panel(
                content,
                title="💰 Session Cost Summary",
                border_style="green"
            ))


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    return CostTracker.get_instance()
