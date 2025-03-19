// history.js
console.log("history.js loaded");
function getSearchHistory() {
    const history = localStorage.getItem("searchHistory");
    return history ? JSON.parse(history) : [];
  }
  function saveSearchHistory(history) {
    localStorage.setItem("searchHistory", JSON.stringify(history));
  }
  function addSearchHistory(query, resultsHTML) {
    let history = getSearchHistory();
    history.unshift({ query, resultsHTML });
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
    history.forEach((item, index) => {
      const li = document.createElement("li");
      li.className = "list-group-item";
      li.style.cursor = "pointer";
      li.textContent = item.query;
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