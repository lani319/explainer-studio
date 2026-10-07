// Built-in scene types. Each one reads only its `screen` block (text, items) and the line cues,
// so the same layout works in every language. See references/scene-types.md for the fields.
(function () {
  "use strict";
  const E = window.Explainer;
  const { el, appear, prog, lerp, ease, rich } = E.util;
  const list = (v) => (Array.isArray(v) ? v : v == null ? [] : [v]);
  const text = (v) => (v && typeof v === "object" ? v.text ?? v.title ?? "" : v);

  // Is item k "the one being talked about"? From its cue until the next item's cue.
  function activeWindow(ctx, items, k) {
    const a = ctx.at(items[k], k);
    const b = k + 1 < items.length ? ctx.at(items[k + 1], k + 1) : ctx.dur;
    return [a, b];
  }

  // ---------- cover: kicker, title, sub ----------
  E.scene("cover", (root, ctx) => {
    const s = ctx.screen;
    const wrap = el("div", "cover", root);
    const orbit = el("div", "orbit", wrap);
    const rings = [0, 1, 2].map((i) => el("div", `ring r${i}`, orbit));
    const sparks = Array.from({ length: 14 }, (_, i) => el("div", "spark", orbit, null));
    const col = el("div", "cover-text", wrap);
    let logo = null;
    if (ctx.meta.logo) {
      logo = el("img", "cover-logo", col);
      logo.src = ctx.meta.logo;
      logo.alt = "";
    }
    const kicker = el("div", "kicker", col, rich(s.kicker));
    const title = el("div", "cover-title", col);
    const chars = [...String(s.title ?? "")].map((c) => el("span", "", title, c === " " ? "&nbsp;" : rich(c)));
    const rule = el("div", "rule", col);
    const subt = el("div", "cover-sub", col, rich(s.sub));
    const badge = s.badge ? el("div", "cover-badge", col, rich(s.badge)) : null;
    // Long titles (some languages run long) shrink to fit the text column instead of running into the art.
    let fitted = false;
    const fit = () => {
      if (fitted || !title.scrollWidth) return;
      fitted = true;
      const max = col.clientWidth || 980;
      if (title.scrollWidth > max) title.style.fontSize = `${Math.floor(128 * (max / title.scrollWidth))}px`;
    };
    return (t) => {
      fit();
      if (logo) appear(logo, t, 0.0, { dy: -16 });
      appear(kicker, t, 0.1, { dx: -30, dy: 0 });
      chars.forEach((c, i) => {
        const p = prog(t, 0.25 + i * 0.045, 0.6);
        c.style.opacity = p;
        c.style.transform = `translateY(${(1 - p) * 50}px)`;
      });
      rule.style.width = `${lerp(0, 280, prog(t, 0.7, 0.9, ease))}px`;
      appear(subt, t, 1.0);
      if (badge) appear(badge, t, 1.3);
      rings.forEach((r, i) => {
        const p = prog(t, 0.1 + i * 0.15, 1.2);
        r.style.opacity = (0.9 - i * 0.2) * p;
        r.style.transform = `rotate(${(t * (8 + i * 5) * (i % 2 ? -1 : 1)).toFixed(2)}deg) scale(${lerp(0.7, 1, p)})`;
      });
      sparks.forEach((d, i) => {
        const a = (i / sparks.length) * Math.PI * 2 + t * 0.15 * (i % 3 ? 1 : -1);
        const r = 170 + (i % 4) * 55;
        d.style.transform = `translate(${(Math.cos(a) * r).toFixed(1)}px, ${(Math.sin(a) * r).toFixed(1)}px)`;
        d.style.opacity = (prog(t, 0.6 + i * 0.05, 0.6) * (0.4 + 0.6 * Math.abs(Math.sin(t + i)))).toFixed(3);
      });
    };
  });

  // ---------- cards: title, cards[{title, sub, tag, at}], columns ----------
  E.scene("cards", (root, ctx) => {
    const s = ctx.screen;
    const items = list(s.cards);
    const head = s.title ? el("div", "scene-title", root, rich(s.title)) : null;
    const cols = s.columns || (items.length <= 4 ? items.length : 3);
    const grid = el("div", "cards", root);
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    const nodes = items.map((c) => {
      const n = el("div", "card", grid);
      if (c.tag) el("div", "card-tag", n, rich(c.tag));
      el("div", "card-title", n, rich(text(c)));
      if (c.sub) el("div", "card-sub", n, rich(c.sub));
      return n;
    });
    return (t) => {
      if (head) appear(head, t, 0.05, { dy: -16 });
      nodes.forEach((n, k) => {
        appear(n, t, ctx.at(items[k], k, 0.3), { dy: 30, scale: 0.96 });
        const [a, b] = activeWindow(ctx, items, k);
        n.classList.toggle("on", items[k].at != null && t >= a && t < b);
      });
    };
  });

  // ---------- quote: kicker, title, items[{label, text, at}], points[{text, at}], note ----------
  E.scene("quote", (root, ctx) => {
    const s = ctx.screen;
    const items = list(s.items);
    const points = list(s.points);
    const wrap = el("div", "quote", root);
    const side = el("div", "quote-side", wrap);
    const kicker = el("div", "quote-kicker", side, rich(s.kicker));
    const stitle = s.title ? el("div", "quote-title", side, rich(s.title)) : null;
    const main = el("div", "quote-main", wrap);
    const rows = items.map((it) => {
      const r = el("div", "quote-row", main);
      if (it.label) el("div", "quote-label", r, rich(it.label));
      el("div", "quote-text", r, rich(text(it)));
      return r;
    });
    const chips = el("div", "chips", main);
    const pts = points.map((p) => el("div", "chip", chips, rich(text(p))));
    const note = s.note ? el("div", "quote-note", wrap, rich(s.note)) : null;
    const defaultAt = (k) => ({ at: k });
    const itemsAt = items.map((it, k) => (typeof it.at === "number" ? it : { ...it, ...defaultAt(k) }));
    return (t) => {
      appear(kicker, t, 0.05, { dx: -30, dy: 0 });
      if (stitle) appear(stitle, t, 0.25, { dx: -30, dy: 0 });
      rows.forEach((r, k) => {
        appear(r, t, ctx.at(itemsAt[k], k), { dy: 26 });
        const [a, b] = activeWindow(ctx, itemsAt, k);
        r.classList.toggle("on", items.length > 1 && t >= a && t < b);
      });
      // points default to the last line (a summary), staggered
      pts.forEach((p, k) => {
        const at = points[k] && typeof points[k].at === "number" ? ctx.cue(points[k].at) : ctx.cue(ctx.lines - 1) + k * 0.35;
        appear(p, t, at, { dy: 16, scale: 0.9 });
      });
      if (note) appear(note, t, 0.6, { dy: 0 });
    };
  });

  // ---------- flow: title, steps[{title, sub, at}], note ----------
  E.scene("flow", (root, ctx) => {
    const s = ctx.screen;
    const steps = list(s.steps);
    const head = s.title ? el("div", "scene-title", root, rich(s.title)) : null;
    const row = el("div", "flow", root);
    const nodes = [];
    const arrows = [];
    steps.forEach((st, k) => {
      if (k) {
        const a = el("div", "flow-arrow", row);
        el("div", "flow-line", a);
        el("div", "flow-head", a);
        arrows.push(a);
      }
      const n = el("div", "flow-step", row);
      el("div", "flow-num", n, String(k + 1));
      el("div", "flow-title", n, rich(text(st)));
      if (st.sub) el("div", "flow-sub", n, rich(st.sub));
      nodes.push(n);
    });
    const stepsAt = steps.map((st, k) => (typeof st.at === "number" ? st : { ...st, at: Math.min(k, ctx.lines - 1) }));
    const note = s.note ? el("div", "flow-note", root, rich(s.note)) : null;
    return (t) => {
      if (head) appear(head, t, 0.05, { dy: -16 });
      nodes.forEach((n, k) => {
        const a = ctx.at(stepsAt[k], k);
        appear(n, t, a, { dy: 30 });
        const [x, y] = activeWindow(ctx, stepsAt, k);
        n.classList.toggle("on", t >= x && t < y);
        if (k) {
          const p = prog(t, a - 0.5, 0.5);
          arrows[k - 1].style.opacity = p > 0 ? 1 : 0;
          arrows[k - 1].querySelector(".flow-line").style.transform = `scaleX(${p.toFixed(3)})`;
          arrows[k - 1].querySelector(".flow-head").style.opacity = p > 0.95 ? 1 : 0;
        }
      });
      if (note) appear(note, t, ctx.cue(ctx.lines - 1));
    };
  });

  // ---------- list: title, items[{text, at}] ----------
  E.scene("list", (root, ctx) => {
    const s = ctx.screen;
    const items = list(s.items).map((it, k) => (typeof it === "object" ? it : { text: it }));
    const head = s.title ? el("div", "scene-title", root, rich(s.title)) : null;
    const box = el("div", "list", root);
    const rows = items.map((it, k) => {
      const r = el("div", "list-row", box);
      el("div", "list-dot", r, String(k + 1));
      el("div", "list-text", r, rich(it.text));
      return r;
    });
    return (t) => {
      if (head) appear(head, t, 0.05, { dy: -16 });
      rows.forEach((r, k) => {
        appear(r, t, ctx.at(items[k], k, 0.35), { dx: -40, dy: 0 });
        const [a, b] = activeWindow(ctx, items, k);
        r.classList.toggle("on", typeof items[k].at === "number" && t >= a && t < b);
      });
    };
  });

  // ---------- closing: title, items (recap), next ----------
  E.scene("closing", (root, ctx) => {
    const s = ctx.screen;
    const items = list(s.items);
    const wrap = el("div", "closing", root);
    const left = el("div", "closing-left", wrap);
    const head = el("div", "closing-title", left, rich(s.title || ctx.ui.recap || ""));
    const rows = items.map((it) => {
      const r = el("div", "closing-row", left);
      el("div", "tick", r, "✓");
      el("div", "", r, rich(text(it)));
      return r;
    });
    let next = null;
    if (s.next) {
      next = el("div", "closing-next", wrap);
      el("div", "closing-next-k", next, rich(s.next_kicker || ctx.ui.next || ""));
      el("div", "closing-next-t", next, rich(s.next));
    }
    const src = list(ctx.meta.sources);
    const foot = src.length ? el("div", "sources", root, `<b>${rich(ctx.ui.sources || "Sources")}</b> · ${src.map(rich).join(" · ")}`) : null;
    return (t) => {
      appear(head, t, 0.05, { dy: 16 });
      rows.forEach((r, k) => appear(r, t, ctx.at(items[k], k, 0.4) + 0.2, { dx: -40, dy: 0 }));
      if (next) appear(next, t, ctx.cue(Math.max(0, ctx.lines - 1)), { dx: 80, dy: 0 });
      if (foot) appear(foot, t, 0.8, { dy: 0 });
    };
  });
})();
