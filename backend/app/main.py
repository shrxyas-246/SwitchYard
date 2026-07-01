#is the entry point that ties everything together. It creates the FastAPI() application object, 
# registers your routes, sets up CORS, and runs any startup logic. When you launch the server with 
# uvicorn app.main:app, the app.main:app part means "the app object inside app/main.py" — this file is what gets run.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api.routes import dashboard
origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
app = FastAPI(title="Switchyard API")

app.add_middleware(CORSMiddleware, 
                   allow_origins=origins, 
                   allow_methods=["*"], 
                   allow_headers=["*"])

app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"message": "Switchyard API is running"}