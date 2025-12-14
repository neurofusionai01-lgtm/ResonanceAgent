import os
import numpy as np
import google.generativeai as genai
from typing import Dict, Any, Optional
import httpx
import json

from core_types import NLPEngineProtocol, IntentVector, IntentCategory, EmotionalValence, UrgencyLevel

# --- Prompt Sablonu ---
INTENT_EXTRACTION_PROMPT = """
Analyze the user's text and provide a detailed intent analysis in JSON format.
The user text is: "{text}"

If the user asks to perform a calculation, write a note, or look up information, classify the intent as 'PROBLEM_SOLVING' or 'information_seeking'.

The JSON output should strictly follow this structure:
{{
  "primary_intent": "one of {intent_categories}",
  "secondary_intents": ["one or more of {intent_categories}"],
  "emotion": "one of {emotion_valences}",
  "urgency": "one of {urgency_levels}",
  "confidence": 0.0 to 1.0,
  "complexity": 0.0 to 1.0,
  "domain_context": "A short, relevant subject domain (e.g., 'math', 'personal_notes')",
  "temporal_context": "past, present, or future",
  "interaction_style": "formal, casual, or technical"
}}

Do not include any other text or explanations in your response, only the JSON object.
"""

# --- Google Mühərriki ---
class RealNLPEngine(NLPEngineProtocol):
    """Google Gemini API istifadə edərək niyyəti və embedding-i çıxaran real mühərrik."""
    def __init__(self, api_key: str, intent_model_name: str = "gemini-1.5-flash", embedding_model_name: str = "text-embedding-004"):
        if not api_key:
            raise ValueError("Google API Key is required for RealNLPEngine.")
        genai.configure(api_key=api_key)
        self.intent_model = genai.GenerativeModel(intent_model_name)
        self.embedding_model_name = embedding_model_name
        print("✅ NLP Engine (Gemini) başladıldı.")

    async def extract_deep_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentVector:
        print(f"🧠 Mətn üçün niyyət analizi edilir: '{text}'")
        
        prompt = INTENT_EXTRACTION_PROMPT.format(
            text=text,
            intent_categories=[i.value for i in IntentCategory],
            emotion_valences=[e.name for e in EmotionalValence],
            urgency_levels=[u.name for u in UrgencyLevel]
        )

        try:
            response = await self.intent_model.generate_content_async(prompt)
            # Cavabın formatını yoxlamaq və təmizləmək üçün əlavə məntiq
            cleaned_text = response.text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:-3].strip()
            
            intent_data = json.loads(cleaned_text)
            return IntentVector.from_dict(intent_data)
        except Exception as e:
            print(f"❌ Gemini niyyət analizi xətası: {e}")
            # Xəta zamanı default IntentVector qaytarırıq
            return IntentVector(primary_intent=IntentCategory.GENERAL_CONVERSATION)

    async def generate_embedding(self, text: str) -> np.ndarray:
        print(f"🔢 Mətn üçün embedding yaradılır: '{text}'")
        try:
            result = await genai.embed_content_async(
                model=self.embedding_model_name,
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return np.array(result['embedding'])
        except Exception as e:
            print(f"❌ Embedding yaradılmasında xəta: {e}")
            return np.zeros(768) # text-embedding-004 üçün ölçü

# --- Lokal Mühərrik ---
class LocalNLPEngine(NLPEngineProtocol):
    """Lokalda işləyən bir AI modelinə (məsələn, Ollama) qoşulan mühərrik."""
    def __init__(self, chat_model_name: str, embedding_model_name: str, embedding_size: int, api_base_url: str = "http://localhost:11434/v1"):
        self.chat_model_name = chat_model_name
        self.embedding_model_name = embedding_model_name
        self.embedding_size = embedding_size
        self.api_base_url = api_base_url.removesuffix("/")
        self.client = httpx.AsyncClient(base_url=self.api_base_url, timeout=120.0)
        print(f"✅ Lokal NLP Engine (Söhbət: {self.chat_model_name}, Embedding: {self.embedding_model_name}) başladıldı.")

    async def extract_deep_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentVector:
        print(f"🧠 Lokal model ilə niyyət analizi edilir: '{text}'")
        try:
            prompt = INTENT_EXTRACTION_PROMPT.format(
                text=text,
                intent_categories=[i.value for i in IntentCategory],
                emotion_valences=[e.name for e in EmotionalValence],
                urgency_levels=[u.name for u in UrgencyLevel]
            )
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.chat_model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0
                }
            )
            response.raise_for_status()
            intent_data = json.loads(response.json()["choices"][0]["message"]["content"])
            return IntentVector.from_dict(intent_data)
        except Exception as e:
            print(f"❌ Lokal niyyət analizi xətası: {e}")
            # Xəta zamanı default IntentVector qaytarırıq
            return IntentVector(primary_intent=IntentCategory.GENERAL_CONVERSATION)

    async def generate_embedding(self, text: str) -> np.ndarray:
        print(f"🔢 Lokal model ilə embedding yaradılır: '{text}'")
        try:
            response = await self.client.post(
                "/embeddings",
                # OpenAI-uyğun endpoint 'input' gözləyir, 'prompt' deyil.
                json={"model": self.embedding_model_name, "input": text}
            )
            response.raise_for_status()
            # OpenAI-uyğun cavab formatı: {"data": [{"embedding": [...]}]}
            return np.array(response.json()["data"][0]["embedding"])
        except Exception as e:
            print(f"❌ Lokal embedding yaradılmasında xəta: {e}")
            return np.zeros(self.embedding_size)