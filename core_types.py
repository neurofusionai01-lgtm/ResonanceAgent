"""
Core Types and Enums for Resonance Agent System
===============================================
Fundamental data structures and type definitions used throughout the system.
"""

from typing import Dict, List, Any, Optional, Union, Protocol
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from datetime import datetime, timezone
import numpy as np
import uuid
from abc import ABC, abstractmethod
import json


class EmotionalValence(IntEnum):
    """Enhanced emotional valence with more nuanced levels"""
    EXTREMELY_NEGATIVE = -3
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    SLIGHTLY_NEGATIVE = -0.5
    NEUTRAL = 0
    SLIGHTLY_POSITIVE = 0.5
    POSITIVE = 1
    VERY_POSITIVE = 2
    EXTREMELY_POSITIVE = 3
    
    # Score thresholds for valence classification
    EXTREMELY_NEGATIVE_THRESHOLD = -0.8
    VERY_NEGATIVE_THRESHOLD = -0.6
    NEGATIVE_THRESHOLD = -0.3
    SLIGHTLY_NEGATIVE_THRESHOLD = -0.1
    NEUTRAL_THRESHOLD = 0.1
    SLIGHTLY_POSITIVE_THRESHOLD = 0.3
    POSITIVE_THRESHOLD = 0.6
    VERY_POSITIVE_THRESHOLD = 0.8

    @classmethod
    def from_score(cls, score: float) -> 'EmotionalValence':
        """Convert floating point score to emotional valence with improved precision"""
        if score <= cls.EXTREMELY_NEGATIVE_THRESHOLD:
            return cls.EXTREMELY_NEGATIVE
        elif score <= cls.VERY_NEGATIVE_THRESHOLD:
            return cls.VERY_NEGATIVE
        elif score <= cls.NEGATIVE_THRESHOLD:
            return cls.NEGATIVE
        elif score <= cls.SLIGHTLY_NEGATIVE_THRESHOLD:
            return cls.SLIGHTLY_NEGATIVE
        elif score <= cls.NEUTRAL_THRESHOLD:
            return cls.NEUTRAL
        elif score <= cls.SLIGHTLY_POSITIVE_THRESHOLD:
            return cls.SLIGHTLY_POSITIVE
        elif score <= cls.POSITIVE_THRESHOLD:
            return cls.POSITIVE
        elif score <= cls.VERY_POSITIVE_THRESHOLD:
            return cls.VERY_POSITIVE
        else:
            return cls.EXTREMELY_POSITIVE


class IntentCategory(Enum):
    """Enhanced intent categories with more granular classification"""
    INFORMATION_SEEKING = "information_seeking"
    PROBLEM_SOLVING = "problem_solving"
    EMOTIONAL_SUPPORT = "emotional_support"
    CREATIVE_REQUEST = "creative_request"
    LEARNING_ASSISTANCE = "learning_assistance"
    DECISION_MAKING = "decision_making"
    GENERAL_CONVERSATION = "general_conversation"
    TECHNICAL_HELP = "technical_help"
    PERSONAL_REFLECTION = "personal_reflection"
    PLANNING_ASSISTANCE = "planning_assistance"


class MemoryType(Enum):
    """Different types of memories in the system"""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"
    CONTEXTUAL = "contextual"
    CONSOLIDATED = "consolidated"


