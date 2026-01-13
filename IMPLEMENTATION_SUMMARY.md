# Tool Calling Implementation Summary

## ✅ What Was Implemented

I've successfully added function calling (tool use) support to your LLM Council application. Here's what was done:

### 1. **Created `backend/tools.py`** (NEW)
   - Implemented 4 tools with OpenRouter-compatible schemas:
     - `web_search()` - Uses Tavily API (preferred) or DuckDuckGo (fallback)
     - `calculator()` - Safe mathematical calculations using Python's eval
     - `wikipedia_search()` - Wikipedia article summaries
     - `get_url_content()` - Extracts readable text from URLs
   - Each tool has proper error handling and graceful degradation
   - Tool execution dispatcher to route tool calls to appropriate functions

### 2. **Updated `backend/config.py`**
   - Added `ENABLE_TOOLS = True` flag to enable/disable tool calling
   - Added `TAVILY_API_KEY` environment variable support
   - Added `MAX_TOOL_ITERATIONS = 5` to prevent infinite loops

### 3. **Updated `backend/openrouter.py`**
   - Modified `query_model()` to accept `tools` parameter
   - Implemented tool calling loop:
     - Sends tools with initial request
     - Detects `tool_calls` in responses
     - Executes tools and returns results to model
     - Continues until model provides final answer
     - Maximum 5 iterations per model
   - Updated `query_models_parallel()` to pass tools to all models
   - Returns both `content` and `tool_calls` in response dict

### 4. **Updated `backend/council.py`**
   - Modified `stage1_collect_responses()` to support tools
   - Loads tool schemas when `ENABLE_TOOLS = True`
   - Passes tools to all council models in parallel
   - Each model can independently use tools
   - Tool usage history stored in Stage 1 results

### 5. **Updated `pyproject.toml`**
   - Added dependencies:
     - `beautifulsoup4>=4.12.0` - HTML parsing
     - `wikipedia>=1.4.0` - Wikipedia API
     - `duckduckgo-search>=4.0.0` - Web search fallback
     - `tavily-python>=0.3.0` - Primary web search

### 6. **Documentation**
   - Created `TOOLS_DOCUMENTATION.md` - Comprehensive guide
   - Created `IMPLEMENTATION_SUMMARY.md` - This file
   - Created `test_tools.py` - Testing script

## 🚀 How to Use

### Step 1: Install Dependencies

```bash
# If using uv (recommended)
uv sync

# Or using pip
pip install beautifulsoup4 wikipedia duckduckgo-search tavily-python
```

### Step 2: Configure Environment Variables

