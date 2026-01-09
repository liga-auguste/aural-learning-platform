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

if (themeSwitch) {
  themeSwitch.addEventListener("click", () => {
    darkmode = localStorage.getItem("darkmode");
    darkmode !== "active" ? enableDarkmode() : disableDarkmode();
  });
}
// <-- Darkmode

// Sidebar
document.addEventListener('DOMContentLoaded', () => {
  const sidebar  = document.querySelector('.sidebar');
  const menuBtn  = document.querySelector('.menu-btn');
  const closeBtn = document.querySelector('.close-btn');

  if (!sidebar || !menuBtn || !closeBtn) return;

  const focusables = () => sidebar.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  function openSidebar() {
    sidebar.classList.add('open');

    document.body.classList.add('nav-open'); 

    sidebar.removeAttribute('inert');
    sidebar.setAttribute('aria-hidden', 'false');
    menuBtn.setAttribute('aria-expanded', 'true');
    (closeBtn || focusables()[0] || sidebar).focus();
    document.addEventListener('keydown', onEsc, { once: true });
  }

  function closeSidebar() {
    menuBtn.focus();
    sidebar.classList.remove('open');

    document.body.classList.remove('nav-open');

    sidebar.setAttribute('inert', '');
    sidebar.setAttribute('aria-hidden', 'true');
    menuBtn.setAttribute('aria-expanded', 'false');
  }

  function onEsc(e) {
    if (e.key === 'Escape') closeSidebar();
  }

  sidebar.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const items = [...focusables()];
    if (!items.length) return;
    const first = items[0];
    const last  = items[items.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault(); last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault(); first.focus();
    }
  });

  menuBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    openSidebar();
  });

  closeBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    closeSidebar();
  });

  document.addEventListener('click', (e) => {
    if (!sidebar.classList.contains('open')) return;
    if (sidebar.contains(e.target) || e.target.closest('.menu-btn')) return;
    closeSidebar();
  });
});

// <-- Sidebar

document.addEventListener("DOMContentLoaded", () => {
  const rows = Array.from(document.querySelectorAll(".audio-row"));
  const btnRow = document.querySelector(".audio-add-row");
  const btn = document.getElementById("add-audio-btn");

  // Wenn auf der Seite kein Audio-Block existiert → nichts tun
  if (rows.length === 0 || !btnRow || !btn) return;

  function hiddenRows() {
    return rows.filter(r => r.classList.contains("is-hidden"));
  }

  function updateButton() {
    if (hiddenRows().length === 0) {
      btnRow.style.display = "none";
    } else {
      btnRow.style.display = ""; // falls wieder sichtbar werden soll
    }
  }

  btn.addEventListener("click", () => {
    const next = hiddenRows()[0];
    if (next) next.classList.remove("is-hidden");
    updateButton();
  });

  updateButton();
});
