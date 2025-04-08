document.addEventListener("DOMContentLoaded", () => {
    const backToTopButton = document.getElementById("backToTopButton");
  
    window.addEventListener("scroll", () => {
      if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        backToTopButton.style.display = "block";
      } else {
        backToTopButton.style.display = "none";
      }
    });
  
    backToTopButton.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });