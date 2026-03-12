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

// Navbar search

document.addEventListener("DOMContentLoaded", () => {
  const search = document.querySelector("[data-nav-search]");
  if (!search) return;

  const toggle = search.querySelector(".nav-search-toggle");
  const form = search.querySelector("form.nav-search-form");
  const input = form?.querySelector("input[name='q']");

  const open = () => {
    search.classList.add("is-open");
    toggle?.setAttribute("aria-expanded", "true");
    input?.focus();
  };

  const close = () => {
    search.classList.remove("is-open");
    toggle?.setAttribute("aria-expanded", "false");
  };

  toggle?.addEventListener("click", (e) => {
    e.preventDefault();
    search.classList.contains("is-open") ? close() : open();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });

  document.addEventListener("click", (e) => {
    if (search.classList.contains("is-open") && !search.contains(e.target)) close();
  });

  if ((input?.value || "").trim() !== "") open();
});

// Aufgabentypen
(function () {

  const input = document.querySelector('input[name="tasktype"]');
  const container = document.getElementById("tasktype-chips");
  if (!input || !container) return;

  function parseTags(value){
    return value
      .split(",")
      .map(t => t.trim())
      .filter(Boolean);
  }

  function setTags(tags){
    input.value = tags.join(", ");
  }

  function updateChipState(tags){

    const chips = [...container.querySelectorAll(".chip")];

    chips.forEach(chip=>{
      const tag = chip.dataset.tag.toLowerCase();

      if(tags.some(t => t.toLowerCase() === tag)){
        chip.classList.add("active");
      }else{
        chip.classList.remove("active");
      }
    });

    // aktive Chips nach vorne sortieren
    chips
      .sort((a,b)=>{
        const aActive = a.classList.contains("active");
        const bActive = b.classList.contains("active");
        return (bActive - aActive);
      })
      .forEach(chip => container.appendChild(chip));
  }

  container.addEventListener("click", e=>{

    const chip = e.target.closest(".chip");
    if(!chip) return;

    const tag = chip.dataset.tag.trim();
    let tags = parseTags(input.value);

    const index = tags.findIndex(t => t.toLowerCase() === tag.toLowerCase());

    if(index >= 0){
      tags.splice(index,1);
    }else{
      tags.push(tag);
    }

    setTags(tags);
    updateChipState(tags);

  });

  // Initialzustand setzen
  updateChipState(parseTags(input.value));

})();

// Glossary Live-Suche
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.querySelector("[data-glossary-search]");
  const grid = document.querySelector("[data-glossary-grid]");
  const noResults = document.querySelector(".glossary-no-results");

  if (!searchInput || !grid) return;

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    const cards = grid.querySelectorAll(".glossary-card");
    let visible = 0;

    cards.forEach(card => {
      const name = card.dataset.termName || "";
      const match = !query || name.includes(query);
      card.hidden = !match;
      if (match) visible++;
    });

    if (noResults) noResults.hidden = visible > 0;
  });
});