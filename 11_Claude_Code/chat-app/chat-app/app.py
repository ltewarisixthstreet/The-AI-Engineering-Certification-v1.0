from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatMessage(BaseModel):
    message: str
    conversation_id: str


class ChatReply(BaseModel):
    reply: str


def generate_agent_reply(message: str, conversation_id: str) -> str:
    """
    Stub function for agent reply generation.
    This will be replaced with real agent logic later.
    """
    return f"Echo: {message}"


@app.get("/")
async def serve_chat():
    return FileResponse("static/index.html", media_type="text/html")


@app.post("/api/chat")
async def chat(chat_msg: ChatMessage) -> ChatReply:
    reply = generate_agent_reply(chat_msg.message, chat_msg.conversation_id)
    return ChatReply(reply=reply)
