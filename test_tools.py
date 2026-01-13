"""
Quick test script to verify tool calling functionality.

Run this script to test individual tools without starting the full application.
"""

import asyncio
from backend.tools import (
    execute_web_search,
    execute_calculator,
    execute_wikipedia_search,
    execute_get_url_content
)


async def test_calculator():
    """Test the calculator tool."""
    print("\n=== Testing Calculator ===")
    
    tests = [
        "2 + 2",
        "sqrt(16)",
        "sin(pi/2)",
        "15 * 2847 / 100",  # 15% of 2847
        "log(100)",
    ]
    
    for expression in tests:
        result = await execute_calculator(expression)
        print(f"  {expression} = {result}")


async def test_wikipedia():
    """Test the Wikipedia search tool."""
    print("\n=== Testing Wikipedia Search ===")
    
    queries = [
        "Quantum computing",
        "Python programming language",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = await execute_wikipedia_search(query)
        # Print first 200 characters
        print(f"  {result[:200]}...")


async def test_web_search():
    """Test the web search tool."""
    print("\n=== Testing Web Search ===")
    print("Note: This requires TAVILY_API_KEY or duckduckgo-search installed")
    
    query = "latest AI news 2026"
    print(f"\nQuery: {query}")
    result = await execute_web_search(query)
    # Print first 300 characters
    print(f"  {result[:300]}...")


async def test_url_content():
    """Test the URL content fetcher."""
    print("\n=== Testing URL Content Fetcher ===")
    
    # Test with a simple example URL
    url = "https://example.com"
    print(f"\nURL: {url}")
    result = await execute_get_url_content(url)
    # Print first 200 characters
    print(f"  {result[:200]}...")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Tool Calling Test Suite")
    print("=" * 60)
    
    # Test calculator (always works, no dependencies)
    await test_calculator()
    
    # Test Wikipedia (requires wikipedia package)
    try:
        await test_wikipedia()
    except ImportError as e:
        print(f"\n=== Wikipedia Test Skipped ===")
        print(f"  Error: {e}")
    
    # Test web search (requires tavily or duckduckgo-search)
    try:
        await test_web_search()
    except Exception as e:
        print(f"\n=== Web Search Test Skipped/Failed ===")
        print(f"  Error: {e}")
    
    # Test URL content (requires httpx and beautifulsoup4)
    try:
        await test_url_content()
    except Exception as e:
        print(f"\n=== URL Content Test Failed ===")
        print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

