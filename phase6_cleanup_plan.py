#!/usr/bin/env python3
"""
AI Scholar - Phase 6: Legacy Code Cleanup Plan
==============================================

This script analyzes the codebase and provides a systematic cleanup plan
for removing duplicate functionality and old architecture files.

Usage: python phase6_cleanup_plan.py
"""

import os
import sys
from datetime import datetime

def analyze_codebase():
    """Analyze the current codebase structure and identify cleanup targets"""
    
    print("=" * 80)
    print("🧹 AI SCHOLAR - PHASE 6 CLEANUP ANALYSIS")
    print("=" * 80)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Files and directories to analyze
    cleanup_targets = {
        "Legacy Search Modules": {
            "directory": "searches/",
            "files": [
                "arxiv_search.py",
                "core_search.py", 
                "crossref_search.py",
                "semantic_search.py"
            ],
            "status": "🔴 DUPLICATE - Replaced by new providers",
            "action": "Remove after verification"
        },
        
        "Root Level Legacy Files": {
            "directory": "./",
            "files": [
                "main.py",
                "key1.py",
                "chatbot.py",
                "paper_aggregator.py",
                "paper_search.py",
                "ai_ranker.py",
                "analytics.py",
                "fairness.py",
                "prompts.py",
                "utils.py",
                "endpoints.py"
            ],
            "status": "🟡 LEGACY - May have dependencies",
            "action": "Analyze dependencies then remove"
        },
        
        "Old AI Scholar Module": {
            "directory": "ai_scholar/",
            "files": [
                "ai_ranker.py",
                "analytics.py", 
                "paper_aggregator.py",
                "paper_search.py",
                "prompts.py"
            ],
            "status": "🔴 DUPLICATE - Replaced by new architecture",
            "action": "Remove after verification"
        },
        
        "Utility Modules": {
            "directory": "utils/",
            "files": [
                "utils.py"
            ],
            "status": "🟡 REVIEW - May contain useful functions",
            "action": "Extract useful functions, then remove"
        },
        
        "Cache Directories": {
            "directory": "__pycache__/",
            "files": ["*.pyc files"],
            "status": "🟢 SAFE - Can be removed",
            "action": "Clean all cache files"
        }
    }
    
    print("🎯 CLEANUP TARGETS IDENTIFIED:")
    print("-" * 50)
    
    for category, info in cleanup_targets.items():
        print(f"\n📁 {category}")
        print(f"   📂 Location: {info['directory']}")
        print(f"   📋 Status: {info['status']}")
        print(f"   🔧 Action: {info['action']}")
        print("   📄 Files:")
        for file in info['files']:
            file_path = os.path.join(info['directory'], file)
            exists = "✅" if os.path.exists(file_path) or file.endswith('.pyc files') else "❌"
            print(f"      {exists} {file}")
    
    print("\n" + "=" * 80)
    print("📋 CLEANUP PHASES:")
    print("=" * 80)
    
    phases = [
        {
            "name": "Phase 6.1: Safe Cleanup",
            "description": "Remove cache files and obviously duplicate files",
            "risk": "🟢 Low Risk",
            "files": ["__pycache__/ directories", "*.pyc files"]
        },
        {
            "name": "Phase 6.2: Search Module Cleanup", 
            "description": "Remove old search modules (replaced by new providers)",
            "risk": "🟡 Medium Risk", 
            "files": ["searches/ directory contents"]
        },
        {
            "name": "Phase 6.3: Legacy Module Analysis",
            "description": "Analyze and remove duplicate functionality in ai_scholar/",
            "risk": "🟡 Medium Risk",
            "files": ["ai_scholar/ai_ranker.py", "ai_scholar/analytics.py", "others"]
        },
        {
            "name": "Phase 6.4: Root Level Cleanup",
            "description": "Remove root level legacy files after dependency check",
            "risk": "🔴 High Risk",
            "files": ["main.py", "chatbot.py", "paper_aggregator.py", "others"]
        },
        {
            "name": "Phase 6.5: Configuration Consolidation",
            "description": "Consolidate configuration and remove unused imports",
            "risk": "🟡 Medium Risk", 
            "files": ["config.py", "runtime.py", "import statements"]
        },
        {
            "name": "Phase 6.6: Final Verification",
            "description": "Test system and ensure no broken dependencies",
            "risk": "🟢 Low Risk",
            "files": ["All remaining files"]
        }
    ]
    
    for i, phase in enumerate(phases, 1):
        print(f"\n{i}. {phase['name']}")
        print(f"   📝 {phase['description']}")
        print(f"   ⚠️  Risk Level: {phase['risk']}")
        print(f"   📁 Target Files: {', '.join(phase['files'])}")
    
    print("\n" + "=" * 80)
    print("🚨 IMPORTANT SAFETY MEASURES:")
    print("=" * 80)
    print("1. 📁 Create backup before major deletions")
    print("2. 🧪 Test application after each cleanup phase")
    print("3. 🔍 Verify no imports point to deleted modules")
    print("4. 📝 Update documentation after cleanup")
    print("5. 🔄 Keep git history for recovery if needed")
    
    print("\n" + "=" * 80)
    print("✅ READY FOR PHASE 6 CLEANUP!")
    print("🚀 Recommendation: Start with Phase 6.1 (Safe Cleanup)")
    print("=" * 80)

if __name__ == "__main__":
    analyze_codebase()
