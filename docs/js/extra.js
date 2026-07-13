function addGroupFilter(table) {
  const headers = Array.from(table.querySelectorAll("thead th"));
  const groupIndex = headers.findIndex(function (th) {
    return th.textContent.trim() === "Group";
  });
  if (groupIndex === -1) return;

  const rows = Array.from(table.querySelectorAll("tbody tr"));
  const groups = Array.from(
    new Set(rows.map((row) => row.children[groupIndex].textContent.trim()))
  ).sort();

  const select = document.createElement("select");
  select.className = "ref-group-filter";
  select.multiple = true;
  groups.forEach(function (group) {
    const option = document.createElement("option");
    option.value = group;
    option.textContent = group;
    select.appendChild(option);
  });

  const anchor = table.closest(".md-typeset__scrollwrap") || table;
  anchor.parentElement.insertBefore(select, anchor);

  new SlimSelect({
    select: select,
    settings: {
      placeholderText: "Filter by group…",
      closeOnSelect: false,
    },
    events: {
      afterChange: function (selected) {
        const wanted = selected.map((option) => option.value);
        rows.forEach(function (row) {
          const group = row.children[groupIndex].textContent.trim();
          row.style.display = wanted.length === 0 || wanted.includes(group) ? "" : "none";
        });
      },
    },
  });
}

document$.subscribe(function () {
  const article = document.querySelector("article:has(> #comap-controller-reference)");
  if (!article) return;

  article.querySelectorAll("table").forEach(function (table) {
    new Tablesort(table);
    addGroupFilter(table);
  });
});