class UrgencyLevel(IntEnum):
    """Standardized urgency levels"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

    # Score thresholds for urgency classification
    VERY_LOW_THRESHOLD = 0.2
    LOW_THRESHOLD = 0.4
    MEDIUM_THRESHOLD = 0.6
    HIGH_THRESHOLD = 0.8
    
    @classmethod
    def from_score(cls, score: float) -> 'UrgencyLevel':
        if score <= cls.VERY_LOW_THRESHOLD:
            return cls.VERY_LOW
        elif score <= cls.LOW_THRESHOLD:
            return cls.LOW
        elif score <= cls.MEDIUM_THRESHOLD:
            return cls.MEDIUM
        elif score <= cls.HIGH_THRESHOLD:
            return cls.HIGH
        else:
            return cls.CRITICAL


@dataclass
class IntentVector:
    """Enhanced representation of user intent with richer metadata"""
    primary_intent: IntentCategory
    secondary_intents: List[IntentCategory] = field(default_factory=list)
    confidence: float = 0.0
    emotion: EmotionalValence = EmotionalValence.NEUTRAL
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    complexity: float = 0.0
    semantic_embedding: Optional[np.ndarray] = None
    context_tags: List[str] = field(default_factory=list)
    temporal_context: Optional[str] = None
    domain_context: Optional[str] = None
    interaction_style: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.complexity = max(0.0, min(1.0, self.complexity))
        self.secondary_intents = list(dict.fromkeys(self.secondary_intents))
        if self.primary_intent in self.secondary_intents:
            self.secondary_intents.remove(self.primary_intent)
    
    def to_dict(self) -> Dict[str, Any]:
        result = self.__dict__.copy()
        result["primary_intent"] = self.primary_intent.value
        result["secondary_intents"] = [i.value for i in self.secondary_intents]
        result["emotion"] = self.emotion.name
        result["urgency"] = self.urgency.name
        if self.semantic_embedding is not None:
            result["semantic_embedding"] = self.semantic_embedding.tolist()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentVector':
        try:
            embedding = np.array(data["semantic_embedding"]) if "semantic_embedding" in data and data["semantic_embedding"] else None
            return cls(
                primary_intent=IntentCategory(data["primary_intent"]),
                secondary_intents=[IntentCategory(i) for i in data.get("secondary_intents", [])],
                confidence=data.get("confidence", 0.0),
                emotion=EmotionalValence[data.get("emotion", "NEUTRAL")],
                urgency=UrgencyLevel[data.get("urgency", "MEDIUM")],
                complexity=data.get("complexity", 0.0),
                semantic_embedding=embedding,
                context_tags=data.get("context_tags", []),
                temporal_context=data.get("temporal_context"),
                domain_context=data.get("domain_context"),
                interaction_style=data.get("interaction_style"),
                metadata=data.get("metadata", {})
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid IntentVector data: {e}")


@dataclass
class MemoryFragment:
    """Enhanced memory unit with advanced metadata and relationships"""
    id: str
    content: Dict[str, Any]
    memory_type: MemoryType
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    importance: float = 0.0
    confidence: float = 1.0
    embedding: Optional[np.ndarray] = None
    tags: List[str] = field(default_factory=list)
    source: str = "user_interaction"
    related_memories: List[str] = field(default_factory=list)
    emotional_context: Optional[EmotionalValence] = None
    decay_factor: float = 1.0
    consolidation_level: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    IMPORTANCE_BOOST_ON_ACCESS: float = 0.01
    DECAY_RESET_ON_ACCESS: float = 0.1
    EMOTIONAL_ALIGNMENT_WEIGHT: float = 0.3
    TEMPORAL_DECAY_RATE: float = 0.01
    MIN_TEMPORAL_DECAY: float = 0.1
    SEMANTIC_SIMILARITY_BOOST: float = 1.0
    EMOTIONAL_ALIGNMENT_RANGE: float = 6.0
    
    def __post_init__(self):
        self.importance = max(0.0, min(1.0, self.importance))
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.decay_factor = max(0.0, min(1.0, self.decay_factor))
        self.consolidation_level = max(0, self.consolidation_level)
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the fragment to a dictionary suitable for ChromaDB metadata."""
        result = self.__dict__.copy()
        # Convert complex types to JSON-serializable formats
        result["memory_type"] = self.memory_type.value
        result["created_at"] = self.created_at.isoformat()
        result["last_accessed"] = self.last_accessed.isoformat()
        if self.emotional_context:
            result["emotional_context"] = self.emotional_context.name
        
        # ChromaDB-nin qəbul etməsi üçün mürəkkəb tipləri (dict, list) JSON mətninə çeviririk
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                result[key] = json.dumps(value)

        result.pop("embedding", None) # Embedding-i ayrıca idarə edirik

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryFragment':
        """Creates a MemoryFragment from a dictionary (e.g., from ChromaDB)."""
        try:
            # JSON mətninə çevrilmiş sahələri yenidən orijinal tiplərinə (dict, list) qaytarırıq
            parsed_data = data.copy()
            for key, value in parsed_data.items():
                if isinstance(value, str) and value.startswith(    ("{", "[")):
                    try:
                        parsed_data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        # Bu sahə əslində JSON deyilmiş, olduğu kimi saxlayaq
                        pass

            embedding = np.array(parsed_data.get("embedding")) if parsed_data.get("embedding") is not None else None
            emotional_context = EmotionalValence[parsed_data.get("emotional_context")] if parsed_data.get("emotional_context") else None
            
            created_at_dt = datetime.fromisoformat(parsed_data["created_at"])
            last_accessed_dt = datetime.fromisoformat(parsed_data["last_accessed"])
            if created_at_dt.tzinfo is None: created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)
            if last_accessed_dt.tzinfo is None: last_accessed_dt = last_accessed_dt.replace(tzinfo=timezone.utc)

            return cls(
                id=parsed_data["id"],
                content=parsed_data.get("content", {}),
                memory_type=MemoryType(parsed_data["memory_type"]),
                created_at=created_at_dt,
                last_accessed=last_accessed_dt,
                access_count=data.get("access_count", 0),
                importance=data.get("importance", 0.0),
                confidence=data.get("confidence", 1.0),
                embedding=embedding,
                tags=data.get("tags", []),
                source=data.get("source", "user_interaction"),
                related_memories=data.get("related_memories", []),
                emotional_context=emotional_context,
                decay_factor=data.get("decay_factor", 1.0),
                consolidation_level=data.get("consolidation_level", 0),
                metadata=data.get("metadata", {})
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid MemoryFragment data: {e}")
    
    def access(self) -> None:
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1
        self.importance = min(1.0, self.importance + self.IMPORTANCE_BOOST_ON_ACCESS)
        self.decay_factor = min(1.0, self.decay_factor + self.DECAY_RESET_ON_ACCESS)
    
    def calculate_relevance_score(self, query_embedding: Optional[np.ndarray] = None, current_emotion: Optional[EmotionalValence] = None, temporal_weight: float = 1.0) -> float:
        score = self.importance * self.confidence * self.decay_factor
        if query_embedding is not None and self.embedding is not None:
            query_norm = np.linalg.norm(query_embedding)
            embedding_norm = np.linalg.norm(self.embedding)
            if query_norm > 0 and embedding_norm > 0:
                semantic_similarity = np.dot(query_embedding, self.embedding) / (query_norm * embedding_norm)
                score *= (self.SEMANTIC_SIMILARITY_BOOST + semantic_similarity)
        if current_emotion is not None and self.emotional_context is not None:
            emotional_alignment = 1.0 - abs(current_emotion.value - self.emotional_context.value) / self.EMOTIONAL_ALIGNMENT_RANGE
            score *= (1.0 + emotional_alignment * self.EMOTIONAL_ALIGNMENT_WEIGHT)
        age_days = (datetime.now(timezone.utc) - self.created_at).days
        temporal_decay = max(self.MIN_TEMPORAL_DECAY, 1.0 - age_days * self.TEMPORAL_DECAY_RATE)
        score *= (temporal_decay * temporal_weight)
        return score


@dataclass 
class UserProfile:
    """Comprehensive user profile with preferences and behavioral patterns"""
    user_id: str
    name: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_history: Dict[str, Any] = field(default_factory=dict)
    behavioral_patterns: Dict[str, Any] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: Dict[str, Any] = field(default_factory=dict)
    emotional_profile: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    MAX_INTERESTS_TO_STORE: int = 20
    
    def update_from_interaction(self, intent: IntentVector, feedback: Optional[Dict[str, Any]] = None):
        self.last_updated = datetime.now(timezone.utc)
        self.interaction_history["total_interactions"] = self.interaction_history.get("total_interactions", 0) + 1
        intent_key = intent.primary_intent.value
        self.behavioral_patterns.setdefault("intent_frequencies", {})[intent_key] = self.behavioral_patterns.get("intent_frequencies", {}).get(intent_key, 0) + 1
        emotion_key = intent.emotion.name
        self.emotional_profile.setdefault("emotional_patterns", {})[emotion_key] = self.emotional_profile.get("emotional_patterns", {}).get(emotion_key, 0) + 1
        if intent.domain_context and intent.domain_context not in self.interests:
            self.interests.append(intent.domain_context)
            self.interests = self.interests[-self.MAX_INTERESTS_TO_STORE:]

    def to_json(self) -> str:
        """Serializes the UserProfile to a JSON string."""
        data = self.__dict__.copy()
        data["created_at"] = self.created_at.isoformat()
        data["last_updated"] = self.last_updated.isoformat()
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'UserProfile':
        """Deserializes a UserProfile from a JSON string."""
        data = json.loads(json_str)
        # Handle datetime conversion
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])

        # We need to filter out keys that might not be in the __init__ if the schema changed,
        # or handle missing keys. dataclass constructor expects specific args.
        # But since we control the schema, let's assume direct mapping + strictness for now.
        # We should remove 'MAX_INTERESTS_TO_STORE' if it's in the json (it shouldn't be as it's a class var, but check just in case)
        if "MAX_INTERESTS_TO_STORE" in data:
            del data["MAX_INTERESTS_TO_STORE"]

        return cls(**data)


