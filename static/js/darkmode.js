function initDarkModeToggle(toggleId) {
    const toggle = document.getElementById(toggleId);
    const body = document.body;
    if (localStorage.getItem("darkMode") === "true") {
      body.classList.add("dark-mode");
      toggle.checked = true;
    }
    toggle.addEventListener("change", () => {
      if (toggle.checked) {
        body.classList.add("dark-mode");
        localStorage.setItem("darkMode", "true");
      } else {
        body.classList.remove("dark-mode");
        localStorage.setItem("darkMode", "false");
      }
    });
  }
  window.initDarkModeToggle = initDarkModeToggle;
  