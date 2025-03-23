// history.js
console.log("history.js loaded");
function getSearchHistory() {
    const history = localStorage.getItem("searchHistory");
    return history ? JSON.parse(history) : [];
  }

  function saveSearchHistory(history) {
    localStorage.setItem("searchHistory", JSON.stringify(history));
  }

  function addSearchHistory(query, resultsHTML, source) {
    let history = getSearchHistory();
    history.unshift({ query, resultsHTML, source });
    history = history.slice(0, 10);
    saveSearchHistory(history);
    updateHistoryTabs();
  }

  function clearSearchHistory() {
    localStorage.removeItem("searchHistory");
    updateHistoryTabs();
  }
  
  function updateHistoryTabs() {
    const history = getSearchHistory();
    const tabsContainer = document.getElementById("searchHistoryTabs");
    if (!tabsContainer) return;
    tabsContainer.innerHTML = "";
    
    // Map each source to its icon URL (adjust paths as needed)
    const iconMapping = {
      semantic_scholar: "/static/icons/semantic.png",
      arxiv: "/static/icons/arxiv.png",
      crossref: "/static/icons/cross.png",
      core: "/static/icons/core.png",
      aggregate: "/static/icons/aggregate.png"  // New icon for aggregate searches
    };
  
    history.forEach((item, index) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex align-items-center";
      li.style.cursor = "pointer";
      
      // Use the source from the entry, defaulting to a normal backend if not provided.
      const src = item.source || "default";
      if (iconMapping[src]) {
        const img = document.createElement("img");
        img.src = iconMapping[src];
        img.alt = src;
        img.style.width = "16px";
        img.style.height = "16px";
        img.style.marginRight = "8px";
        li.appendChild(img);
      }
      
      const span = document.createElement("span");
      span.textContent = item.query;
      li.appendChild(span);
  
      li.addEventListener("click", () => displayHistory(index));
      tabsContainer.appendChild(li);
    });
  }
  
  
  function displayHistory(index) {
    const history = getSearchHistory();
    if (index < 0 || index >= history.length) return;
    const entry = history[index];
    const resultsContent = document.getElementById("resultsContent");
    if (resultsContent) {
      resultsContent.innerHTML = entry.resultsHTML;
    }
    const queryDisplay = document.getElementById("queryDisplay");
    if (queryDisplay) {
      queryDisplay.textContent = entry.query;
    }
  }

  window.SearchHistory = {
    addSearchHistory,
    clearSearchHistory,
    updateHistoryTabs,
    getSearchHistory,
    displayHistory,
  };
  console.log("SearchHistory defined:", window.SearchHistory);