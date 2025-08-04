/**
 * RESULT-FILTER.JS - Shared result filtering functionality
 * Handles filtering and sorting of search results across all pages
 */

class ResultFilter {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Setup event listeners for all filter selects
        document.addEventListener('change', (event) => {
            if (event.target.classList.contains('result-filter') || 
                event.target.classList.contains('filter-select') ||
                event.target.id === 'result-filter') {
                const filterType = event.target.value;
                const searchId = event.target.dataset.searchId;
                console.log('Filter triggered:', filterType, 'searchId:', searchId);
                this.filterResults(filterType, searchId);
            }
        });
    }

    filterResults(filterType, searchId = null) {
        // Determine the correct results container
        let resultsContainer;
        if (searchId) {
            // History page - specific search results or sidebar history results
            resultsContainer = document.querySelector(`#results-${searchId} .results-content`) ||
                              document.querySelector('.results-section .result-grid') ||
                              document.querySelector('.results-section');
        } else {
            // Search or index page - main results
            resultsContainer = document.querySelector('.results-container .results-content') || 
                              document.querySelector('.results-container') ||
                              document.querySelector('.results-section');
        }

        if (!resultsContainer) {
            console.log('No results container found for filtering. SearchId:', searchId);
            console.log('Available containers:', {
                historyResults: document.querySelector(`#results-${searchId} .results-content`),
                resultGrid: document.querySelector('.results-section .result-grid'),
                resultsSection: document.querySelector('.results-section'),
                resultsContainer: document.querySelector('.results-container')
            });
            return;
        }

        console.log('Found results container:', resultsContainer.className, 'for filter:', filterType);

        const resultGroups = resultsContainer.querySelectorAll('.result-group, .result-provider-section, .source-group');
        const allPapers = [];
        const originalStructure = []; // Store original groups for default restore

        console.log('Found result groups:', resultGroups.length);

        // Collect all papers with their metadata
        resultGroups.forEach((group, groupIndex) => {
            const provider = this.getProviderFromGroup(group);
            const papers = group.querySelectorAll('.result-item, .result-card, .paper-item');
            
            console.log(`Provider: ${provider}, Papers found: ${papers.length}`);
            
            // Store original group structure
            const originalGroup = {
                element: group.cloneNode(true),
                provider: provider,
                papers: []
            };
            
            papers.forEach((paper, paperIndex) => {
                const paperData = this.extractPaperData(paper, provider);
                if (paperData && paperData.title) {
                    const paperObj = {
                        element: paper.cloneNode(true),
                        data: paperData,
                        originalGroup: group,
                        originalOrder: groupIndex * 1000 + paperIndex, // Preserve original order
                        groupIndex: groupIndex,
                        paperIndex: paperIndex
                    };
                    
                    allPapers.push(paperObj);
                    originalGroup.papers.push(paperObj);
                }
            });
            
            originalStructure.push(originalGroup);
        });

        console.log('Total papers collected:', allPapers.length);

        // Sort papers based on filter type
        this.sortPapers(allPapers, filterType);

        // Re-render results
        this.renderFilteredResults(allPapers, filterType, resultsContainer, originalStructure);
    }

    getProviderFromGroup(group) {
        const heading = group.querySelector('h3, h5');
        if (heading) {
            const text = heading.textContent.trim();
            // Extract provider name (remove badge text and icons)
            const match = text.match(/([A-Za-z\s]+?)(?:\s*\(\d+\s+papers?\)|\s*\d+\s+papers?|$)/);
            return match ? match[1].trim() : text;
        }
        
        // For source-group elements, check data-source attribute
        if (group.classList.contains('source-group')) {
            return group.dataset.source ? group.dataset.source.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown';
        }
        
        return 'Unknown';
    }

    extractPaperData(paperElement, provider) {
        // Try multiple selectors for title
        const titleElement = paperElement.querySelector('h4 a, .paper-title, .result-title a, h6.paper-title, .paper-title a');
        const title = titleElement ? titleElement.textContent.trim().replace(/\s*\n\s*/g, ' ') : '';
        
        // Extract year - try multiple selectors and text patterns
        let year = null;
        
        // First try standard selectors
        const yearElement = paperElement.querySelector('.result-meta span:nth-child(2), .meta-item:has(i.fa-calendar) span, .result-year, .meta-item i.fa-calendar + span');
        if (yearElement) {
            const yearMatch = yearElement.textContent.match(/\d{4}/);
            year = yearMatch ? parseInt(yearMatch[0]) : null;
        }
        
        // For history items, look in the text content
        if (!year) {
            const textContent = paperElement.textContent;
            const yearMatch = textContent.match(/Year:\s*(\d{4})/i);
            if (yearMatch) {
                year = parseInt(yearMatch[1]);
            }
        }

        // Extract citations - try multiple selectors and text patterns
        let citations = 0;
        
        // First try standard selectors
        const citationElement = paperElement.querySelector('.result-meta span:nth-child(3), .meta-item:has(i.fa-quote-right) span, .result-citations, .meta-item i.fa-quote-right + span');
        if (citationElement) {
            const citationMatch = citationElement.textContent.match(/(\d+)/);
            citations = citationMatch ? parseInt(citationMatch[0]) : 0;
        }
        
        // For history items, look in the text content
        if (!citations) {
            const textContent = paperElement.textContent;
            const citationMatch = textContent.match(/Citations:\s*(\d+)/i);
            if (citationMatch) {
                citations = parseInt(citationMatch[1]);
            }
        }

        console.log('Extracted paper data:', { title, year, citations, provider });
        
        return {
            title: title,
            year: year,
            citations: citations,
            provider: provider
        };
    }

    sortPapers(papers, filterType) {
        switch (filterType) {
            case 'citations':
                papers.sort((a, b) => (b.data.citations || 0) - (a.data.citations || 0));
                break;
            case 'year':
                papers.sort((a, b) => (b.data.year || 0) - (a.data.year || 0));
                break;
            case 'title':
                papers.sort((a, b) => (a.data.title || '').localeCompare(b.data.title || ''));
                break;
            case 'provider':
                papers.sort((a, b) => (a.data.provider || '').localeCompare(b.data.provider || ''));
                break;
            case 'default':
                // Restore original order
                papers.sort((a, b) => (a.originalOrder || 0) - (b.originalOrder || 0));
                break;
            default:
                // Restore original order for any unrecognized filter
                papers.sort((a, b) => (a.originalOrder || 0) - (b.originalOrder || 0));
                break;
        }
    }

    renderFilteredResults(papers, filterType, container, originalStructure = null) {
        // Clear existing results
        const existingGroups = container.querySelectorAll('.result-group, .result-provider-section, .source-group');
        existingGroups.forEach(group => group.remove());

        if (filterType === 'default' && originalStructure) {
            // Restore original structure exactly
            this.renderOriginalStructure(originalStructure, container);
        } else if (filterType === 'provider') {
            // Group by provider
            this.renderGroupedResults(papers, container);
        } else {
            // Show all papers in a single group for other filters
            this.renderSingleGroupResults(papers, filterType, container);
        }
    }

    renderOriginalStructure(originalStructure, container) {
        // Restore the exact original structure
        originalStructure.forEach(originalGroup => {
            container.appendChild(originalGroup.element);
        });
    }

    renderGroupedResults(papers, container) {
        const groupedPapers = {};
        
        papers.forEach(paper => {
            const provider = paper.data.provider;
            if (!groupedPapers[provider]) {
                groupedPapers[provider] = [];
            }
            groupedPapers[provider].push(paper);
        });

        // Sort providers alphabetically, except for default order
        const sortedProviders = Object.keys(groupedPapers).sort();
        
        sortedProviders.forEach(provider => {
            // Sort papers within each group by original order for default, or keep current sort for provider filter
            const group = this.createResultGroup(provider, groupedPapers[provider]);
            container.appendChild(group);
        });
    }

    renderSingleGroupResults(papers, filterType, container) {
        const filterLabels = {
            'citations': 'Citations',
            'year': 'Year',
            'title': 'Alphabetical',
            'default': 'Default Order'
        };
        
        const groupTitle = `Sorted by ${filterLabels[filterType] || 'Default Order'}`;
        const group = this.createResultGroup(groupTitle, papers);
        container.appendChild(group);
    }

    createResultGroup(title, papers) {
        // Detect result display style based on page context
        const isSearchStyle = document.querySelector('.search-page') || 
                             title.includes('Sorted by') ||
                             document.querySelector('.result-group');
        
        const isHistoryPage = document.querySelector('.history-page');
        
        let groupClass, headingTag;
        
        if (isHistoryPage) {
            groupClass = 'source-group';
            headingTag = 'h3';
        } else if (isSearchStyle) {
            groupClass = 'result-group';
            headingTag = 'h3';
        } else {
            groupClass = 'result-provider-section';
            headingTag = 'h5';
        }
        
        const group = document.createElement('div');
        group.className = groupClass;
        
        const heading = document.createElement(headingTag);
        heading.innerHTML = `
            <i class="fas fa-folder-open me-2"></i>
            ${title}
            ${isSearchStyle || isHistoryPage ? 
                `<small>(${papers.length} papers)</small>` : 
                `<span class="badge bg-secondary">${papers.length} papers</span>`
            }
        `;
        group.appendChild(heading);

        if (isHistoryPage) {
            // History page style - direct append as paper-item
            papers.forEach(paper => {
                paper.element.className = 'paper-item';
                group.appendChild(paper.element);
            });
        } else if (isSearchStyle) {
            // Direct append for search-style results
            papers.forEach(paper => {
                group.appendChild(paper.element);
            });
        } else {
            // Create row structure for card-style results
            const row = document.createElement('div');
            row.className = 'row';
            
            papers.forEach(paper => {
                const col = document.createElement('div');
                col.className = 'col-lg-6 mb-3';
                col.appendChild(paper.element);
                row.appendChild(col);
            });
            
            group.appendChild(row);
        }

        return group;
    }
}

// Initialize global result filter
document.addEventListener('DOMContentLoaded', function() {
    window.resultFilter = new ResultFilter();
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResultFilter;
}
