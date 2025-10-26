// Darkmode -->
let darkmode = localStorage.getItem("darkmode");
const themeSwitch = document.getElementById("themeSwitch");

const enableDarkmode = () => {
  document.body.classList.add("darkmode");
  localStorage.setItem("darkmode", "active");
};

const disableDarkmode = () => {
  document.body.classList.remove("darkmode");
  localStorage.setItem("darkmode", null);
};

if (darkmode === "active") enableDarkmode();

themeSwitch.addEventListener("click", () => {
  darkmode = localStorage.getItem("darkmode");
  darkmode !== "active" ? enableDarkmode() : disableDarkmode();
});

// <-- Darkmode

document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.sidebar');          // <ul id="sidebar">
  const menuBtn  = document.querySelector('.menu-btn');        // Burger
  const closeBtn = document.querySelector('.close-btn');       // X

  if (!sidebar || !menuBtn || !closeBtn) return;

  // Alle fokussierbaren Elemente innerhalb der Sidebar (für Fokus-Trap)
  const focusables = () => sidebar.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  function openSidebar() {
    sidebar.classList.add('open');
    sidebar.removeAttribute('inert');
    sidebar.setAttribute('aria-hidden', 'false');
    menuBtn.setAttribute('aria-expanded', 'true');

    // Fokus in die Sidebar legen (Close-Button oder erstes fokussierbares Element)
    (closeBtn || focusables()[0] || sidebar).focus();

    // ESC schließt
    document.addEventListener('keydown', onEsc, { once: true });
  }

  function closeSidebar() {
    // 1) Fokus VOR dem Verstecken raus aus der Sidebar holen
    menuBtn.focus();

    // 2) Dann verstecken/„deaktivieren“
    sidebar.classList.remove('open');
    sidebar.setAttribute('inert', '');           // verhindert Fokus
    sidebar.setAttribute('aria-hidden', 'true');
    menuBtn.setAttribute('aria-expanded', 'false');
  }

  function onEsc(e) {
    if (e.key === 'Escape') closeSidebar();
  }

  // Optional: Fokus in der Sidebar einschließen, solange sie offen ist
  sidebar.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const items = [...focusables()];
    if (items.length === 0) return;
    const first = items[0];
    const last  = items[items.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault(); last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault(); first.focus();
    }
  });

  // Clicks
  menuBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); openSidebar(); });
  closeBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); closeSidebar(); });

  // Optional: Klick außerhalb schließt
  document.addEventListener('click', (e) => {
    if (!sidebar.classList.contains('open')) return;
    if (sidebar.contains(e.target) || e.target.closest('.menu-btn')) return;
    closeSidebar();
  });
});
