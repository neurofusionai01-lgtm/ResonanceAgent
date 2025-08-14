

from typing import Dict, Any
from datetime import datetime, timezone
import uuid

from core_types import (
    MemoryFragment, MemoryType, UserProfile, IntentVector, 
    NLPEngineProtocol, MemoryManagerProtocol, ResponseGeneratorProtocol
)

class ResonanceAgent:
    """Bütün komponentləri birləşdirən və agentin məntiqini idarə edən əsas sinif.""" 
    def __init__(
        self,
        nlp_engine: NLPEngineProtocol,
        memory_manager: MemoryManagerProtocol,
        response_generator: ResponseGeneratorProtocol,
        user_id: str
    ):
        self.nlp_engine = nlp_engine
        self.memory_manager = memory_manager
        self.response_generator = response_generator
        self.user_id = user_id
        # Real tətbiqdə istifadəçi profili də databazadan yüklənməlidir.
        # Sadəlik üçün hələlik hər dəfə yeni profil yaradırıq.
        self.user_profile = UserProfile(user_id=user_id)
        print(f"🤖 Resonance Agent '{self.user_id}' üçün hazır vəziyyətdədir.")

    async def process_message(self, text: str) -> Dict[str, Any]:
        """İstifadəçi mesajını tamamilə emal edir və cavab qaytarır."""
        print("\n" + "-"*50)
        print(f"📩 Yeni mesaj alındı: '{text}'")

        # 1. Niyyəti analiz et
        intent_vector = await self.nlp_engine.extract_deep_intent(text)

        # 2. Mətn üçün embedding yarat
        query_embedding = await self.nlp_engine.generate_embedding(text)

        # 3. Əlaqəli yaddaşları tap
        retrieved_memories = await self.memory_manager.retrieve_memories(
            user_id=self.user_id,
            query_embedding=query_embedding
        )

        # 4. Cavab yaratmaq üçün kontekst hazırla
        context = {
            "user_profile": self.user_profile,
            "retrieved_memories": retrieved_memories
        }

        # 5. Cavabı yarat
        response = await self.response_generator.generate_response(
            user_id=self.user_id,
            query=text,
            intent=intent_vector,
            context=context
        )

        # 6. Bu interaksiyanı yaddaşda saxla
        new_memory = MemoryFragment(
            id=str(uuid.uuid4()),
            content={"query": text, "response": response.get("text")},
            memory_type=MemoryType.EPISODIC,
            created_at=datetime.now(timezone.utc),
            last_accessed=datetime.now(timezone.utc),
            embedding=query_embedding,
            emotional_context=intent_vector.emotion,
            tags=[intent_vector.primary_intent.value, intent_vector.domain_context]
        )
        await self.memory_manager.store_memory(self.user_id, new_memory)

        # 7. İstifadəçi profilini yenilə
        self.user_profile.update_from_interaction(intent_vector)
        print(f"👤 İstifadəçi profili yeniləndi. Ümumi interaksiya: {self.user_profile.interaction_history.get('total_interactions')}")
        print("-"*50 + "\n")

        return response