Create a `.env` file (if you don't have one):

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional - for better web search (falls back to DuckDuckGo if not provided)
TAVILY_API_KEY=your_tavily_key_here
```

### Step 3: Test Tools (Optional)

Test the tools independently before running the full application:

```bash
python test_tools.py
```

### Step 4: Start the Application

```bash
# Backend
cd backend
uvicorn main:app --reload --port 8001

# Frontend (in another terminal)
cd frontend
npm run dev
```

### Step 5: Try Tool-Enabled Queries

Ask questions that benefit from tools:

- **Web Search**: "What are the latest AI developments this week?"
- **Calculator**: "What's 15% of 2847?"
- **Wikipedia**: "Tell me about quantum entanglement"
- **URL Content**: "Summarize this article: https://..."

## 🔍 How It Works

### Request Flow

```
User Query
    ↓
Stage 1: Council Models (with tools enabled)
    ↓
Model A                Model B                Model C
    ↓                      ↓                      ↓
Needs web search?      Needs calculation?     Direct answer?
    ↓                      ↓                      ↓
Call web_search()     Call calculator()      Return text
    ↓                      ↓                      ↓
Receive results       Receive results         —
    ↓                      ↓                      ↓
Formulate answer      Formulate answer       Already done
    ↓                      ↓                      ↓
         Final Stage 1 Responses
                    ↓
         Stage 2: Rankings (text-only)
                    ↓
         Stage 3: Synthesis (text-only)
```

### Tool Calling Loop (per model)

For each model in Stage 1:
1. Send query with tool definitions
2. If model returns `tool_calls`:
   - Execute each tool
   - Add results to conversation
   - Re-query model with results
   - Repeat (max 5 iterations)
3. Model provides final text response
4. Store response + tool usage history

## 📊 Data Structure Changes

### Stage 1 Response Format

**Before:**
```json
{
  "model": "openai/gpt-4o",
  "response": "Here is my answer..."
}
```

**After (with tools):**
```json
{
  "model": "openai/gpt-4o",
  "response": "Based on the search results, here is my answer...",
  "tool_calls": [
    {
      "name": "web_search",
      "arguments": {"query": "AI news 2026"},
      "result": "Web search results:\n1. ..."
    }
  ]
}
```

The `tool_calls` field is optional and only present if tools were used.

## 🔧 Configuration Options

### Enable/Disable Tools

In `backend/config.py`:

```python
ENABLE_TOOLS = True  # Set to False to disable all tools
```

### Change Max Iterations

```python
MAX_TOOL_ITERATIONS = 5  # Adjust as needed (1-10 recommended)
```

### Tool-Specific Configuration

Tools automatically degrade gracefully:
- **Web Search**: Uses Tavily if `TAVILY_API_KEY` set, else DuckDuckGo
- **Wikipedia**: Returns error if package not installed
- **Calculator**: Always works (no external dependencies)
- **URL Content**: Returns error if URL unreachable

## ✨ Key Features

### 1. **Stage 1 Only**
Tools are only available during Stage 1 (initial responses). Stages 2 and 3 remain text-only, which makes sense since they're evaluating/synthesizing Stage 1 outputs.

### 2. **Independent Tool Use**
Each council member can use tools independently and in parallel. One model might search the web while another does calculations.

### 3. **Graceful Degradation**
- If a tool fails, error message is returned to the model
- If API is unavailable, falls back to alternatives (DuckDuckGo for web search)
- If model doesn't support tools, automatically falls back to text-only
- Never breaks existing functionality

### 4. **Automatic Tool Detection**
Models decide when to use tools based on the query. The system doesn't force tool usage.

### 5. **No Breaking Changes**
- Existing conversations work unchanged
- Tools are optional (can be disabled)
- Frontend automatically receives tool usage data
- Storage automatically persists tool calls

## 🧪 Testing Suggestions

### Test Query Examples

1. **Current Events** (Web Search)
   ```
   What happened in AI news today?
   ```

2. **Calculations** (Calculator)
   ```
   If I invest $10,000 at 7% annual interest for 5 years, how much will I have?
   ```

3. **General Knowledge** (Wikipedia)
   ```
   Explain quantum computing and its potential applications.
   ```

4. **URL Analysis** (URL Content)
   ```
   Summarize the key points from: https://example.com/article
   ```

5. **Multi-Tool Query**
   ```
   Compare the GDP growth rates of the US and China over the past year, 
   and calculate the percentage difference.
   ```
   (May use web_search + calculator)

## 📝 Frontend Considerations

The frontend will automatically receive tool usage data in the API response. You can optionally display:

- Tool calls made by each model
- Tool results received
- Visual indicators showing which models used tools
- Expandable sections to show tool execution details

Example Stage 1 response structure:
```javascript
{
  model: "openai/gpt-4o",
  response: "Based on the search results...",
  tool_calls: [
    {
      name: "web_search",
      arguments: { query: "..." },
      result: "..."
    }
  ]
}
```

## 🐛 Troubleshooting

### Issue: "Import X could not be resolved"
**Solution**: Install dependencies with `uv sync` or `pip install -r requirements.txt`

### Issue: Web search returns "Error: ... not installed"
**Solution**: Install either `tavily-python` or `duckduckgo-search`

### Issue: Model doesn't use tools
**Possible causes**:
- Model doesn't support function calling (check OpenRouter docs)
- Query doesn't require tools (model decides this)
- `ENABLE_TOOLS = False` in config

### Issue: Tool execution times out
**Solution**: Increase timeout in `backend/openrouter.py` (default: 120s)

## 🎯 Next Steps

1. **Install dependencies**: Run `uv sync`
2. **Set up API keys**: Add `TAVILY_API_KEY` to `.env` (optional but recommended)
3. **Test tools**: Run `python test_tools.py`
4. **Start application**: Run backend and frontend
5. **Try tool queries**: Ask questions that require external information
6. **Monitor behavior**: Check console logs to see tool execution

## 📚 Additional Resources

- **OpenRouter Function Calling Docs**: https://openrouter.ai/docs#function-calling
- **Tavily API**: https://tavily.com/
- **Tool Schemas**: See `backend/tools.py` for full implementation

## 🔐 Security Notes

- Calculator uses safe eval with restricted namespace (only math functions)
- URL fetcher has timeout and size limits
- No arbitrary code execution possible
- All tools have proper error handling

## 💡 Future Enhancements

Potential improvements:
- Add more tools (database queries, file operations, etc.)
- Per-model tool permissions
- Tool usage analytics/metrics
- Streaming tool execution updates to frontend
- Custom tool definitions via API
- Tool result caching
- Rate limiting for external APIs

---

**Implementation Complete!** 🎉

All deliverables have been completed:
- ✅ New `backend/tools.py` with 4 tool implementations
- ✅ Updated `backend/openrouter.py` with tool calling support
- ✅ Updated `backend/council.py` with tool integration
- ✅ Updated `backend/config.py` with tool configuration
- ✅ Updated `pyproject.toml` with dependencies
- ✅ Documentation explaining how tools work

The system is ready to use. Just install dependencies and start testing!

