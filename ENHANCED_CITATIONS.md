# Enhanced "Most Cited" Aggregated Search

## Overview

The aggregated search has been enhanced to optimize for citation-based ranking by intelligently selecting providers and distributing search limits to maximize the collection of highly cited papers.

## Key Improvements

### 1. **Provider Optimization for Citations**
When using `ranking_mode='citations'`, the system now:
- **Excludes ArXiv**: Since ArXiv doesn't provide citation data, it's excluded from citation-based searches
- **Focuses on Citation-Rich Providers**: Prioritizes Semantic Scholar, CrossRef, OpenAlex, and CORE
- **Optimizes Resource Allocation**: Distributes higher limits to providers with better citation data

### 2. **Intelligent Limit Distribution**
- **Semantic Scholar**: Gets 2x base limit (excellent citation data)
- **CrossRef**: Gets 1.5x base limit (reliable citation counts)  
- **OpenAlex**: Gets 1.5x base limit (good coverage)
- **CORE**: Gets standard limit (limited citation data)
- **Total Target**: Aims for 10x final results or 500 papers minimum

### 3. **Enhanced Citation Ranking**
- **Quality Filtering**: Prioritizes papers with actual citation data
- **Fallback Strategy**: Includes recent papers without citations as secondary candidates
- **Better Explanations**: Provides context-aware explanations for citation rankings

### 4. **Smart Pre-filtering**
- Filters out papers with missing or invalid citation data
- Uses publication year as fallback ranking for papers without citations
- Maintains result quality while maximizing coverage

## Usage

```python
# Enhanced citation search
result = ai_scholar.search_papers(
    query="machine learning",
    limit=150,              # Higher per-provider limit
    ai_result_limit=20,     # Final results wanted
    ranking_mode='citations' # Triggers optimization
)
```

## Expected Results

### Provider Selection
- ✅ Semantic Scholar: Enhanced limit for best citation data
- ✅ CrossRef: Enhanced limit for reliable citations  
- ✅ OpenAlex: Enhanced limit for broad coverage
- ✅ CORE: Standard limit (limited citations)
- ❌ ArXiv: Excluded (no citation data)

### Result Quality
- Higher proportion of papers with citation data
- Better distribution of highly cited vs. recent papers
- More accurate citation-based ranking
- Contextual explanations for each paper's ranking

### Performance Benefits
- **More Targeted**: Focuses computational resources on citation-rich providers
- **Higher Quality**: Better signal-to-noise ratio in citation data
- **Scalable**: Can handle larger result sets efficiently
- **Transparent**: Clear statistics on provider usage and optimization

## Example Output

```
📊 Provider Usage Optimization:
   semantic_scholar: 284 raw → 142 filtered
   crossref: 198 raw → 156 filtered  
   openalex: 176 raw → 134 filtered
   core: 89 raw → 67 filtered

📊 Citation Analysis:
   Papers with citation data: 18/20
   Average citations: 1,247 citations
   Citation range: 23 - 15,432 citations
   High impact papers (>100 citations): 15
```

This enhancement ensures that when users select "Most Cited Papers" ranking, they get the highest quality, most impactful papers available from the academic databases.
