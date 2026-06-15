/**
 * CyCoTech Blog — interacciones de UI.
 * Vanilla JS, sin eval (compatible con CSP estricta: script-src 'self').
 */
(function () {
  "use strict";

  // ---- Menú móvil -----------------------------------------------------------
  function initMenu() {
    var btn = document.querySelector("[data-menu-toggle]");
    var menu = document.querySelector("[data-menu]");
    if (!btn || !menu) return;
    btn.addEventListener("click", function () {
      var willOpen = menu.classList.contains("hidden");
      menu.classList.toggle("hidden", !willOpen);
      btn.querySelectorAll("[data-icon-open]").forEach(function (e) { e.classList.toggle("hidden", willOpen); });
      btn.querySelectorAll("[data-icon-close]").forEach(function (e) { e.classList.toggle("hidden", !willOpen); });
    });
  }

  // ---- Toggle de tema -------------------------------------------------------
  function initTheme() {
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof window.toggleTheme === "function") window.toggleTheme();
      });
    });
  }

  // ---- Dropdowns (selector de idioma, etc.) --------------------------------
  function initDropdowns() {
    document.querySelectorAll("[data-dropdown]").forEach(function (dd) {
      var toggle = dd.querySelector("[data-dropdown-toggle]");
      var panel = dd.querySelector("[data-dropdown-panel]");
      if (!toggle || !panel) return;

      function close() {
        panel.classList.add("hidden");
        dd.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
      function open() {
        panel.classList.remove("hidden");
        dd.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
      }
      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        if (panel.classList.contains("hidden")) open(); else close();
      });
      document.addEventListener("click", function (e) {
        if (!dd.contains(e.target)) close();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") close();
      });
    });
  }

  // ---- Copiar código --------------------------------------------------------
  function initCopy() {
    document.querySelectorAll("[data-copy]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var block = btn.closest("[data-code-block]");
        var code = block && block.querySelector("[data-code]");
        if (!code || !navigator.clipboard) return;
        navigator.clipboard.writeText(code.innerText).then(function () {
          var idle = btn.querySelector("[data-copy-idle]");
          var done = btn.querySelector("[data-copy-done]");
          if (idle) idle.classList.add("hidden");
          if (done) done.classList.remove("hidden");
          setTimeout(function () {
            if (idle) idle.classList.remove("hidden");
            if (done) done.classList.add("hidden");
          }, 1600);
        });
      });
    });
  }

  // ---- Barra de progreso de lectura ----------------------------------------
  function initProgress() {
    var bar = document.querySelector("[data-progress-bar]");
    if (!bar) return;
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    }
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  function init() {
    initMenu();
    initTheme();
    initDropdowns();
    initCopy();
    initProgress();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
