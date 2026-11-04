/**
 * Horse.uk s.r.o. — shared UI (mockup)
 * i18n-ready: strings live in window.HorseUK.i18n[locale]
 */
(function () {
  "use strict";

  const locale = document.documentElement.lang || "sk";
  const root = document.documentElement;

  window.HorseUK = window.HorseUK || {};
  window.HorseUK.locale = locale;

  /* ——— Header scroll + mobile nav ——— */
  function initHeader() {
    const header = document.querySelector(".site-header");
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector("#site-nav");
    if (!header) return;

    const onScroll = () => {
      header.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    if (toggle && nav) {
      toggle.addEventListener("click", () => {
        const open = nav.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      nav.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
          nav.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }
  }

  /* ——— Scroll reveal (motion 2) ——— */
  function initReveal() {
    const nodes = document.querySelectorAll(".reveal");
    if (!nodes.length) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      nodes.forEach((n) => n.classList.add("is-visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    nodes.forEach((n) => io.observe(n));
  }

  /* ——— Cookie consent shell ——— */
  function initCookies() {
    const banner = document.getElementById("cookie-banner");
    if (!banner) return;
    const key = "horseuk_cookie_consent";
    let stored = null;
    try {
      stored = localStorage.getItem(key);
    } catch (_) {
      /* ignore */
    }
    if (stored) return;

    requestAnimationFrame(() => banner.classList.add("is-visible"));

    banner.querySelectorAll("[data-cookie]").forEach((btn) => {
      btn.addEventListener("click", () => {
        try {
          localStorage.setItem(key, btn.getAttribute("data-cookie") || "dismissed");
        } catch (_) {
          /* ignore */
        }
        banner.classList.remove("is-visible");
        setTimeout(() => banner.remove(), 500);
      });
    });
  }

  /* ——— Booking form client validation ——— */
  function initBookingForm() {
    const form = document.getElementById("booking-form");
    if (!form) return;

    const success = document.getElementById("booking-success");
    const fields = {
      service: form.querySelector("#service"),
      date: form.querySelector("#date"),
      time: form.querySelector("#time"),
      name: form.querySelector("#name"),
      phone: form.querySelector("#phone"),
      email: form.querySelector("#email"),
    };

    const messages = {
      required: "Toto pole je povinné.",
      email: "Zadajte platný e-mail.",
      phone: "Zadajte platné telefónne číslo.",
      date: "Vyberte dátum v budúcnosti.",
    };

    function setError(input, msg) {
      const group = input.closest(".form-group");
      input.classList.add("is-invalid");
      input.setAttribute("aria-invalid", "true");
      if (group) {
        group.classList.add("has-error");
        const err = group.querySelector(".field-error");
        if (err) err.textContent = msg;
      }
    }

    function clearError(input) {
      const group = input.closest(".form-group");
      input.classList.remove("is-invalid");
      input.removeAttribute("aria-invalid");
      if (group) group.classList.remove("has-error");
    }

    function validEmail(v) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
    }

    function validPhone(v) {
      const digits = v.replace(/[\s\-()]/g, "");
      return /^\+?\d{9,15}$/.test(digits);
    }

    Object.values(fields).forEach((input) => {
      if (!input) return;
      input.addEventListener("input", () => clearError(input));
      input.addEventListener("change", () => clearError(input));
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      let ok = true;

      Object.values(fields).forEach((input) => {
        if (!input) return;
        clearError(input);
        if (!String(input.value || "").trim()) {
          setError(input, messages.required);
          ok = false;
        }
      });

      if (fields.email && fields.email.value.trim() && !validEmail(fields.email.value.trim())) {
        setError(fields.email, messages.email);
        ok = false;
      }
      if (fields.phone && fields.phone.value.trim() && !validPhone(fields.phone.value.trim())) {
        setError(fields.phone, messages.phone);
        ok = false;
      }
      if (fields.date && fields.date.value) {
        const picked = new Date(fields.date.value + "T00:00:00");
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (picked < today) {
          setError(fields.date, messages.date);
          ok = false;
        }
      }

      if (!ok) {
        const first = form.querySelector(".is-invalid");
        if (first) first.focus();
        return;
      }

      form.classList.add("is-hidden");
      if (success) {
        success.classList.add("is-visible");
        success.focus();
      }
    });

    const resetBtn = document.getElementById("booking-reset");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        form.reset();
        form.classList.remove("is-hidden");
        if (success) success.classList.remove("is-visible");
      });
    }
  }

  /* ——— Admin login shell (UI only) ——— */
  function initAdminLogin() {
    const form = document.getElementById("admin-login-form");
    if (!form) return;
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const email = form.querySelector("#admin-email");
      const pass = form.querySelector("#admin-password");
      let ok = true;
      [email, pass].forEach((el) => {
        if (!el) return;
        const group = el.closest(".form-group");
        if (!el.value.trim()) {
          el.classList.add("is-invalid");
          if (group) group.classList.add("has-error");
          ok = false;
        } else {
          el.classList.remove("is-invalid");
          if (group) group.classList.remove("has-error");
        }
      });
      if (!ok) return;
      window.location.href = form.getAttribute("data-dashboard") || "./dashboard.html";
    });
  }

  /**
   * GitHub project Pages live under /<repo>/ (e.g. /horse-uk.sk/).
   * Without a trailing slash, relative asset URLs resolve one level too high.
   * Keep page-relative hrefs (no <base> tag — that breaks ../ links).
   */
  function ensureProjectPagesTrailingSlash() {
    if (!/\.github\.io$/i.test(location.hostname)) return;
    const path = location.pathname;
    const last = path.split("/").pop() || "";
    const looksLikeFile = /\.[a-z0-9]+$/i.test(last);
    if (!path.endsWith("/") && !looksLikeFile) {
      location.replace(path + "/" + location.search + location.hash);
    }
  }

  ensureProjectPagesTrailingSlash();

  document.addEventListener("DOMContentLoaded", () => {
    root.setAttribute("data-locale", locale);
    root.dataset.pagesBase = /\.github\.io$/i.test(location.hostname)
      ? "/" + (location.pathname.split("/").filter(Boolean)[0] || "") + "/"
      : "/";
    initHeader();
    initReveal();
    initCookies();
    initBookingForm();
    initAdminLogin();
  });
})();
