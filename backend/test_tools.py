"""
Simple test script for tool implementations.
Run with: uv run python test_tools.py
"""

import asyncio
from backend.tools import calculator, wikipedia_search, get_url_content, web_search


async def test_calculator():
    """Test the calculator tool."""
    print("\n=== Testing Calculator ===")
    
    tests = [
        "15 * 2847 / 100",
        "sqrt(144)",
        "2 ** 10",
        "sin(pi / 2)",
        "log(100, 10)",
    ]
    
    for expr in tests:
        result = await calculator(expr)
        print(f"  {expr} = {result}")


async def test_wikipedia():
    """Test the Wikipedia search tool."""
    print("\n=== Testing Wikipedia ===")
    
    result = await wikipedia_search("Python programming language")
    print(f"  {result[:200]}...")


async def test_web_search():
    """Test the web search tool."""
    print("\n=== Testing Web Search ===")
    
    result = await web_search("artificial intelligence news 2026")
    print(f"  {result[:300]}...")


async def test_url_content():
    """Test the URL content extraction tool."""
    print("\n=== Testing URL Content ===")
    
    # Use a simple, bot-friendly URL
    result = await get_url_content("https://example.com")
    print(f"  {result[:200]}...")


async def main():
    """Run all tests."""
    print("Testing LLM Council Tool Implementations")
    print("=" * 50)
    
    await test_calculator()
    await test_wikipedia()
    await test_web_search()
    await test_url_content()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

