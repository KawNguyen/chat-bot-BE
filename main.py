from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import brand, type, headphone
from database import Base, engine
from services.ai_client import AIClient
import os
from routers import chatbot
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ai_url = os.getenv("AI_API_URL")
    ai_model = os.getenv("AI_MODEL")
    ai_key = os.getenv("AI_API_KEY")
    
    try:
        if ai_url:
            app.state.ai_client = AIClient(api_url=ai_url, model=ai_model, api_key=ai_key)
            print(f"AI Client initialized with URL: {ai_url}")
            print(f"AI Model: {ai_model or 'mistralai/mistral-7b-instruct-v0.3'}")
        else:
            app.state.ai_client = None
            print("Warning: AI_API_URL not set. Chat endpoints will not work.")
    except Exception as e:
        print(f"Failed to initialize AI client: {e}")
        app.state.ai_client = None
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

app.include_router(brand.router)
app.include_router(headphone.router)
app.include_router(type.router)
app.include_router(chatbot.router)