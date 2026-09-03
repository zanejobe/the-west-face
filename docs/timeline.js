(() => {
  const events = [...document.querySelectorAll(".event")];
  const branchInputs = [...document.querySelectorAll('input[name="branch"]')];
  const formationInputs = [...document.querySelectorAll('input[name="formation"]')];
  const countEl = document.getElementById("visible-count");

  const selected = (inputs) =>
    new Set(inputs.filter((i) => i.checked).map((i) => i.value));

  function applyFilters() {
    const branches = selected(branchInputs);
    const formations = selected(formationInputs);
    let visible = 0;

    for (const ev of events) {
      const evBranches = (ev.dataset.branches || "").split(/\s+/).filter(Boolean);
      const evFormations = (ev.dataset.formations || "").split(/\s+/).filter(Boolean);
      const branchOk =
        evBranches.length === 0 || evBranches.some((b) => branches.has(b));
      const formationOk = evFormations.some((f) => formations.has(f));
      const show = branchOk && formationOk;
      ev.classList.toggle("is-hidden", !show);
      if (show) visible += 1;
    }

    if (countEl) countEl.textContent = String(visible);

    // Hide empty eras
    for (const era of document.querySelectorAll(".era")) {
      const any = [...era.querySelectorAll(".event")].some(
        (e) => !e.classList.contains("is-hidden")
      );
      const isPlaceholder = !era.querySelector(".event");
      era.hidden = !(any || isPlaceholder);
    }
  }

  for (const input of [...branchInputs, ...formationInputs]) {
    input.addEventListener("change", applyFilters);
  }

  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) entry.target.classList.add("is-visible");
      }
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );
  events.forEach((el) => io.observe(el));

  applyFilters();
})();
