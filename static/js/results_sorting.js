class ResultsSorter {
  constructor() {
    this.originalHTML = '';
    this.papers = [];
    this.currentSort = 'default';
  }

  init() {
    const sortSelect = document.getElementById('sortBy');
    const resultsContent = document.getElementById('resultsContent');
    
    if (sortSelect && resultsContent) {
      this.originalHTML = resultsContent.innerHTML;
      this.parseResults();
      
      sortSelect.addEventListener('change', (e) => {
        this.sortResults(e.target.value);
      });
    }
  }

  parseResults() {
    const resultsContent = document.getElementById('resultsContent');
    if (!resultsContent) return;

    this.papers = [];
    
    const sourceHeaders = resultsContent.querySelectorAll('h4');
    
    sourceHeaders.forEach(header => {
      const source = header.textContent.replace(' results:', '');
      const ul = header.nextElementSibling;
      
      if (ul && ul.tagName === 'UL') {
        const listItems = ul.querySelectorAll('li');
        
        listItems.forEach(li => {
          const paper = this.parsePaperFromHTML(li, source);
          if (paper) {
            this.papers.push({
              ...paper,
              element: li.cloneNode(true),
              source: source
            });
          }
        });
      }
    });
  }

  parsePaperFromHTML(li, source) {
    const html = li.innerHTML;
    
    const titleMatch = html.match(/<strong>(.*?)<\/strong>/);
    const title = titleMatch ? titleMatch[1] : '';
    
    const yearMatch = html.match(/\((\d{4})\)/);
    const year = yearMatch ? parseInt(yearMatch[1]) : 0;
    
    const citationMatch = html.match(/<strong>Citations<\/strong>:\s*([^<]+)/i);
    let citations = -1;
    if (citationMatch) {
      const citationText = citationMatch[1].trim().toLowerCase();
      if (citationText !== 'n/a' && citationText !== 'not available' && !isNaN(citationText)) {
        citations = parseInt(citationText);
      }
    }
    
    const authorsMatch = html.match(/<strong>Authors<\/strong>:\s*([^<]+)/i);
    const authors = authorsMatch ? authorsMatch[1].trim() : '';
    
    const urlMatch = html.match(/href='([^']+)'/);
    const url = urlMatch ? urlMatch[1] : '';

    return {
      title: title,
      year: year,
      citations: citations,
      authors: authors,
      url: url,
      originalHTML: li.outerHTML
    };
  }

  sortResults(sortType) {
    this.currentSort = sortType;
    
    if (sortType === 'default') {
      document.getElementById('resultsContent').innerHTML = this.originalHTML;
      return;
    }

    const papersBySource = {};
    this.papers.forEach(paper => {
      if (!papersBySource[paper.source]) {
        papersBySource[paper.source] = [];
      }
      papersBySource[paper.source].push(paper);
    });

    Object.keys(papersBySource).forEach(source => {
      papersBySource[source].sort((a, b) => {
        switch (sortType) {
          case 'citations-desc':
            return b.citations - a.citations;
          case 'citations-asc':
            return a.citations - b.citations;
          case 'year-desc':
            return b.year - a.year;
          case 'year-asc':
            return a.year - b.year;
          case 'title-asc':
            return a.title.toLowerCase().localeCompare(b.title.toLowerCase());
          default:
            return 0;
        }
      });
    });

    this.rebuildHTML(papersBySource);
  }

  rebuildHTML(papersBySource) {
    const resultsContent = document.getElementById('resultsContent');
    if (!resultsContent) return;

    let newHTML = '';

    Object.keys(papersBySource).forEach(source => {
      newHTML += `<h4>${source} results:</h4><ul>`;
      
      papersBySource[source].forEach(paper => {
        newHTML += paper.element.outerHTML;
      });
      
      newHTML += '</ul>';
    });

    resultsContent.innerHTML = newHTML;
  }

  buildPaperHTML(paper) {
    let html = `<li><strong>${paper.title}</strong> (${paper.year || 'Unknown year'})<br>`;
    html += `<strong>Authors</strong>: ${paper.authors}<br>`;
    html += `<strong>Citations</strong>: ${paper.citations || 'N/A'}<br>`;
    html += `<a href='${paper.url}' target='_blank'>Read More</a></li></br>`;
    
    return html;
  }

  refresh() {
    this.originalHTML = document.getElementById('resultsContent').innerHTML;
    this.parseResults();
    if (this.currentSort !== 'default') {
      this.sortResults(this.currentSort);
    }
  }
}

document.addEventListener('DOMContentLoaded', function() {
  window.resultsSorter = new ResultsSorter();
  
  setTimeout(() => {
    if (document.getElementById('resultsContent') && document.getElementById('resultsContent').innerHTML.trim()) {
      window.resultsSorter.init();
    }
  }, 100);
});

window.ResultsSorter = ResultsSorter;
