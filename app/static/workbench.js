(() => {
  "use strict";
  const sidebar = document.getElementById("workspace-sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  const prompt = document.getElementById("prompt");
  const newChat = document.getElementById("new-chat");
  const isMobile = () => window.matchMedia("(max-width: 767.98px)").matches;

  function setSidebarOpen(open) {
    sidebar.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.textContent = open ? "Close menu" : "Explore";
  }
  toggle.addEventListener("click", () => setSidebarOpen(!sidebar.classList.contains("is-open")));
  sidebar.addEventListener("click", (event) => {
    if (isMobile() && event.target.closest("#conversation-list button")) {
      setSidebarOpen(false);
    }
  });
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      if (!newChat.disabled) newChat.click();
    }
    if (event.key === "Escape" && isMobile() && sidebar.classList.contains("is-open")) {
      setSidebarOpen(false);
      toggle.focus();
    }
  });
  document.querySelectorAll(".starter-card[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      if (prompt.disabled) return;
      prompt.value = button.dataset.prompt;
      prompt.focus();
      prompt.setSelectionRange(prompt.value.length, prompt.value.length);
    });
  });
})();
