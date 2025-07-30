import hashlib
from datetime import datetime, timedelta

# Simple in-memory cache for search results
search_cache = {}
CACHE_DURATION = timedelta(hours=1)

def get_cache_key(query, limit, backend, min_year, max_year):
    cache_data = f"{query}_{limit}_{backend}_{min_year}_{max_year}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def get_cached_result(cache_key):
    if cache_key in search_cache:
        cached_data, timestamp = search_cache[cache_key]
        if datetime.now() - timestamp < CACHE_DURATION:
            print(f"Using cached result for query")
            return cached_data
        else:
            del search_cache[cache_key]
    return None

def cache_result(cache_key, result):
    search_cache[cache_key] = (result, datetime.now())

def clear_search_cache():
    global search_cache
    search_cache.clear()
    print("Search cache cleared")

def get_cache_stats():
    total_entries = len(search_cache)
    expired_entries = 0
    current_time = datetime.now()
    
    for cache_key, (result, timestamp) in search_cache.items():
        if current_time - timestamp >= CACHE_DURATION:
            expired_entries += 1
    
    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries
    }

def cleanup_expired_cache():
    global search_cache
    current_time = datetime.now()
    expired_keys = []
    
    for cache_key, (result, timestamp) in search_cache.items():
        if current_time - timestamp >= CACHE_DURATION:
            expired_keys.append(cache_key)
    
    for key in expired_keys:
        del search_cache[key]
    
    if expired_keys:
        print(f"Cleaned up {len(expired_keys)} expired cache entries")
