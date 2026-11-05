function k(a, l = 14) {
  if (a.length * l >= 360) throw new RangeError("Labels do not fit this lane");
  const e = a.map((r, c) => ({ index: c, angle: (r % 360 + 360) % 360 })).sort((r, c) => r.angle - c.angle);
  if (e.length < 2) return e;
  for (let r = 0; r < 400; r++) {
    let c = 0;
    for (let s = 0; s < e.length; s++) {
      const g = e[s], y = e[(s + 1) % e.length], h = y.angle + (s === e.length - 1 ? 360 : 0) - g.angle;
      if (h < l) {
        const x = (l - h) / 2;
        g.angle -= x, y.angle += x, c = Math.max(c, x);
      }
    }
    if (c < 1e-7) break;
  }
  return e;
}
const i = (a) => document.querySelector(a), v = (a) => Array.from(document.querySelectorAll(a)), $ = "http://www.w3.org/2000/svg";
function u(a, l, e) {
  const r = document.createElementNS($, a);
  for (const [c, s] of Object.entries(l)) r.setAttribute(c, String(s));
  return e && (r.textContent = e), r;
}
function p(a, l, e) {
  const r = (180 - a + e) * Math.PI / 180;
  return { x: 400 + l * Math.cos(r), y: 400 - l * Math.sin(r) };
}
function b(a, l, e) {
  return u("line", { x1: a.x, y1: a.y, x2: l.x, y2: l.y, class: e });
}
const S = ["☉", "☽", "☿", "♀", "♂", "♃", "♄", "♅", "♆", "♇", "☊"], _ = ["♈︎", "♉︎", "♊︎", "♋︎", "♌︎", "♍︎", "♎︎", "♏︎", "♐︎", "♑︎", "♒︎", "♓︎"], C = i("#chart-data");
if (C) {
  let a = function(t) {
    const n = e.rows.find((o) => o.key === t);
    if (!n) return;
    v("[data-planet]").forEach((o) => {
      const f = o.dataset.planet === t;
      o.classList.toggle("selected", f), o.setAttribute("aria-pressed", String(f));
    }), v("[data-row]").forEach((o) => o.classList.toggle("selected", o.dataset.row === t)), v(".aspect").forEach((o) => {
      const f = o.dataset.a === t || o.dataset.b === t;
      o.classList.toggle("highlighted", f), o.classList.toggle("dimmed", !f);
    }), i("#selected-name").textContent = n.name, i("#selected-meta").textContent = `${n.sign_name} · ${n.position}${n.house ? " · " + e.labels.house + " " + n.house : ""}${n.retrograde ? " ℞" : ""}`;
    const m = i("#selected-text");
    m.replaceChildren();
    for (const o of [...n.text, ...n.house_text ? [n.house_text] : []]) {
      const f = document.createElement("p");
      f.textContent = o, m.append(f);
    }
    const d = i("#selected-aspects");
    d.replaceChildren();
    for (const o of e.aspects.filter((f) => f.a === t || f.b === t)) {
      const f = document.createElement("p");
      f.className = "connection", f.textContent = `${o.name} · ${o.a === t ? o.b_name : o.a_name} · ${o.orb.toFixed(2)}°`, d.append(f);
    }
  }, l = function(t) {
    h = Math.max(1, Math.min(3, t)), r.style.width = `${h * 100}%`, r.style.maxWidth = "none";
  };
  const e = JSON.parse(C.textContent || "{}"), r = i("#chart-svg"), c = e.result.angles.asc ?? 0, s = u("g", { class: "chart-layers" });
  r.append(s), [365, 322, 280, 242, 205].forEach((t, n) => s.append(u("circle", { cx: 400, cy: 400, r: t, class: n === 0 ? "outer-ring" : "ring" })));
  for (let t = 0; t < 360; t++)
    s.append(b(p(t, 322, c), p(t, t % 30 === 0 ? 348 : t % 5 === 0 ? 333 : 327, c), "tick"));
  for (let t = 0; t < 12; t++) {
    s.append(b(p(t * 30, 280, c), p(t * 30, 365, c), "zodiac-divider"));
    const n = p(t * 30 + 15, 345, c), m = u("text", { x: n.x, y: n.y, class: "zodiac-symbol" }, _[t]);
    m.append(u("title", {}, e.signs[t])), s.append(m);
  }
  if (e.result.cusps.forEach((t, n) => {
    s.append(b(p(t, 205, c), p(t, 280, c), n % 3 === 0 ? "house-line angular" : "house-line"));
    const m = e.result.cusps[(n + 1) % 12], d = p(t + (m - t + 360) % 360 / 2, 224, c);
    s.append(u("text", { x: d.x, y: d.y, class: "house-number" }, String(n + 1)));
  }), e.result.angles.asc !== void 0) {
    const t = p(c, 383, c);
    s.append(u("text", { x: t.x, y: t.y, class: "angle-label" }, "ASC"));
    const n = p(e.result.angles.mc, 383, c);
    s.append(u("text", { x: n.x, y: n.y, class: "angle-label" }, "MC"));
  }
  const g = u("g", { class: "aspects" });
  s.append(g);
  for (const t of e.aspects) {
    const n = e.result.planets.find((o) => o.key === t.a), m = e.result.planets.find((o) => o.key === t.b), d = b(p(n.longitude, 203, c), p(m.longitude, 203, c), `aspect ${t.type}`);
    d.dataset.a = t.a, d.dataset.b = t.b, g.append(d);
  }
  const y = k(e.result.planets.map((t) => t.longitude)).map(({ index: t, angle: n }) => ({ p: e.result.planets[t], i: t, angle: n }));
  for (const t of y) {
    const n = t.p;
    s.append(b(p(n.longitude, 242, c), p(t.angle, 261, c), "leader"));
    const m = p(n.longitude, 242, c);
    s.append(u("circle", { cx: m.x, cy: m.y, r: 3, class: "position-dot" }));
    const d = p(t.angle, 261, c), o = u("g", { class: "planet-symbol", tabindex: 0, role: "button", "aria-label": `${e.rows[t.i].name}, ${e.rows[t.i].sign_name}, ${e.rows[t.i].position}` });
    o.dataset.planet = n.key, o.append(u("circle", { cx: d.x, cy: d.y, r: 17, class: "planet-hit" })), o.append(u("text", { x: d.x, y: d.y }, S[t.i])), n.retrograde && o.append(u("text", { x: d.x + 12, y: d.y + 12, class: "retrograde" }, "℞")), s.append(o);
  }
  s.append(u("circle", { cx: 400, cy: 400, r: 48, class: "centre-ring" })), s.append(u("text", { x: 400, y: 402, class: "centre-mark" }, "✧")), v("[data-planet]").forEach((t) => {
    t.addEventListener("click", () => a(t.dataset.planet)), t.tagName.toLowerCase() === "g" && t.addEventListener("keydown", (n) => {
      const m = n;
      ["Enter", " "].includes(m.key) && (m.preventDefault(), a(t.dataset.planet));
    });
  }), a("sun");
  let h = 1;
  const x = i("#map-viewport");
  i("#zoom-in").addEventListener("click", () => l(h + 0.25)), i("#zoom-out").addEventListener("click", () => l(h - 0.25)), i("#reset").addEventListener("click", () => {
    l(1), x.scrollTo(0, 0);
  });
}
const E = i("#motion"), L = matchMedia("(prefers-reduced-motion: reduce)");
function w() {
  document.body.classList.toggle("no-motion", L.matches || localStorage.getItem("motion") === "off"), E && (E.checked = !document.body.classList.contains("no-motion"));
}
w();
L.addEventListener("change", w);
E?.addEventListener("change", () => {
  localStorage.setItem("motion", E.checked ? "on" : "off"), w();
});
document.addEventListener("visibilitychange", () => document.body.classList.toggle("paused", document.hidden));
function z() {
  return i("input[name=csrfmiddlewaretoken]")?.value || "";
}
v("[data-link]").forEach((a) => a.addEventListener("click", async () => {
  a.disabled = !0;
  try {
    const l = await fetch(a.dataset.link, { method: "POST", headers: { "X-CSRFToken": z() } });
    if (!l.ok) throw new Error(String(l.status));
    const { url: e } = await l.json(), r = i("#personal-url");
    if (r && (r.textContent = e), a.dataset.mode === "open")
      location.assign(e);
    else
      try {
        await navigator.clipboard.writeText(e), i("#toast").textContent = { en: "Copied", uk: "Скопійовано", ru: "Скопировано" }[document.documentElement.lang] || "Copied", setTimeout(() => i("#toast").textContent = "", 2500);
      } catch {
        r || window.prompt("URL", e);
      }
  } catch {
    i("#toast").textContent = "Error";
  } finally {
    a.disabled = !1;
  }
}));
i("#find-place")?.addEventListener("click", async () => {
  const a = i("#place-search").value, l = i("#country-search").value, e = i("#place-results");
  if (e.replaceChildren(), a.length < 2) return;
  const r = await fetch(`/admin/places/?q=${encodeURIComponent(a)}&country=${encodeURIComponent(l)}`);
  if (!r.ok) return;
  const { results: c } = await r.json();
  for (const s of c) {
    const g = document.createElement("button");
    g.type = "button", g.textContent = s.label, g.addEventListener("click", () => {
      for (const [y, h] of Object.entries({ city_id: s.id, place: s.label, latitude: s.latitude, longitude: s.longitude, timezone: s.timezone })) {
        const x = i(`#id_${y}`);
        x && (x.value = String(h));
      }
      e.replaceChildren();
    }), e.append(g);
  }
});
["place", "latitude", "longitude", "timezone"].forEach((a) => i(`#id_${a}`)?.addEventListener("input", () => {
  const l = i("#id_city_id");
  l && (l.value = "");
}));
i("#editor-form")?.addEventListener("submit", () => {
  const a = i("#editor-form button[type=submit]");
  a && (a.disabled = !0, a.textContent = "…");
});
