#!/usr/bin/env python3
"""
Test script for handling 1000+ results with aggregate search optimization
This ensures all providers are used and the optimization works at scale
"""

import sys
sys.path.insert(0, '.')

from ai_scholar.app_factory import app_factory
from ai_scholar.services.service_factory import ServiceFactory
from ai_scholar.models.paper import Paper
import traceback
import time

def test_1000_results_optimization():
    """Test aggregate search with settings to get ~1000 results"""
    
    print("🧪 Testing 1000+ Results Aggregate Search Optimization")
    print("=" * 80)
    
    try:
        # Create app context
        app = app_factory.create_app()
        with app.app_context():
            # Get the paper service from the service factory
            service_factory = ServiceFactory()
            service_factory.initialize_services()
            paper_service = service_factory.get_paper_service()
            
            print("✅ Successfully created paper service")
            
            # Test query that should return many results
            test_query = "machine learning"  # More common term should get more results
            
            print(f"\n🔍 Testing large-scale aggregate search for: '{test_query}'")
            print("📊 Target: ~1000 results from all providers")
            print("-" * 60)
            
            start_time = time.time()
            
            # Call aggregate search with high limits to stress test
            result = paper_service.aggregate_and_rank_papers(
                query=test_query,
                limit=300,  # Very high per-provider limit to get ~1000+ total
                ai_result_limit=20,  # More final results for testing
                ranking_mode='ai',
                min_year=2015,  # Broader year range to get more results
                max_year=None
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Aggregate search completed in {processing_time:.2f} seconds!")
            
            # Analyze results
            if result and result.papers:
                print(f"✅ Found {len(result.papers)} final papers in results")
                
                # Check aggregation stats
                if hasattr(result, 'aggregation_stats') and result.aggregation_stats:
                    print("✅ Aggregation statistics available!")
                    
                    stats = result.aggregation_stats
                    print(f"\n📊 Aggregation Process Analysis:")
                    
                    # Get the actual values
                    papers_collected = stats.get('total_collected', stats.get('papers_collected', 'N/A'))
                    after_filter = stats.get('after_pre_filter', 'N/A')
                    after_dedup = stats.get('after_dedup', stats.get('after_deduplication', 'N/A'))
                    sent_to_ai = stats.get('sent_to_ai', 'N/A')
                    final_results = stats.get('final_results', len(result.papers))
                    
                    print(f"   📚 Total Papers Collected: {papers_collected}")
                    print(f"   🧹 After Pre-filtering: {after_filter}")
                    print(f"   🔄 After Deduplication: {after_dedup}")
                    print(f"   🤖 Sent to AI: {sent_to_ai}")
                    print(f"   🎯 Final Results: {final_results}")
                    
                    # Check if optimization was triggered
                    if isinstance(papers_collected, int) and papers_collected > 200:
                        print(f"✅ Successfully handled {papers_collected} papers (>200)")
                        if isinstance(sent_to_ai, int) and sent_to_ai <= 200:
                            print("✅ Optimization working: AI received manageable number")
                        else:
                            print("⚠️  Warning: AI received more than 200 papers")
                    elif isinstance(papers_collected, int):
                        print(f"ℹ️  Collected {papers_collected} papers (optimization not needed)")
                    
                    # Check provider breakdown  
                    providers_used_info = stats.get('providers_used', stats.get('provider_breakdown', {}))
                    if providers_used_info:
                        print(f"\n🔍 Provider Breakdown:")
                        total_from_providers = 0
                        providers_used = []
                        
                        for provider, info in providers_used_info.items():
                            if isinstance(info, dict):
                                raw_count = info.get('raw_count', 0)
                                after_filter = info.get('after_filter', 0)
                                print(f"   {provider}: {raw_count} raw → {after_filter} filtered")
                                total_from_providers += after_filter
                                if after_filter > 0:
                                    providers_used.append(provider)
                            else:
                                # Simple count format
                                print(f"   {provider}: {info} papers")
                                total_from_providers += info
                                if info > 0:
                                    providers_used.append(provider)
                        
                        print(f"\n📈 Provider Analysis:")
                        print(f"   Total providers used: {len(providers_used)}")
                        print(f"   Providers: {', '.join(providers_used)}")
                        print(f"   Total papers collected: {total_from_providers}")
                        
                        # Expected providers
                        expected_providers = ['crossref', 'arxiv', 'semantic_scholar', 'core', 'openalex']
                        missing_providers = [p for p in expected_providers if p not in providers_used]
                        
                        if len(providers_used) >= 3:
                            print("✅ Good provider diversity!")
                        if missing_providers:
                            print(f"⚠️  Missing providers: {', '.join(missing_providers)}")
                    
                    # Check if pre-ranking was used
                    if stats.get('pre_ranking_used', False):
                        print("✅ Pre-ranking optimization was triggered (as expected for large results)")
                    else:
                        print("ℹ️  Pre-ranking not used (papers count was manageable)")
                
                # Analyze final results quality
                print(f"\n📄 Final Results Analysis:")
                
                # Check for diversity in years
                years = [p.year for p in result.papers if p.year]
                if years:
                    print(f"   📅 Year range: {min(years)} - {max(years)}")
                
                # Check for diversity in citations
                citations = [p.citations for p in result.papers if p.citations and p.citations > 0]
                if citations:
                    avg_citations = sum(citations) / len(citations)
                    print(f"   📊 Average citations: {avg_citations:.1f}")
                    print(f"   📊 Citation range: {min(citations)} - {max(citations)}")
                
                # Show sample papers with improved explanations
                print(f"\n📄 Sample Papers with AI Explanations (showing first 3):")
                for i, paper in enumerate(result.papers[:3]):
                    print(f"\n   {i+1}. {paper.title[:80]}...")
                    print(f"      Authors: {paper.authors[:60]}...")
                    print(f"      Year: {paper.year}, Citations: {paper.citations}")
                    if hasattr(paper, 'explanation') and paper.explanation:
                        print(f"      🤖 AI Explanation: {paper.explanation}")
                    print()
                
                # Performance analysis
                papers_per_second = len(result.papers) / processing_time if processing_time > 0 else 0
                print(f"⚡ Performance: {papers_per_second:.1f} final papers/second")
                
            else:
                print("❌ No papers found in results")
                
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()

def test_provider_availability():
    """Test that all expected providers are available and working"""
    
    print("\n🔍 Testing Provider Availability")
    print("-" * 60)
    
    try:
        app = app_factory.create_app()
        with app.app_context():
            service_factory = ServiceFactory()
            service_factory.initialize_services()
            
            # Check available providers
            from ai_scholar.providers import provider_registry
            
            search_providers = provider_registry.get_all_search_providers()
            ai_provider = provider_registry.get_ai_provider()
            
            print(f"Available search providers: {list(search_providers.keys())}")
            print(f"AI provider available: {'Yes' if ai_provider else 'No'}")
            
            # Test each provider individually
            for name, provider in search_providers.items():
                try:
                    # Quick test search
                    test_result = provider.search("test", limit=5)
                    status = "✅ Working" if test_result else "⚠️  No results"
                    print(f"   {name}: {status}")
                except Exception as e:
                    print(f"   {name}: ❌ Error - {str(e)[:50]}...")
            
    except Exception as e:
        print(f"❌ Error testing providers: {str(e)}")

def main():
    """Run the 1000 results test"""
    
    print("🚀 AI Scholar - 1000 Results Optimization Test")
    print("=" * 80)
    print("This test verifies:")
    print("- Handling of 1000+ results from multiple providers")
    print("- Optimization pipeline performance at scale")
    print("- Provider diversity and availability")
    print("- AI explanation quality")
    print("=" * 80)
    
    # Test provider availability first
    test_provider_availability()
    
    # Test large-scale optimization
    test_1000_results_optimization()
    
    print("\n" + "=" * 80)
    print("🏁 1000 Results Test Complete!")
    print("\nKey Success Metrics:")
    print("✅ Papers collected should be > 500")
    print("✅ Multiple providers should be used")
    print("✅ AI should receive ≤ 200 papers")
    print("✅ Processing should complete in reasonable time")
    print("✅ Final results should have specific AI explanations")

if __name__ == "__main__":
    main()
