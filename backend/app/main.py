from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json

from . import models, email_assistant
from .database import SessionLocal, engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/chat")
async def chat(message: dict, db: Session = Depends(get_db)):
    try:
        # Get response from email assistant
        response = email_assistant.get_assistant_response(message["message"])
        
        # Save message and response to database
        user_message = models.ChatMessage(role="user", content=message["message"])
        assistant_message = models.ChatMessage(role="assistant", content=response)
        
        db.add(user_message)
        db.add(assistant_message)
        db.commit()
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat-history")
async def get_chat_history(db: Session = Depends(get_db)):
    messages = db.query(models.ChatMessage).order_by(models.ChatMessage.timestamp).all()
    return messages 