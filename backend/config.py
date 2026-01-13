"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.2",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "openai/gpt-5.2"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Data directory for prompt templates
TEMPLATES_DIR = "data/templates"

# Tool calling configuration
ENABLE_TOOLS = True  # Enable/disable tool calling support
TAVILY_API_KEY = "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"
MAX_TOOL_ITERATIONS = 5  # Maximum number of tool calling iterations per model
