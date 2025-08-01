#!/usr/bin/env python3
"""
AI Scholar - Phase 6: Conservative Cleanup Strategy
==================================================

This script performs safe, incremental cleanup with dependency analysis.
"""

import os
import sys
from typing import List, Dict, Set

def analyze_dependencies():
    """Analyze what files can be safely removed"""
    
    print("🔍 ANALYZING DEPENDENCIES FOR SAFE CLEANUP")
    print("=" * 60)
    
    # Files that are definitely safe to remove (already replaced)
    safe_to_remove = {
        "searches/arxiv_search.py": "Replaced by ArxivSearchProvider",
        "searches/semantic_search.py": "Replaced by SemanticScholarProvider", 
        "searches/crossref_search.py": "Replaced by CrossRefProvider",
        "searches/core_search.py": "Replaced by COREProvider"
    }
    
    # Files that need dependency analysis
    analyze_files = {
        "ai_scholar/paper_search.py": "Still imported by service_factory",
        "ai_scholar/paper_aggregator.py": "May have dependencies",
        "ai_scholar/ai_ranker.py": "May have dependencies",
        "main.py": "Legacy entry point - may be used"
    }
    
    print("✅ SAFE TO REMOVE (Phase 6.2):")
    for file, reason in safe_to_remove.items():
        exists = "✅" if os.path.exists(file) else "❌"
        print(f"   {exists} {file} - {reason}")
    
    print("\n🔍 NEED ANALYSIS (Phase 6.3):")
    for file, reason in analyze_files.items():
        exists = "✅" if os.path.exists(file) else "❌"
        print(f"   {exists} {file} - {reason}")
    
    return safe_to_remove, analyze_files

def phase_6_2_cleanup():
    """Phase 6.2: Remove safe files (old search modules)"""
    print("\n🧹 PHASE 6.2: REMOVING OLD SEARCH MODULES")
    print("-" * 50)
    
    safe_files = [
        "searches/arxiv_search.py",
        "searches/semantic_search.py", 
        "searches/crossref_search.py",
        "searches/core_search.py"
    ]
    
    for file in safe_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Removed {file}")
            except Exception as e:
                print(f"   ❌ Failed to remove {file}: {e}")
        else:
            print(f"   ⚠️  {file} not found")
    
    # Remove the searches directory if empty
    try:
        if os.path.exists("searches") and not os.listdir("searches"):
            os.rmdir("searches")
            print("   ✅ Removed empty searches/ directory")
    except Exception as e:
        print(f"   ⚠️  Could not remove searches/ directory: {e}")

def test_system():
    """Test that the system still works after cleanup"""
    print("\n🧪 TESTING SYSTEM AFTER CLEANUP")
    print("-" * 40)
    
    try:
        # Test app creation
        sys.path.insert(0, '.')
        from ai_scholar.app_factory import ApplicationFactory
        
        app_factory = ApplicationFactory()
        app = app_factory.create_app(use_new_architecture=True)
        
        # Test main routes
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("   ✅ Main route working")
            else:
                print(f"   ❌ Main route failed: {response.status_code}")
            
            response = client.get('/about')
            if response.status_code == 200:
                print("   ✅ About route working")
            else:
                print(f"   ❌ About route failed: {response.status_code}")
        
        print("   ✅ System test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ System test failed: {e}")
        return False

def main():
    """Main cleanup execution"""
    print("🚀 STARTING CONSERVATIVE PHASE 6 CLEANUP")
    print("=" * 60)
    
    # Step 1: Analyze dependencies
    safe_files, analyze_files = analyze_dependencies()
    
    # Step 2: Remove safe files only
    phase_6_2_cleanup()
    
    # Step 3: Test system
    if test_system():
        print("\n✅ PHASE 6.2 CLEANUP SUCCESSFUL!")
        print("🔄 Ready for Phase 6.3: Dependency Analysis")
    else:
        print("\n❌ SYSTEM TEST FAILED - STOPPING CLEANUP")
        print("🔄 Please fix issues before continuing.")

if __name__ == "__main__":
    main()
