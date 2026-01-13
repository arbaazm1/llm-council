"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio

from . import storage
from .council import run_full_council, generate_conversation_title, generate_template_title, stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final, calculate_aggregate_rankings
import re

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


class CreateTemplateRequest(BaseModel):
    """Request to create a new prompt template."""
    name: str
    body: str


class UpdateTemplateRequest(BaseModel):
    """Request to update a prompt template."""
    name: str
    body: str


class PromptTemplate(BaseModel):
    """Prompt template model."""
    id: str
    created_at: str
    updated_at: str
    name: str
    body: str
    fields: List[str]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a specific conversation."""
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "message": "Conversation deleted"}


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Get conversation history (before adding the new message)
    conversation_history = conversation["messages"]

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process with conversation history
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content,
        conversation_history
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Get conversation history (before adding the new message)
    conversation_history = conversation["messages"]

    async def event_generator():
        try:
            # Mark conversation as processing
            storage.set_conversation_processing(conversation_id, True)
            
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses with conversation history
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(request.content, conversation_history)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Mark conversation as not processing
            storage.set_conversation_processing(conversation_id, False)

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Mark conversation as not processing on error
            storage.set_conversation_processing(conversation_id, False)
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


def extract_template_fields(body: str) -> List[str]:
    """Extract field names from template body (fields are in {{field_name}} format)."""
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, body)
    # Return unique fields in order of appearance
    seen = set()
    unique_fields = []
    for field in matches:
        if field not in seen:
            seen.add(field)
            unique_fields.append(field)
    return unique_fields


@app.get("/api/templates", response_model=List[PromptTemplate])
async def list_templates():
    """List all prompt templates."""
    return storage.list_templates()


@app.post("/api/templates", response_model=PromptTemplate)
async def create_template(request: CreateTemplateRequest):
    """Create a new prompt template."""
    template_id = str(uuid.uuid4())
    
    # Extract fields from the body
    fields = extract_template_fields(request.body)
    
    # Generate a name if empty
    name = request.name.strip()
    if not name:
        # Use AI to generate a descriptive title
        name = await generate_template_title(request.body)
    
    template = storage.create_template(template_id, name, request.body, fields)
    return template


@app.get("/api/templates/{template_id}", response_model=PromptTemplate)
async def get_template(template_id: str):
    """Get a specific template."""
    template = storage.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.put("/api/templates/{template_id}", response_model=PromptTemplate)
async def update_template(template_id: str, request: UpdateTemplateRequest):
    """Update an existing template."""
    # Extract fields from the body
    fields = extract_template_fields(request.body)
    
    # Generate a name if empty
    name = request.name.strip()
    if not name:
        # Generate name from first line or first 50 chars of body
        first_line = request.body.split('\n')[0].strip()
        name = first_line[:50] if first_line else "Untitled Template"
    
    template = storage.update_template(template_id, name, request.body, fields)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a template."""
    success = storage.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "message": "Template deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
