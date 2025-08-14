import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Agentin özünü və mərkəzləşdirilmiş qurulum funksiyasını import edirik
from agent import ResonanceAgent
from main import setup_agent

# --- FastAPI Tətbiqi və Qlobal Dəyişənlər ---

load_dotenv()

app = FastAPI(title="Resonance Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Agent instansiyasını qlobal olaraq saxlayırıq
agent_instance: ResonanceAgent = None

# --- FastAPI Events ---

@app.on_event("startup")
async def startup_event():
    """Proqram başlayarkən agenti mərkəzləşdirilmiş funksiya ilə yaradır."""
    global agent_instance
    
    try:
        engine_type = os.getenv("ENGINE_TYPE", "google").lower()
        # Agent qurulumunu main.py-dəki vahid, etibarlı mənbədən çağırırıq
        agent_instance = setup_agent(engine_type)
    except Exception as e:
        print(f"❌ KRİTİK XƏTA: Veb server agenti qura bilmədi: {e}")
        agent_instance = None

# --- API Endpoints ---

class ChatRequest(BaseModel):
    text: str
    user_id: str = "web_user_001" # Bu, gələcəkdə autentifikasiyadan gəlməlidir

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Əsas söhbət səhifəsini göstərir."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_with_agent(chat_request: ChatRequest):
    """Agent ilə söhbət üçün əsas endpoint."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent hazır deyil. Serverdə konfiqurasiya xətası ola bilər.")
    
    try:
        # Agentin əsas mesaj emal funksiyasını çağırırıq
        response = await agent_instance.process_message(chat_request.text)
        return JSONResponse(content=response)
    except Exception as e:
        print(f"❌ Söhbət zamanı daxili xəta: {e}")
        raise HTTPException(status_code=500, detail=f"Agentlə söhbət zamanı daxili xəta baş verdi: {e}")

@app.get("/status")
async def get_status():
    """Agentin və serverin vəziyyətini yoxlayır."""
    return {
        "status": "ok",
        "agent_initialized": agent_instance is not None,
        "engine_type": os.getenv("ENGINE_TYPE", "google").lower() if agent_instance else None
    }