# Protocol definitions for dependency injection
class NLPEngineProtocol(Protocol):
    """Protocol for NLP engines"""
    async def extract_deep_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentVector: ...
    async def generate_embedding(self, text: str) -> np.ndarray: ...


class MemoryManagerProtocol(Protocol):
    """Protocol for memory managers"""
    async def store_memory(self, user_id: str, memory: MemoryFragment) -> str: ...
    async def retrieve_memories(self, user_id: str, query_embedding: Optional[np.ndarray] = None, limit: int = 10) -> List[MemoryFragment]: ...
    async def update_memory(self, user_id: str, memory_id: str, updates: Dict[str, Any]) -> bool: ...


class ResponseGeneratorProtocol(Protocol):
    """Protocol for response generators"""
    async def generate_response(self, user_id: str, query: str, intent: IntentVector, context: Dict[str, Any]) -> Dict[str, Any]: ...


# Exception classes for better error handling
class ResonanceAgentError(Exception):
    """Base exception for Resonance Agent errors"""
    pass

class IntentExtractionError(ResonanceAgentError):
    """Error in intent extraction process"""
    pass

class MemoryOperationError(ResonanceAgentError):
    """Error in memory operations"""
    pass

class ResponseGenerationError(ResonanceAgentError):
    """Error in response generation"""
    pass

class ConfigurationError(ResonanceAgentError):
    """Error in system configuration"""
    pass


@dataclass
class ResonanceConfig:
    """System configuration with intelligent defaults"""
    nlp_model_name: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    max_tokens: int = 4096
    temperature: float = 0.7
    max_memories_per_user: int = 10000
    memory_consolidation_interval_hours: int = 24
    memory_decay_rate: float = 0.01
    semantic_similarity_threshold: float = 0.75
    max_response_length: int = 2000
    mutation_steps: int = 3
    template_selection_strategy: str = "intent_based"
    log_level: str = "INFO"
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_analytics: bool = True
    
    def validate(self) -> None:
        """Validate configuration values"""
        if not (0 <= self.temperature <= 2):
            raise ConfigurationError("Temperature must be between 0 and 2")
        if self.max_memories_per_user < 100:
            raise ConfigurationError("max_memories_per_user must be at least 100")
        if not (1 <= self.mutation_steps <= 10):
            raise ConfigurationError("mutation_steps must be between 1 and 10")