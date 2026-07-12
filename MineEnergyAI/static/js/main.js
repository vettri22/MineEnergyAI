/* =====================================================================
   main.js — MineEnergy AI shared front-end behavior
   Handles: page loader, theme toggle (persisted in-memory), live clock,
   sidebar toggle on mobile, and Bootstrap toast initialization.
   ===================================================================== */

(function () {
  "use strict";

  // In-memory theme state (no localStorage per platform constraints)
  window.__mineEnergyTheme = window.__mineEnergyTheme || "dark";

  /** Hide the full-page loader once the DOM/content is ready. */
  function hidePageLoader() {
    const loader = document.getElementById("pageLoader");
    if (loader) {
      setTimeout(() => loader.classList.add("hide"), 250);
    }
  }

  /** Toggle between dark and light themes by swapping the data-theme attribute. */
  function initThemeToggle() {
    const toggleBtn = document.getElementById("themeToggle");
    const icon = document.getElementById("themeIcon");
    const html = document.documentElement;

    html.setAttribute("data-theme", window.__mineEnergyTheme);
    updateThemeIcon();

    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        window.__mineEnergyTheme = window.__mineEnergyTheme === "dark" ? "light" : "dark";
        html.setAttribute("data-theme", window.__mineEnergyTheme);
        updateThemeIcon();
      });
    }

    function updateThemeIcon() {
      if (!icon) return;
      icon.className = window.__mineEnergyTheme === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
    }
  }

  /** Update the live clock every second. */
  function initLiveClock() {
    const clockEl = document.getElementById("liveClock");
    if (!clockEl) return;
    function tick() {
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString("en-IN", { hour12: false });
    }
    tick();
    setInterval(tick, 1000);
  }

  /** Show/hide sidebar on mobile via the hamburger button. */
  function initSidebarToggle() {
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    if (menuToggle && sidebar) {
      menuToggle.addEventListener("click", () => sidebar.classList.toggle("show"));
      document.addEventListener("click", (e) => {
        if (window.innerWidth <= 991 && sidebar.classList.contains("show") &&
            !sidebar.contains(e.target) && e.target !== menuToggle) {
          sidebar.classList.remove("show");
        }
      });
    }
  }

  /** Initialize all visible Bootstrap toasts. */
  function initToasts() {
    if (typeof bootstrap === "undefined") return;
    document.querySelectorAll(".toast").forEach((toastEl) => {
      try {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
      } catch (err) {
        console.warn("Toast init failed:", err);
      }
    });
  }

  /** Animate KPI numbers counting up from 0 to their target value. */
  function animateCounters() {
    document.querySelectorAll("[data-count-to]").forEach((el) => {
      const target = parseFloat(el.getAttribute("data-count-to"));
      const decimals = el.getAttribute("data-decimals") ? parseInt(el.getAttribute("data-decimals")) : 0;
      const duration = 900;
      const start = performance.now();

      function frame(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        el.textContent = value.toLocaleString("en-IN", {
          minimumFractionDigits: decimals, maximumFractionDigits: decimals,
        });
        if (progress < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    hidePageLoader();
    safeRun(initThemeToggle);
    safeRun(initLiveClock);
    safeRun(initSidebarToggle);
    safeRun(initToasts);
    safeRun(animateCounters);

    // Enable Bootstrap tooltips globally (only if Bootstrap loaded successfully)
    safeRun(function () {
      if (typeof bootstrap === "undefined") return;
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => new bootstrap.Tooltip(el));
    });
  });

  /** Run a function and swallow/report any error so one failure never blocks the rest of the UI init. */
  function safeRun(fn) {
    try { fn(); } catch (err) { console.warn("MineEnergy AI UI init warning:", err); }
  }

  window.addEventListener("load", hidePageLoader);
})();
