function showLoader(loaderId) {
    const loader = document.getElementById(loaderId);
    if (loader) loader.style.display = "flex";
  }
  
  function hideLoader(loaderId) {
    const loader = document.getElementById(loaderId);
    if (loader) loader.style.display = "none";
  }
  
  window.Loader = { showLoader, hideLoader };
  