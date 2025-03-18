// Dark Mode Toggle with Persistence
function initDarkModeToggle(toggleId) {
    const toggle = document.getElementById(toggleId);
    const body = document.body;
    // Check stored preference in localStorage
    if (localStorage.getItem("darkMode") === "true") {
      body.classList.add("dark-mode");
      toggle.checked = true;
    }
    toggle.addEventListener("change", function () {
      if (this.checked) {
        body.classList.add("dark-mode");
        localStorage.setItem("darkMode", "true");
      } else {
        body.classList.remove("dark-mode");
        localStorage.setItem("darkMode", "false");
      }
    });
  }
  
  // Loader Overlay Functions
  function showLoader(loaderId) {
    const loader = document.getElementById(loaderId);
    if (loader) {
      loader.style.display = "flex";
    }
  }
  
  function hideLoader(loaderId) {
    const loader = document.getElementById(loaderId);
    if (loader) {
      loader.style.display = "none";
    }
  }
  
  // Initialize functions on DOMContentLoaded
  document.addEventListener("DOMContentLoaded", function () {
    initDarkModeToggle("darkModeToggle");
  
    // Show loader on form submission
    const searchForm = document.getElementById("searchForm");
    if (searchForm) {
      searchForm.addEventListener("submit", function () {
        showLoader("loader-overlay");
      });
    }
  });
  