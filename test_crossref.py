"""Test script for CrossRef search provider"""
import sys
import logging
from ai_scholar.providers.crossref_provider import CrossRefProvider

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_crossref_search():
    """Test CrossRef search functionality"""
    print("=" * 60)
    print("Testing CrossRef Search Provider")
    print("=" * 60)
    
    # Initialize provider
    print("\n1. Initializing CrossRef provider...")
    provider = CrossRefProvider()
    print(f"   Provider name: {provider.get_provider_name()}")
    
    # Check availability
    print("\n2. Checking if CrossRef is available...")
    available = provider.is_available()
    print(f"   Available: {available}")
    
    # Test search
    print("\n3. Testing search with query: 'machine learning'")
    query = "machine learning"
    limit = 10
    
    try:
        results = provider.search(query, limit)
        
        print(f"\n   ✓ Search completed successfully!")
        print(f"   Results found: {len(results)}")
        
        if results:
            print("\n   First 3 results:")
            for i, paper in enumerate(results[:3], 1):
                print(f"\n   Paper {i}:")
                print(f"   Title: {paper.get('title', 'N/A')[:80]}...")
                print(f"   Authors: {paper.get('authors', 'N/A')[:60]}...")
                print(f"   Year: {paper.get('year', 'N/A')}")
                print(f"   Citations: {paper.get('citations', 'N/A')}")
                print(f"   URL: {paper.get('url', 'N/A')[:60]}...")
                print(f"   Source: {paper.get('source', 'N/A')}")
        else:
            print("\n   ✗ No results returned (but no error)")
            
    except Exception as e:
        print(f"\n   ✗ Search failed with error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test with year filter
    print("\n4. Testing search with year filter (2020-2024)...")
    try:
        results_filtered = provider.search(query, limit, min_year=2020, max_year=2024)
        print(f"   ✓ Filtered search completed!")
        print(f"   Results found: {len(results_filtered)}")
        
        if results_filtered:
            print(f"   Sample result year: {results_filtered[0].get('year', 'N/A')}")
    except Exception as e:
        print(f"   ✗ Filtered search failed: {str(e)}")
    
    # Test query validation
    print("\n5. Testing query validation...")
    test_queries = [
        ("", False, "Empty query"),
        ("a", False, "Too short"),
        ("machine learning", True, "Valid query"),
        ("  neural networks  ", True, "Valid with whitespace"),
    ]
    
    for test_query, should_pass, description in test_queries:
        result = provider.validate_query(test_query)
        status = "✓" if result == should_pass else "✗"
        print(f"   {status} {description}: {result}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_crossref_search()
