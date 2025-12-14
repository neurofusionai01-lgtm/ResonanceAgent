

import google.generativeai as genai
from typing import Dict, Any, List
import httpx
from datetime import datetime
import re
from core_types import ResponseGeneratorProtocol, IntentVector, MemoryFragment

# --- INTELLIGENT & CONTEXT-AWARE PROMPT TEMPLATE ---
RESPONSE_GENERATION_PROMPT_TEMPLATE = (
    "You are Resonance, a highly intelligent and empathetic AI assistant.\n"
    "Current Date/Time: {current_time}\n"
    "User Profile: {user_profile_summary}\n\n"

    "CONTEXT ANALYSIS:\n"
    "- User Query: {query}\n"
    "- Detected Intent: {primary_intent} (Confidence: {confidence})\n"
    "- Emotional State: {emotion}\n"
    "- Relevant Memories: {memory_context}\n\n"

    "INSTRUCTIONS:\n"
    "1. FIRST, think step-by-step about the user's request, their hidden emotional needs, and how to best help them. Output this thinking process inside <thought>...</thought> tags.\n"
    "2. SECOND, provide your final response to the user in their language (likely Azerbaijani or English). Be natural, helpful, and concise.\n"
    "3. If the user asks about time or date, use the 'Current Date/Time' provided above.\n"
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
            # Better formatting for memories
            memory_summary = "\n".join([f"- {mem.content.get('query', '')} -> {mem.content.get('response', '')}" for mem in retrieved_memories])

        user_profile = context.get("user_profile")
        profile_summary = "Unknown User"
        if user_profile:
             interests = ", ".join(user_profile.interests) if user_profile.interests else "None yet"
             profile_summary = f"ID: {user_profile.user_id}, Interests: {interests}, Interactions: {user_profile.interaction_history.get('total_interactions', 0)}"

        prompt = RESPONSE_GENERATION_PROMPT_TEMPLATE.format(
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_profile_summary=profile_summary,
            query=query,
            primary_intent=intent.primary_intent.value,
            confidence=intent.confidence,
            emotion=intent.emotion.name,
            memory_context=memory_summary
        )
        
        try:
            response = await self.model.generate_content_async(prompt)
            raw_text = response.text

            # Extract thought process
            thought_process = None
            thought_match = re.search(r'<thought>(.*?)</thought>', raw_text, re.DOTALL)
            if thought_match:
                thought_process = thought_match.group(1).strip()
                print(f"🤔 Agent Düşünür: {thought_process}")
                # Remove thought from final response to user
                final_response = re.sub(r'<thought>.*?</thought>', '', raw_text, flags=re.DOTALL).strip()
            else:
                final_response = raw_text

        except Exception as e:
            print(f"❌ Cavab yaradılmasında xəta: {e}")
            final_response = "Bağışlayın, sorğunuzu emal edərkən xəta baş verdi."
            thought_process = None

        return {"text": final_response, "thought": thought_process}

    async def generate_raw(self, prompt: str) -> str:
        """Executes a raw generation without the standard template (used for ReAct)."""
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Raw Generate Error: {e}")
            return f"Error: {e}"


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
            memory_summary = "\n".join([f"- {mem.content.get('query', '')} -> {mem.content.get('response', '')}" for mem in retrieved_memories])

        user_profile = context.get("user_profile")
        profile_summary = "Unknown User"
        if user_profile:
             interests = ", ".join(user_profile.interests) if user_profile.interests else "None yet"
             profile_summary = f"ID: {user_profile.user_id}, Interests: {interests}, Interactions: {user_profile.interaction_history.get('total_interactions', 0)}"

        prompt = RESPONSE_GENERATION_PROMPT_TEMPLATE.format(
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_profile_summary=profile_summary,
            query=query,
            primary_intent=intent.primary_intent.value,
            confidence=intent.confidence,
            emotion=intent.emotion.name,
            memory_context=memory_summary
        )

        try:
            # We create a system prompt and a user prompt for better results with local models
            messages = [
                {"role": "system", "content": "You are a helpful and empathetic AI assistant named Resonance. Always think inside <thought> tags before answering."},
                {"role": "user", "content": prompt}
            ]
            response = await self.client.post(
                "/chat/completions",
                json={"model": self.model_name, "messages": messages, "temperature": 0.7}
            )
            response.raise_for_status()
            response_json = response.json()
            raw_text = response_json['choices'][0]['message']['content']

            # Extract thought process
            thought_process = None
            thought_match = re.search(r'<thought>(.*?)</thought>', raw_text, re.DOTALL)
            if thought_match:
                thought_process = thought_match.group(1).strip()
                print(f"🤔 Agent Düşünür (Local): {thought_process}")
                # Remove thought from final response to user
                final_response = re.sub(r'<thought>.*?</thought>', '', raw_text, flags=re.DOTALL).strip()
            else:
                final_response = raw_text

        except Exception as e:
            print(f"❌ Lokal cavab yaradılmasında xəta: {e}")
            final_response = "I'm sorry, I encountered an error with the local model. Please check if it's running correctly."
            thought_process = None

        return {"text": final_response, "thought": thought_process}

    async def generate_raw(self, prompt: str) -> str:
        """Executes a raw generation without the standard template (used for ReAct)."""
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0 # Strict for tools
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ Raw Generate Error: {e}")
            return f"Error: {e}"
