"""
Tool definitions and execution functions for LLM Council.

This module provides 4 tools that models can call during Stage 1:
1. web_search - Search the web using Tavily or DuckDuckGo
2. calculator - Perform mathematical calculations
3. wikipedia_search - Search Wikipedia
4. get_url_content - Fetch and extract content from URLs

Each tool has a schema (for the API) and an execution function.
"""

import os
import json
import httpx
import math
from typing import Any, Dict, List
from bs4 import BeautifulSoup


# ============================================================================
# TOOL SCHEMAS (OpenRouter/OpenAI format)
# ============================================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, or real-time data. Use this when you need up-to-date information that may not be in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform mathematical calculations. Supports basic arithmetic, exponents, square root (sqrt), trigonometric functions (sin, cos, tan), logarithms (log, log10), and constants (pi, e).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Search Wikipedia for encyclopedic information about topics, people, places, concepts, etc. Returns a summary of the Wikipedia article.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search for on Wikipedia"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_url_content",
            "description": "Fetch and extract readable text content from a URL. Use this to read articles, blog posts, or web pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch content from (must start with http:// or https://)"
                    }
                },
                "required": ["url"]
            }
        }
    }
]


# ============================================================================
# TOOL EXECUTION FUNCTIONS
# ============================================================================

async def execute_web_search(query: str) -> str:
    """
    Execute a web search using Tavily API (preferred) or DuckDuckGo (fallback).
    
    Args:
        query: Search query string
        
    Returns:
        Formatted search results as a string
    """
    # Try to get API key from config first, then environment
    try:
        from .config import TAVILY_API_KEY
        tavily_api_key = TAVILY_API_KEY
    except ImportError:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    # Try Tavily first if API key is available
    if tavily_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": 5
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Format results
                results = []
                for idx, result in enumerate(data.get("results", []), 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "")
                    content = result.get("content", "")
                    results.append(f"{idx}. {title}\n   URL: {url}\n   {content}")
                
                if results:
                    return "Web search results:\n\n" + "\n\n".join(results)
                else:
                    return "No results found."
                    
        except Exception as e:
            print(f"Tavily search failed: {e}, falling back to DuckDuckGo")
    
    # Fallback to DuckDuckGo
    try:
        # Try new package name first
        try:
            from ddgs import DDGS
        except ImportError:
            # Fall back to old package name
            from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = []
            for idx, result in enumerate(ddgs.text(query, max_results=5), 1):
                title = result.get("title", "No title")
                url = result.get("href", "")
                body = result.get("body", "")
                results.append(f"{idx}. {title}\n   URL: {url}\n   {body}")
            
            if results:
                return "Web search results:\n\n" + "\n\n".join(results)
            else:
                return "No results found."
                
    except ImportError:
        return "Error: Neither Tavily nor DuckDuckGo search libraries are available. Please install 'tavily-python' or 'duckduckgo-search'."
    except Exception as e:
        return f"Error performing web search: {str(e)}"


async def execute_calculator(expression: str) -> str:
    """
    Execute a mathematical calculation safely.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Calculation result or error message
    """
    # Create a safe namespace with only math functions
    safe_dict = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        # Math module functions
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "floor": math.floor,
        "ceil": math.ceil,
        "pi": math.pi,
        "e": math.e,
        "degrees": math.degrees,
        "radians": math.radians,
    }
    
    try:
        # Remove any potentially dangerous characters/keywords
        dangerous = ["import", "__", "exec", "eval", "compile", "open", "file"]
        for word in dangerous:
            if word in expression.lower():
                return f"Error: Expression contains disallowed keyword: {word}"
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        # Format the result
        if isinstance(result, float):
            # Round to reasonable precision
            if result == int(result):
                return str(int(result))
            else:
                return f"{result:.10g}"  # Up to 10 significant figures
        else:
            return str(result)
            
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error calculating expression: {str(e)}"


async def execute_wikipedia_search(query: str) -> str:
    """
    Search Wikipedia and return a summary.
    
    Args:
        query: Topic to search for
        
    Returns:
        Wikipedia summary or error message
    """
    try:
        import wikipedia
        
        # Set language to English
        wikipedia.set_lang("en")
        
        try:
            # Search for the page
            summary = wikipedia.summary(query, sentences=5, auto_suggest=True)
            page = wikipedia.page(query, auto_suggest=True)
            
            result = f"Wikipedia: {page.title}\n\n{summary}\n\nURL: {page.url}"
            return result
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation pages
            options = e.options[:5]  # Show first 5 options
            options_text = "\n".join([f"  - {opt}" for opt in options])
            return f"Wikipedia disambiguation: Multiple articles match '{query}'.\n\nDid you mean:\n{options_text}\n\nPlease be more specific."
            
        except wikipedia.exceptions.PageError:
            return f"Wikipedia: No article found for '{query}'. The page may not exist."
            
    except ImportError:
        return "Error: Wikipedia library not installed. Please install 'wikipedia' package."
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


async def execute_get_url_content(url: str) -> str:
    """
    Fetch and extract readable content from a URL.
    
    Args:
        url: URL to fetch
        
    Returns:
        Extracted text content or error message
    """
    # Validate URL
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; LLM-Council/1.0)"
            })
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content
            main_content = None
            for tag in ["main", "article", "div[class*='content']", "div[class*='post']"]:
                main_content = soup.find(tag)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find("body")
            
            if not main_content:
                return "Error: Could not extract content from page"
            
            # Get text
            text = main_content.get_text(separator="\n", strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)
            
            # Limit length
            max_chars = 4000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Content truncated due to length...]"
            
            # Get title
            title = soup.find("title")
            title_text = title.get_text().strip() if title else "No title"
            
            return f"Content from: {url}\nTitle: {title_text}\n\n{text}"
            
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - Could not fetch URL"
    except httpx.TimeoutException:
        return "Error: Request timed out while fetching URL"
    except Exception as e:
        return f"Error fetching URL content: {str(e)}"


# ============================================================================
# TOOL EXECUTION DISPATCHER
# ============================================================================

async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dict of arguments for the tool
        
    Returns:
        Tool execution result as a string
    """
    tool_functions = {
        "web_search": execute_web_search,
        "calculator": execute_calculator,
        "wikipedia_search": execute_wikipedia_search,
        "get_url_content": execute_get_url_content,
    }
    
    if tool_name not in tool_functions:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        func = tool_functions[tool_name]
        
        # Extract the appropriate argument based on tool
        if tool_name == "web_search":
            result = await func(arguments.get("query", ""))
        elif tool_name == "calculator":
            result = await func(arguments.get("expression", ""))
        elif tool_name == "wikipedia_search":
            result = await func(arguments.get("query", ""))
        elif tool_name == "get_url_content":
            result = await func(arguments.get("url", ""))
        else:
            result = "Error: Tool not implemented"
        
        return result
        
    except Exception as e:
        return f"Error executing tool {tool_name}: {str(e)}"


def get_enabled_tools() -> List[Dict[str, Any]]:
    """
    Get the list of enabled tool schemas.
    
    Returns:
        List of tool schemas in OpenRouter format
    """
    # For now, return all tools. Could be made configurable via config.py
    return TOOL_SCHEMAS

