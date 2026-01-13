# Tool Calling Feature Documentation

## Overview

This version of LLM Council supports function calling (tool use) during Stage 1. This allows council members to access external information and capabilities when formulating their responses.

## Available Tools

### 1. **web_search(query: str)**
Search the web for current information using Tavily API or DuckDuckGo as fallback.

**Example use case:** "What happened in AI news today?"

### 2. **calculator(expression: str)**
Perform mathematical calculations with support for basic arithmetic and functions (sqrt, sin, cos, log, etc.)

**Example use case:** "What's 15% of 2847?"

### 3. **wikipedia_search(query: str)**
Search Wikipedia for encyclopedic information.

**Example use case:** "Tell me about quantum computing"

### 4. **get_url_content(url: str)**
Fetch and extract readable text content from a URL.

**Example use case:** "Summarize this article: https://..."

## How It Works

### Architecture

1. **Stage 1 Only**: Tools are only available during Stage 1 (initial responses). Stages 2 and 3 remain text-only.

2. **Independent Tool Use**: Each council member can use tools independently in parallel.

3. **Tool Calling Loop**: When a model requests tools:
   - Tool is executed
   - Result is added to conversation
   - Model is re-queried with the result
   - Process repeats until model provides final answer (max 5 iterations)

4. **Graceful Degradation**: If tools fail or aren't available, models fall back to text-only responses.

### Implementation Details

#### Files Modified/Created

- **`backend/tools.py`** (NEW): Tool schemas and execution functions
- **`backend/config.py`**: Added `ENABLE_TOOLS`, `TAVILY_API_KEY`, and `MAX_TOOL_ITERATIONS`
- **`backend/openrouter.py`**: Added tool calling support to `query_model()` and `query_models_parallel()`
- **`backend/council.py`**: Modified `stage1_collect_responses()` to pass tools to models
- **`pyproject.toml`**: Added new dependencies

#### Tool Execution Flow

```
User Query → Stage 1 (with tools)
             ↓
         Council Models (parallel)
             ↓
      Model A          Model B          Model C
         ↓                ↓                ↓
   Tool Call?       Tool Call?       Tool Call?
         ↓                ↓                ↓
   Execute Tool    Execute Tool    Execute Tool
         ↓                ↓                ↓
   Model Response  Model Response  Model Response
         ↓                ↓                ↓
             Final Responses
                    ↓
            Stage 2 (Rankings)
                    ↓
            Stage 3 (Synthesis)
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional - for web search (falls back to DuckDuckGo if not provided)
TAVILY_API_KEY=your_tavily_key_here
```

### Toggle Tools On/Off

In `backend/config.py`:

```python
ENABLE_TOOLS = True  # Set to False to disable all tools
MAX_TOOL_ITERATIONS = 5  # Maximum tool calling loops per model
```

## Installation

Install new dependencies:

```bash
# If using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Dependencies

New packages added:
- `beautifulsoup4` - HTML parsing for URL content extraction
- `wikipedia` - Wikipedia API access
- `duckduckgo-search` - Web search fallback
- `tavily-python` - Primary web search API (optional)

## Example Usage

### Query Requiring Web Search

**Input:** "What are the latest developments in quantum computing this week?"

**Behavior:**
1. Council models receive query with tool definitions
2. Models may call `web_search("quantum computing latest news")`
3. Search results are returned to models
4. Models formulate responses using the retrieved information
5. Stages 2 & 3 proceed normally with enriched responses

### Query Requiring Calculation

**Input:** "If I invest $10,000 at 7% annual interest for 5 years, how much will I have?"

**Behavior:**
1. Model calls `calculator("10000 * (1.07 ** 5)")`
2. Receives result: `14025.52`
3. Formulates response with the calculation

## Error Handling

- **API Unavailable**: Falls back to alternative services (e.g., DuckDuckGo for web search)
- **Tool Execution Error**: Returns error message to model, which can adjust its approach
- **Max Iterations**: After 5 tool calls, stops and returns partial result
- **Unsupported Models**: Models without tool support automatically fall back to text-only

## Testing

Test queries to verify functionality:

```bash
# Web search test
"What happened in AI news today?"

# Calculator test  
"What's the square root of 1337?"

# Wikipedia test
"Tell me about the Riemann hypothesis"

# URL content test
"Summarize this page: https://example.com/article"
```

## Limitations

1. Maximum 5 tool calls per model per query
2. Web search limited to top 5 results
3. URL content truncated at 4000 characters
4. Calculator restricted to safe math operations only

