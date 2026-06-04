/* Shared site behavior: nav scroll state, mobile toggle, reveal-on-scroll */
(function () {
  const nav = document.querySelector(".nav");
  if (nav) {
    const onScroll = () => {
      if (window.scrollY > 4) nav.classList.add("scrolled");
      else nav.classList.remove("scrolled");
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  const toggle = document.querySelector(".nav-mobile-toggle");
  const drawer = document.querySelector(".nav-drawer");
  if (toggle && drawer) {
    toggle.addEventListener("click", () => {
      const open = !drawer.hasAttribute("hidden");
      if (open) drawer.setAttribute("hidden", "");
      else drawer.removeAttribute("hidden");
      toggle.textContent = open ? "≡" : "✕";
    });
  }

  const targets = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }
      },
      { threshold: 0.12 }
    );
    targets.forEach((el) => io.observe(el));
  } else {
    targets.forEach((el) => el.classList.add("in"));
  }

  // Mark current page in nav
  const path = location.pathname.split("/").pop() || "home.html";
  document.querySelectorAll(".nav-links a, .footer-nav a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === path) a.classList.add("active");
  });
})();
