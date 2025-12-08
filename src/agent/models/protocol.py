from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Literal, Any

class Position(BaseModel):
    x: float
    y: float

class QuestionOption(BaseModel):
    id: str
    label: str
    value: Optional[str] = None
    
class Question(BaseModel):
    id: str
    uid: str = Field(..., pattern=r'^[a-z_][a-z0-9_]*$')
    type: Literal["select", "multiselect", "text", "number", "date"]
    question: str = Field(..., min_length=5)
    options: Optional[List[QuestionOption]] = None
    expressao: Optional[str] = None  # Conditional visibility
    
    @field_validator('options')
    @classmethod
    def validate_options_for_select(cls, v, info):
        q_type = info.data.get('type') if hasattr(info, 'data') else None
        if q_type in ['select', 'multiselect'] and not v:
            raise ValueError(f"Question type '{q_type}' requires options")
        return v

class NodeData(BaseModel):
    descricao: str = Field(..., min_length=10)
    questions: List[Question]
    condicao: Optional[str] = None  # Node-level conditional
    
    @field_validator('questions')
    @classmethod
    def validate_unique_uids(cls, v):
        uids = [q.uid for q in v]
        if len(uids) != len(set(uids)):
            raise ValueError(f"Duplicate UIDs in questions: {uids}")
        return v

class ProtocolNode(BaseModel):
    id: str = Field(..., pattern=r'^node-\d+$')
    type: Literal["question", "decision", "action", "end"]
    position: Position
    data: NodeData

class Edge(BaseModel):
    id: str
    source: str = Field(..., pattern=r'^node-\d+$')
    target: str = Field(..., pattern=r'^node-\d+$')
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class ProtocolMetadata(BaseModel):
    company: str
    name: str
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class Protocol(BaseModel):
    metadata: ProtocolMetadata
    nodes: List[ProtocolNode] = Field(..., min_length=1)
    edges: List[Edge] = []
    
    @model_validator(mode='after')
    def validate_edges_reference_existing_nodes(self):
        node_ids = {n.id for n in self.nodes}
        
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge references non-existent source node: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge references non-existent target node: {edge.target}")
        
        return self
    
    @field_validator('nodes')
    @classmethod
    def validate_unique_node_ids(cls, v):
        ids = [n.id for n in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate node IDs")
        return v
