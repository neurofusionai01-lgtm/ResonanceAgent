import asyncio
import os
import argparse
import uvicorn
from dotenv import load_dotenv

# Komponentləri import edirik
from nlp_engine import RealNLPEngine, LocalNLPEngine
from memory_manager import VectorDBMemoryManager
from response_generator import SmartResponseGenerator, LocalResponseGenerator
from agent import ResonanceAgent

# --- Mərkəzləşdirilmiş Agent Qurulum Funksiyası ---
def setup_agent(engine_type: str) -> ResonanceAgent:
    """Konfiqurasiyaya əsasən agenti qurur və qaytarır."""
    print(f"--- Resonance Agent Sistemi Qurulur (Mühərrik: {engine_type.upper()}) ---")

    if engine_type == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("ENGINE_TYPE='google' seçilib, amma GOOGLE_API_KEY tapılmadı.")
        nlp_engine = RealNLPEngine(api_key=api_key)
        response_generator = SmartResponseGenerator(api_key=api_key)
    
    elif engine_type == "local":
        chat_model_name = os.getenv("LOCAL_CHAT_MODEL_NAME")
        embedding_model_name = os.getenv("LOCAL_EMBEDDING_MODEL_NAME")
        embedding_size_str = os.getenv("LOCAL_EMBEDDING_SIZE")

        if not all([chat_model_name, embedding_model_name, embedding_size_str]):
            raise ValueError("Lokal mühərrik üçün tələb olunan parametrlər (.env) tapılmadı.")
        
        try:
            embedding_size = int(embedding_size_str)
        except (ValueError, TypeError):
            raise ValueError(f"LOCAL_EMBEDDING_SIZE rəqəm olmalıdır, amma '{embedding_size_str}' tapıldı.")

        api_base_url = os.getenv("LOCAL_API_BASE_URL", "http://localhost:11434/v1")
        
        nlp_engine = LocalNLPEngine(
            chat_model_name=chat_model_name, 
            embedding_model_name=embedding_model_name, 
            embedding_size=embedding_size, 
            api_base_url=api_base_url
        )
        response_generator = LocalResponseGenerator(
            model_name=chat_model_name, 
            api_base_url=api_base_url
        )
    else:
        raise ValueError(f"Naməlum ENGINE_TYPE: '{engine_type}'")

    memory_manager = VectorDBMemoryManager(path="./resonance_user_memory")
    # Hər rejim üçün fərqli user_id istifadə etmək daha məntiqlidir
    user_id = "web_user_001" if os.getenv("CURRENT_MODE") == "web" else "cli_user_001"
    
    agent = ResonanceAgent(
        nlp_engine=nlp_engine, 
        memory_manager=memory_manager, 
        response_generator=response_generator, 
        user_id=user_id
    )
    print("✅ Agent uğurla quruldu.")
    return agent

# --- CLI Modu üçün Köməkçi Funksiya ---
async def run_cli_mode(agent: ResonanceAgent):
    """Agent üçün interaktiv komanda sətri interfeysini işə salır."""
    print("\n--- Dialoqa Başlamağa Hazır ---")
    print("Çıxmaq üçün 'exit' və ya 'quit' yazın.")

    while True:
        try:
            user_input = await asyncio.to_thread(input, f"\n[{agent.user_id}] Siz: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            response = await agent.process_message(user_input)
            print(f"🤖 Agent: {response.get('text')}")
        except (KeyboardInterrupt, EOFError):
            break
    print("\n👋 Agentlə dialoq bitdi. Sağ olun!")


# ---Əsas Giriş Nöqtəsi ---
if __name__ == "__main__":
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Resonance Agent Sistemi")
    parser.add_argument("--mode", choices=["web", "cli"], default="web", 
                        help="Agenti hansı rejimdə işə salmaq istədiyinizi seçin (web/cli)")
    args = parser.parse_args()

    # Hansı rejimdə işlədiyimizi qeyd edirik ki, setup_agent bilsin
    os.environ["CURRENT_MODE"] = args.mode

    try:
        if args.mode == "web":
            print("--- Veb Server Rejimi Başladılır ---")
            uvicorn.run(
                "web_server:app", 
                host=os.getenv("HOST", "127.0.0.1"), 
                port=int(os.getenv("PORT", 8000)),
                reload=True
            )
        
        elif args.mode == "cli":
            engine_type = os.getenv("ENGINE_TYPE", "google").lower()
            agent = setup_agent(engine_type)
            asyncio.run(run_cli_mode(agent))

    except (ValueError, TypeError) as e:
        print(f"❌ KRİTİK XƏTA: Konfiqurasiya və ya tip xətası: {e}")
    except Exception as e:
        print(f"❌ Gözlənilməyən xəta baş verdi: {e}")