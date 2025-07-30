document.addEventListener("DOMContentLoaded", () => {
  initDarkModeToggle("darkModeToggle");

  const clearHistoryButton = document.getElementById("clearHistoryButton");
  if (clearHistoryButton) {
    clearHistoryButton.addEventListener("click", () => {
      if (typeof clearSearchHistory !== "undefined") {
        clearSearchHistory();
      } else if (window.SearchHistory) {
        window.SearchHistory.clearSearchHistory();
      }
    });
  }

  function ensureSearchHistoryLoaded(callback) {
    if (typeof updateHistoryTabs !== "undefined" || window.SearchHistory) {
      callback();
    } else {
      setTimeout(() => ensureSearchHistoryLoaded(callback), 100);
    }
  }

  ensureSearchHistoryLoaded(() => {
    if (typeof updateHistoryTabs !== "undefined") {
      updateHistoryTabs();
    } else if (window.SearchHistory) {
      window.SearchHistory.updateHistoryTabs();
    }
    console.log("SearchHistory updated.");
  });

  const searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", () => {
      Loader.showLoader("loader-overlay");
    });
  }
});
