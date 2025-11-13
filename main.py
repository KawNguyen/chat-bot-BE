from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import brand, type, headphone, ai
from database import Base, engine

app = FastAPI()

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
app.include_router(ai.router)