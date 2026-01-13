"""OpenRouter API client for making LLM requests."""

import httpx
import json
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL, MAX_TOOL_ITERATIONS


async def query_model(
    model: str,
    messages: List[Dict[str, Any]],
    timeout: float = 120.0,
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tool_iterations: int = MAX_TOOL_ITERATIONS
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API with optional tool calling support.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        tools: Optional list of tool schemas for function calling
        max_tool_iterations: Maximum number of tool calling iterations

    Returns:
        Response dict with 'content', 'tool_calls', and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Track tool usage across iterations
    all_tool_calls = []
    iteration = 0

    while iteration < max_tool_iterations:
        payload = {
            "model": model,
            "messages": messages,
            "extra_body": {
                "reasoning": {
                    "effort": "high",      # or "medium"/"low"/"minimal"/"none"
                    # OR: "max_tokens": 2000  (often used for Anthropic-style budgets)
                    "exclude": True       # set True if you want hidden reasoning
                }
            }
        }

        # Add tools to payload if provided
        if tools and iteration == 0:  # Only send tools on first iteration
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                message = data['choices'][0]['message']

                # Check if model made tool calls
                tool_calls = message.get('tool_calls')

                if tool_calls and tools:
                    # Model wants to use tools
                    # Add assistant message with tool calls to history
                    messages.append({
                        "role": "assistant",
                        "content": message.get('content') or "",
                        "tool_calls": tool_calls
                    })

                    # Execute tools and add results
                    from .tools import execute_tool

                    for tool_call in tool_calls:
                        tool_call_id = tool_call.get('id', f"call_{iteration}")
                        function_name = tool_call['function']['name']
                        
                        # Parse arguments (may be string or dict)
                        arguments = tool_call['function']['arguments']
                        if isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments)
                            except json.JSONDecodeError:
                                arguments = {}

                        # Execute the tool
                        tool_result = await execute_tool(function_name, arguments)

                        # Track this tool call
                        all_tool_calls.append({
                            "name": function_name,
                            "arguments": arguments,
                            "result": tool_result
                        })

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": tool_result
                        })

                    # Continue loop to get model's next response
                    iteration += 1
                    continue

                else:
                    # Model provided final response (no more tool calls)
                    return {
                        'content': message.get('content'),
                        'reasoning_details': message.get('reasoning_details'),
                        'tool_calls': all_tool_calls if all_tool_calls else None
                    }

        except Exception as e:
            print(f"Error querying model {model}: {e}")
            # If we have partial results from tool calls, return them
            if all_tool_calls:
                return {
                    'content': f"Error after {len(all_tool_calls)} tool calls: {str(e)}",
                    'tool_calls': all_tool_calls
                }
            return None

    # Max iterations reached
    print(f"Warning: Model {model} reached max tool iterations ({max_tool_iterations})")
    return {
        'content': "Maximum tool calling iterations reached. Please try rephrasing your question.",
        'tool_calls': all_tool_calls if all_tool_calls else None
    }


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel with optional tool calling support.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model
        tools: Optional list of tool schemas for function calling

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages.copy(), tools=tools) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
