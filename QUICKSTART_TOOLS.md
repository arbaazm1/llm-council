# Quick Start Guide - Tool Calling

Get tool calling working in 5 minutes!

## Step 1: Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install beautifulsoup4 wikipedia duckduckgo-search tavily-python
```

## Step 2: Set Environment Variables

Add to your `.env` file (create if it doesn't exist):

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional - for better web search (falls back to DuckDuckGo)
TAVILY_API_KEY=your_tavily_key_here
```

## Step 3: Test Tools (Optional)

```bash
python test_tools.py
```

This will test each tool independently to verify everything works.

## Step 4: Start the Application

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8001

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

## Step 5: Try Tool-Enabled Queries

Open the application and try these queries:

### Web Search
```
What are the latest developments in AI this week?
```

### Calculator
```
What's 15% of 2847?
```

### Wikipedia
```
Tell me about quantum computing
```

### URL Content
```
Summarize this article: https://example.com
```

### Combined
```
Compare Python and JavaScript popularity based on recent data, 
and calculate the percentage difference.
```

## Expected Behavior

- Models will automatically use tools when needed
- Tool calls are executed in Stage 1 only
- Stage 2 and 3 proceed normally with enriched responses
- Tool usage is stored in conversation history

## Troubleshooting

### "Import could not be resolved"
→ Run `uv sync` or install packages manually

### Web search fails
→ Install `duckduckgo-search` or add `TAVILY_API_KEY` to `.env`

### Model doesn't use tools
→ Some models don't support function calling. The system will fall back to text-only.

## Configuration

To disable tools, set in `backend/config.py`:

```python
ENABLE_TOOLS = False
```

## What's Next?

- Read `TOOLS_DOCUMENTATION.md` for detailed information
- Read `IMPLEMENTATION_SUMMARY.md` for technical details
- Customize tools in `backend/tools.py`
- Add more tools as needed

---

**That's it!** You now have a fully functional tool-calling LLM Council. 🎉

