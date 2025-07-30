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
    console.log("Updating history tabs...");
    const history = getSearchHistory();
    console.log("History items:", history.length);
    const tabsContainer = document.getElementById("searchHistoryTabs");
    if (!tabsContainer) {
      console.error("searchHistoryTabs container not found!");
      return;
    }
    tabsContainer.innerHTML = "";
    
    const iconMapping = {
      semantic_scholar: "/static/icons/semantic.png",
      arxiv: "/static/icons/arxiv.png",
      crossref: "/static/icons/cross.png",
      core: "/static/icons/core.png",
      aggregate: "/static/icons/aggregate.png"
    };

    if (history.length === 0) {
      const li = document.createElement("li");
      li.className = "list-group-item text-muted";
      li.textContent = "No previous searches";
      tabsContainer.appendChild(li);
      return;
    }

    history.forEach((item, index) => {
      console.log(`Adding history item ${index}: ${item.query}`);
      const li = document.createElement("li");
      li.className = "list-group-item d-flex align-items-center";
      li.style.cursor = "pointer";
      
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

      li.addEventListener("click", () => {
        console.log(`Clicked on history item ${index}: ${item.query}`);
        displayHistory(index);
      });
      tabsContainer.appendChild(li);
    });
  }
  
  
  function displayHistory(index) {
    console.log(`Displaying history item ${index}`);
    const history = getSearchHistory();
    if (index < 0 || index >= history.length) {
      console.error(`Invalid history index: ${index}`);
      return;
    }
    const entry = history[index];
    const resultsContent = document.getElementById("resultsContent");
    if (resultsContent) {
      resultsContent.innerHTML = entry.resultsHTML;
      console.log("Results content updated");
      
      setTimeout(() => {
        if (window.resultsSorter) {
          window.resultsSorter.refresh();
        }
      }, 100);
    } else {
      console.error("resultsContent element not found!");
    }
    const queryDisplay = document.getElementById("queryDisplay");
    if (queryDisplay) {
      queryDisplay.textContent = entry.query;
      console.log("Query display updated");
    }
  }

  window.SearchHistory = {
    addSearchHistory,
    clearSearchHistory,
    updateHistoryTabs,
    getSearchHistory,
    displayHistory,
  };
  
  window.getSearchHistory = getSearchHistory;
  window.saveSearchHistory = saveSearchHistory;
  window.addSearchHistory = addSearchHistory;
  window.clearSearchHistory = clearSearchHistory;
  window.updateHistoryTabs = updateHistoryTabs;
  window.displayHistory = displayHistory;

  console.log("SearchHistory defined:", window.SearchHistory);