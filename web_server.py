import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Agentin özünü və mərkəzləşdirilmiş qurulum funksiyasını import edirik
from agent import ResonanceAgent
from main import setup_agent

# --- Lifespan & Dependency Injection ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI tətbiqinin ömrü boyu agenti idarə edir."""
    global agent_instance
    print("--- Veb Server Başladılır: Agent qurulur... ---")
    try:
        engine_type = os.getenv("ENGINE_TYPE", "google").lower()
        agent_instance = setup_agent(engine_type)
        print("--- Agent uğurla quruldu ---")
    except Exception as e:
        print(f"❌ KRİTİK XƏTA: Veb server agenti qura bilmədi: {e}")
        agent_instance = None
    yield
    print("--- Veb Server Dayanır ---")

def get_agent() -> ResonanceAgent:
    """Agenti əldə etmək üçün FastAPI dependency funksiyası."""
    if agent_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Agent hazır deyil. Serverdə konfiqurasiya xətası ola bilər."
        )
    return agent_instance

# --- FastAPI Tətbiqi ---

load_dotenv()

app = FastAPI(title="Resonance Agent", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Agent-i birbaşa qlobal dəyişən kimi saxlamaq əvəzinə,
# onu FastAPI-nin "dependency injection" sistemi ilə idarə edəcəyik.
# Bu, tətbiqin daha stabil və genişləndirilə bilən olmasına kömək edir.

# --- API Endpoints ---

class ChatRequest(BaseModel):
    text: str
    user_id: str = "web_user_001" # Bu, gələcəkdə autentifikasiyadan gəlməlidir

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Əsas söhbət səhifəsini göstərir."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_with_agent(
    chat_request: ChatRequest,
    agent: ResonanceAgent = Depends(get_agent)
):
    """Agent ilə söhbət üçün əsas endpoint."""
    try:
        # Agentin əsas mesaj emal funksiyasını çağırırıq
        response = await agent.process_message(chat_request.text)
        return JSONResponse(content=response)
    except Exception as e:
        print(f"❌ Söhbət zamanı daxili xəta: {e}")
        raise HTTPException(status_code=500, detail=f"Agentlə söhbət zamanı daxili xəta baş verdi: {e}")

@app.get("/history")
async def get_chat_history(agent: ResonanceAgent = Depends(get_agent)):
    """Agentin söhbət tarixçəsini qaytarır."""
    try:
        history = agent.get_chat_history()
        return JSONResponse(content={"history": history})
    except Exception as e:
        print(f"❌ Tarixçə alınarkən xəta: {e}")
        return JSONResponse(content={"history": []})

@app.get("/status")
async def get_status(agent: ResonanceAgent = Depends(get_agent)):
    """Agentin və serverin vəziyyətini yoxlayır."""
    return {
        "status": "ok",
        "agent_initialized": True, # 'Depends' bunu təmin edir
        "engine_type": os.getenv("ENGINE_TYPE", "google").lower()
    }
