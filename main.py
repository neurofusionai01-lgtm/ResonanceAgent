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
        # Default values for local engine to prevent crashes if .env is missing/partial
        chat_model_name = os.getenv("LOCAL_CHAT_MODEL_NAME", "llama3:latest")
        embedding_model_name = os.getenv("LOCAL_EMBEDDING_MODEL_NAME", "nomic-embed-text:latest")
        embedding_size_str = os.getenv("LOCAL_EMBEDDING_SIZE", "768")

        print(f"ℹ️  Local Config: Chat='{chat_model_name}', Embed='{embedding_model_name}', Size={embedding_size_str}")

        try:
            embedding_size = int(embedding_size_str)
        except (ValueError, TypeError):
             print(f"⚠️ LOCAL_EMBEDDING_SIZE '{embedding_size_str}' is invalid. Defaulting to 768.")
             embedding_size = 768

        api_base_url = os.getenv("LOCAL_API_BASE_URL", "http://localhost:11434/v1")

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
    """Agent üçün interaktiv komanda sətri interfeysini işə salır (Rich UI ilə)."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich.text import Text
    except ImportError:
        print("⚠️  'rich' kitabxanası tapılmadı. Zəhmət olmasa 'pip install rich' əmrini icra edin.")
        return

    console = Console()
    console.print(Panel.fit("[bold cyan]Resonance AI Agent[/bold cyan]\n[dim]ReAct Enabled • Memory Active[/dim]", border_style="blue"))
    console.print("[dim]Çıxmaq üçün 'exit' və ya 'quit' yazın.[/dim]\n")

    while True:
        try:
            user_input = await asyncio.to_thread(console.input, f"[bold green]👤 {agent.user_id}:[/bold green] ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            with console.status("[bold yellow]Düşünürəm...[/bold yellow]", spinner="dots"):
                response = await agent.process_message(user_input)

            # Show Thoughts/Trace
            thought = response.get('thought')
            if thought:
                console.print(Panel(Markdown(thought), title="[bold yellow]🧠 Thought Process[/bold yellow]", border_style="yellow", expand=False))

            # Show Trace (if available from ReAct engine)
            trace = response.get('trace')
            if trace:
                for step in trace:
                    if step.get('action'):
                        console.print(f"[dim]⚙️  Action: {step['action']} ({step['input']})[/dim]")
                    if step.get('observation'):
                        console.print(f"[dim]   Result: {step['observation']}[/dim]")

            # Show Final Answer
            console.print(Panel(Markdown(response.get('text')), title="[bold green]🤖 Resonance[/bold green]", border_style="green"))
            print() # Spacer

        except (KeyboardInterrupt, EOFError):
            break
    console.print("\n[bold red]👋 Agentlə dialoq bitdi. Sağ olun![/bold red]")


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
            # Relaod rejimini ətraf mühit dəyişənindən oxuyuruq
            reload_mode = os.getenv("RELOAD_MODE", "False").lower() in ("true", "1", "t")
            uvicorn.run(
                "web_server:app", 
                host=os.getenv("HOST", "127.0.0.1"), 
                port=int(os.getenv("PORT", 8000)),
                reload=reload_mode
            )
        
        elif args.mode == "cli":
            engine_type = os.getenv("ENGINE_TYPE", "google").lower()
            agent = setup_agent(engine_type)
            asyncio.run(run_cli_mode(agent))

    except (ValueError, TypeError) as e:
        print(f"❌ KRİTİK XƏTA: Konfiqurasiya və ya tip xətası: {e}")
    except Exception as e:
        print(f"❌ Gözlənilməyən xəta baş verdi: {e}")