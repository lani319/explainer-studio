// explainer-studio player — draws a timeline on a 1920×1080 stage.
// Everything on screen is a pure function of the time t, so the renderer can jump to any frame.
// In a browser it plays with the narration track; with ?render=1 the renderer drives it via window.__seek(t).
(function () {
  "use strict";

  const W = 1920;
  const H = 1080;
  const FADE_IN = 0.45;
  const FADE_OUT = 0.35;

  // ---------- small helpers shared with scene types ----------
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  // progress 0→1 of an animation that starts at `a` and lasts `d` seconds
  const prog = (t, a, d, fn = easeOut) => fn(clamp((t - a) / d, 0, 1));
  const lerp = (a, b, p) => a + (b - a) * p;

  function el(tag, cls, parent, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    if (parent) parent.appendChild(n);
    return n;
  }

  // Show `node` from time `at`: fade + slide. Before `at` it is hidden.
  function appear(node, t, at, o = {}) {
    const p = prog(t, at, o.dur ?? 0.55);
    node.style.opacity = p.toFixed(3);
    const dx = (o.dx ?? 0) * (1 - p);
    const dy = (o.dy ?? 24) * (1 - p);
    const s = lerp(o.scale ?? 1, 1, p);
    node.style.transform = `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px) scale(${s.toFixed(4)})`;
    return p;
  }

  // Text from a script: escape it, then allow **emphasis** and line breaks (\n).
  function rich(s) {
    const esc = String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return esc.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>");
  }

  const Explainer = (window.Explainer = {
    types: {},
    scene(name, fn) {
      this.types[name] = fn;
    },
    util: { clamp, ease, easeOut, prog, lerp, el, appear, rich, W, H },
  });

  // ---------- context handed to every scene ----------
  function makeCtx(sec, meta) {
    const lines = sec.lines;
    return {
      screen: sec.screen,
      section: sec,
      meta,
      ui: meta.ui || {},
      dur: sec.dur,
      lines: lines.length,
      // start of narration line i, relative to the section (clamped to the last line)
      cue(i) {
        if (!lines.length) return 0.3;
        const k = clamp(Math.round(i), 0, lines.length - 1);
        return lines[k].t0 - sec.t0;
      },
      cueEnd(i) {
        if (!lines.length) return sec.dur;
        const k = clamp(Math.round(i), 0, lines.length - 1);
        return lines[k].t1 - sec.t0;
      },
      // when should item k of a list appear? explicit `at` (line index) wins, else stagger from line 0
      at(item, k, step = 0.4) {
        if (item && typeof item === "object" && typeof item.at === "number") return this.cue(item.at);
        return this.cue(0) + k * step;
      },
    };
  }

  function applyTheme(root, meta) {
    const th = meta.theme || {};
    const map = { accent: "--accent", accent2: "--accent2", bg: "--bg", bg2: "--bg2", fg: "--fg", muted: "--muted" };
    for (const k in map) if (th[k]) root.style.setProperty(map[k], th[k]);
    root.style.setProperty("--font", meta.font || "sans-serif");
    root.style.setProperty("--word-break", meta.word_break || "normal");
    document.documentElement.lang = meta.html_lang || meta.lang || "en";
  }

  function start(root, TL) {
    const render = /[?&]render=1/.test(location.search);
    document.body.classList.toggle("render", render);
    applyTheme(document.documentElement, TL.meta);

    const viewport = el("div", "viewport", root);
    const stage = el("div", "stage", viewport);
    const bg = el("div", "bg", stage);
    const dots = el("div", "dots", bg);
    const layer = el("div", "scenes", stage);
    const tag = el("div", "chapter", stage);
    const tagText = el("span", "", tag);
    el("div", "brand", stage, rich(TL.meta.title));
    const sub = el("div", "subtitle", stage);
    const bar = el("div", "progress", stage);

    const scenes = TL.sections.map((sec) => {
      const box = el("div", "scene", layer);
      box.dataset.id = sec.id;
      const make = Explainer.types[sec.screen.type];
      let update;
      if (!make) {
        el("div", "missing", box, `Unknown screen type: <b>${rich(sec.screen.type)}</b>`);
        update = () => {};
      } else {
        update = make(box, makeCtx(sec, TL.meta)) || (() => {});
      }
      return { sec, box, update };
    });
    const lines = TL.sections.flatMap((s) => s.lines);
    let shownLine = -1;
    let shownSec = -1;

    function seek(t) {
      t = clamp(t, 0, TL.duration);
      dots.style.transform = `translate(${((t * 9) % 64).toFixed(1)}px, ${((t * 4) % 64).toFixed(1)}px)`;
      let cur = 0;
      scenes.forEach((s, i) => {
        const local = t - s.sec.t0;
        const last = i === scenes.length - 1;
        const visible = local >= 0 && (local < s.sec.dur || last);
        if (!visible) {
          s.box.style.display = "none";
          return;
        }
        cur = i;
        const a = Math.min(i === 0 ? 1 : prog(local, 0, FADE_IN, ease), last ? 1 : 1 - prog(local, s.sec.dur - FADE_OUT, FADE_OUT, ease));
        s.box.style.display = "block";
        s.box.style.opacity = a.toFixed(3);
        s.update(local);
      });
      if (cur !== shownSec) {
        shownSec = cur;
        tagText.innerHTML = rich(scenes[cur].sec.title);
        tag.classList.toggle("hidden", scenes[cur].sec.screen.type === "cover");
      }
      let li = -1;
      for (let i = 0; i < lines.length; i++) {
        if (t >= lines[i].t0 && t < lines[i].t1 + 0.25) {
          li = i;
          break;
        }
      }
      if (li !== shownLine) {
        shownLine = li;
        sub.innerHTML = li >= 0 ? `<span>${lines[li].html}</span>` : "";
      }
      sub.style.opacity = li >= 0 ? 1 : 0;
      bar.style.width = `${((t / TL.duration) * 100).toFixed(3)}%`;
    }

    window.__seek = seek;
    seek(0);
    document.fonts.ready.then(() => {
      window.__ready = true;
    });
    if (render) return;

    // ---------- interactive playback ----------
    const fit = () => {
      const s = Math.min(window.innerWidth / W, (window.innerHeight - 56) / H);
      stage.style.transform = `scale(${s})`;
      viewport.style.width = `${W * s}px`;
      viewport.style.height = `${H * s}px`;
    };
    window.addEventListener("resize", fit);
    fit();

    const audio = TL.audio ? new Audio(TL.audio) : null;
    const controls = el("div", "controls", root);
    const play = el("button", "", controls, "▶");
    const range = el("input", "", controls);
    range.type = "range";
    range.min = 0;
    range.max = TL.duration;
    range.step = 0.01;
    range.value = 0;
    const time = el("span", "time", controls);
    const pick = el("select", "", controls);
    TL.sections.forEach((s, i) => el("option", "", pick, rich(s.title)).setAttribute("value", i));

    let playing = false;
    let clock = 0;
    let lastNow = 0;
    const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
    const now = () => (audio ? audio.currentTime : clock);
    const jump = (t) => {
      clock = t;
      if (audio) audio.currentTime = t;
      seek(t);
    };
    const toggle = () => {
      playing = !playing;
      play.textContent = playing ? "❚❚" : "▶";
      lastNow = performance.now();
      if (audio) playing ? audio.play() : audio.pause();
    };
    play.onclick = toggle;
    stage.onclick = toggle;
    range.oninput = () => jump(parseFloat(range.value));
    pick.onchange = () => jump(TL.sections[+pick.value].t0);
    window.addEventListener("keydown", (e) => {
      if (e.code === "Space") {
        e.preventDefault();
        toggle();
      }
    });
    (function loop() {
      if (playing) {
        const n = performance.now();
        if (!audio) clock += (n - lastNow) / 1000;
        lastNow = n;
        const t = now();
        if (t >= TL.duration) toggle();
        seek(t);
        range.value = t;
        pick.value = String(Math.max(0, TL.sections.findIndex((s) => t >= s.t0 && t < s.t0 + s.dur)));
      }
      time.textContent = `${fmt(now())} / ${fmt(TL.duration)}`;
      requestAnimationFrame(loop);
    })();
  }

  Explainer.start = start;
})();
