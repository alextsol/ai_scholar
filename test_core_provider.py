#!/usr/bin/env python3
"""Test script for CORE provider exception handling"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_scholar.providers.core_provider import COREProvider
from ai_scholar.utils.exceptions import RateLimitError, APIUnavailableError, AuthenticationError, NetworkError, TimeoutError

def test_core_provider():
    """Test CORE provider with various queries"""
    
    print("🧪 Testing CORE Provider Exception Handling")
    print("=" * 50)
    
    # Initialize provider
    provider = COREProvider()
    
    # Test queries
    test_queries = [
        "machine learning",
        "artificial intelligence",
        "deep learning neural networks"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 30)
        
        try:
            results = provider.search(query, limit=5)
            print(f"✅ Success: Found {len(results)} results")
            
            if results:
                print("📄 Sample result:")
                result = results[0]
                print(f"   Title: {result.get('title', 'N/A')[:100]}...")
                print(f"   Authors: {result.get('authors', 'N/A')}")
                print(f"   Year: {result.get('year', 'N/A')}")
                print(f"   DOI: {result.get('doi', 'N/A')}")
            else:
                print("ℹ️  No results found (but no error thrown)")
                
        except RateLimitError as e:
            print(f"⏰ Rate Limit Error: {e.user_message}")
            print(f"   Retry after: {e.retry_after_seconds} seconds")
            
        except APIUnavailableError as e:
            print(f"🚫 API Unavailable: {e.user_message}")
            
        except AuthenticationError as e:
            print(f"🔐 Authentication Error: {e.user_message}")
            
        except NetworkError as e:
            print(f"🌐 Network Error: {e.user_message}")
            
        except TimeoutError as e:
            print(f"⏱️  Timeout Error: {e.user_message}")
            
        except Exception as e:
            print(f"❌ Unexpected Error: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_core_provider()
