

import google.generativeai as genai
from typing import Dict, Any, List
import httpx
from core_types import ResponseGeneratorProtocol, IntentVector, MemoryFragment

# --- SADƏLƏŞDİRİLMİŞ VƏ ETİBARLI PROMPT ŞABLONU ---
RESPONSE_GENERATION_PROMPT_TEMPLATE = (
    "You are Resonance, a helpful AI assistant.\n"
    "USER QUERY: {query}\n"
    "YOUR ANALYSIS: Primary intent is {primary_intent} with {emotion} emotion.\n"
    "RELEVANT MEMORIES: {memory_context}\n\n"
    "Based on this, provide a helpful and empathetic response."
)

class SmartResponseGenerator(ResponseGeneratorProtocol):
    """LLM və kontekstdən istifadə edərək cavab yaradır."""
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        if not api_key:
            raise ValueError("Google API Key is required for SmartResponseGenerator.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        print("✅ Cavab Generatoru (Gemini) başladıldı.")

    async def generate_response(self, user_id: str, query: str, intent: IntentVector, context: Dict[str, Any]) -> Dict[str, Any]:
        """Daxil olan bütün məlumatlara əsasən ən yaxşı cavabı yaradır."""
        print("✍️ Cavab hazırlanır...")
        
        retrieved_memories: List[MemoryFragment] = context.get('retrieved_memories', [])
        memory_summary = "No relevant memories found."
        if retrieved_memories:
            memory_summary = ", ".join([f"'{mem.content.get('query', '')}'" for mem in retrieved_memories])

        prompt = RESPONSE_GENERATION_PROMPT_TEMPLATE.format(
            query=query,
            primary_intent=intent.primary_intent.value,
            emotion=intent.emotion.name,
            memory_context=memory_summary
        )
        
        try:
            response = await self.model.generate_content_async(prompt)
            final_response = response.text
        except Exception as e:
            print(f"❌ Cavab yaradılmasında xəta: {e}")
            final_response = "I'm sorry, I encountered an error while processing your request. Could you please try again?"

        return {"text": final_response}


class LocalResponseGenerator(ResponseGeneratorProtocol):
    """Lokal AI modelindən istifadə edərək cavab yaradır."""
    def __init__(self, model_name: str, api_base_url: str = "http://localhost:11434/v1"):
        self.model_name = model_name
        self.api_base_url = api_base_url.removesuffix("/")
        self.client = httpx.AsyncClient(base_url=self.api_base_url, timeout=120.0)
        print(f"✅ Lokal Cavab Generatoru ({self.model_name} @ {self.api_base_url}) başladıldı.")

    async def generate_response(self, user_id: str, query: str, intent: IntentVector, context: Dict[str, Any]) -> Dict[str, Any]:
        """Lokal modelə sorğu göndərərək cavab yaradır."""
        print("✍️ Lokal model ilə cavab hazırlanır...")
        
        retrieved_memories: List[MemoryFragment] = context.get('retrieved_memories', [])
        memory_summary = "No relevant memories found."
        if retrieved_memories:
            memory_summary = ", ".join([f"'{mem.content.get('query', '')}'" for mem in retrieved_memories])

        prompt = RESPONSE_GENERATION_PROMPT_TEMPLATE.format(
            query=query,
            primary_intent=intent.primary_intent.value,
            emotion=intent.emotion.name,
            memory_context=memory_summary
        )

        try:
            # We create a system prompt and a user prompt for better results with local models
            messages = [
                {"role": "system", "content": "You are a helpful and empathetic AI assistant named Resonance."},
                {"role": "user", "content": prompt}
            ]
            response = await self.client.post(
                "/chat/completions",
                json={"model": self.model_name, "messages": messages, "temperature": 0.7}
            )
            response.raise_for_status()
            response_json = response.json()
            final_response = response_json['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ Lokal cavab yaradılmasında xəta: {e}")
            final_response = "I'm sorry, I encountered an error with the local model. Please check if it's running correctly."

        return {"text": final_response}
