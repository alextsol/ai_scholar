// main.js
document.addEventListener("DOMContentLoaded", () => {
  initDarkModeToggle("darkModeToggle");

  function ensureSearchHistoryLoaded(callback) {
    if (typeof SearchHistory !== "undefined") {
      callback();
    } else {
      setTimeout(() => ensureSearchHistoryLoaded(callback), 100);
    }
  }

  ensureSearchHistoryLoaded(() => {
    SearchHistory.updateHistoryTabs();
    console.log("SearchHistory updated.");
  });

  const searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", () => {
      Loader.showLoader("loader-overlay");
    });
  }

  if (window.currentQuery && window.currentResultsHTML && typeof SearchHistory !== "undefined") {
    SearchHistory.addSearchHistory(window.currentQuery, window.currentResultsHTML);
  }
});
