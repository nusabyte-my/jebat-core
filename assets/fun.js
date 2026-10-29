// assets/fun.ts
var RISO = { main: "#ff58a8", gold: "#ffe14a", tint: "#ffd4e8", ok: "#15b9a6", hot: "#ff7a1a", deep: "#2b50e0", white: "#ffffff", grey: "#cccccc", paper: "#f7f7f7", ink: "#000000" };
var ACCENTS = ["main", "gold", "tint", "ok", "hot", "deep"];
var PALETTES = {
  riso: RISO,
  candy: { ...RISO, main: "#b49bff", gold: "#ffd9a8", tint: "#ece5ff", ok: "#7fdcc0", hot: "#ff8fb1", deep: "#6a5cff" },
  matcha: { ...RISO, main: "#6cc46f", gold: "#f2d16b", tint: "#e2f4d6", ok: "#2bb39a", hot: "#ff8a5b", deep: "#1f6b55" },
  sunset: { ...RISO, main: "#ff7a3d", gold: "#ffc94a", tint: "#ffe2d1", ok: "#2ec4b6", hot: "#ff4d6d", deep: "#6b2d91" },
  clay: { ...RISO, main: "#f0845f", gold: "#f4c463", tint: "#fde3d6", ok: "#7fb894", hot: "#e0533d", deep: "#3d5a80" },
  aqua: { ...RISO, main: "#22c3d3", gold: "#ffd75e", tint: "#d3f4f7", ok: "#3fc46a", hot: "#ff6f61", deep: "#0f5f73" }
};
var VIEWS = {
  right: { tilt: [-18, 36], extrude: [-4, 18] },
  left: { tilt: [18, 36], extrude: [4, 18] },
  front: { tilt: [0, 30], extrude: [0, 18] },
  flat: { tilt: [-45, 55], extrude: [0, 20] }
};
var FPS = 60;
var curves = new Map;
function bezier(x1, y1, x2, y2) {
  const key = `${x1},${y1},${x2},${y2}`;
  const hit = curves.get(key);
  if (hit)
    return hit;
  const [ax, bx, cx] = [1 + 3 * x1 - 3 * x2, 3 * x2 - 6 * x1, 3 * x1];
  const [ay, by, cy] = [1 + 3 * y1 - 3 * y2, 3 * y2 - 6 * y1, 3 * y1];
  const sx = (s) => ((ax * s + bx) * s + cx) * s;
  const sy = (s) => ((ay * s + by) * s + cy) * s;
  const dx = (s) => (3 * ax * s + 2 * bx) * s + cx;
  const fn = (x) => {
    if (x <= 0)
      return 0;
    if (x >= 1)
      return 1;
    if (x1 === y1 && x2 === y2)
      return x;
    let s = x;
    for (let i = 0;i < 8; i++) {
      const [e, d] = [sx(s) - x, dx(s)];
      if (Math.abs(e) < 0.0000001)
        return sy(s);
      if (Math.abs(d) < 0.000001)
        break;
      s -= e / d;
    }
    let [lo, hi] = [0, 1];
    s = x;
    for (let i = 0;i < 40 && Math.abs(sx(s) - x) > 0.0000001; i++) {
      if (sx(s) < x)
        lo = s;
      else
        hi = s;
      s = (lo + hi) / 2;
    }
    return sy(s);
  };
  curves.set(key, fn);
  return fn;
}
var parsed = new Map;
var NUM = /-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi;
function parse(d) {
  let hit = parsed.get(d);
  if (!hit) {
    const nums = (d.match(NUM) ?? []).map(Number);
    hit = [d.split(NUM), nums];
    if (parsed.size > 4000)
      parsed.clear();
    parsed.set(d, hit);
  }
  return hit;
}
function mix(a, b, y) {
  if (typeof a === "number")
    return a + (b - a) * y;
  if (typeof a === "string") {
    if (y === 0 || a === b)
      return a;
    const [bits, na] = parse(a);
    const nb = parse(b)[1];
    let out = bits[0];
    for (let i = 0;i < na.length; i++)
      out += +(na[i] + ((nb[i] ?? na[i]) - na[i]) * y).toFixed(3) + bits[i + 1];
    return out;
  }
  const [va, vb] = [a, b];
  return [va[0] + (vb[0] - va[0]) * y, va[1] + (vb[1] - va[1]) * y];
}
var isTrack = (v) => Array.isArray(v) && Array.isArray(v[0]);
var arcs = new WeakMap;
function along(key, a, b, y) {
  let hit = arcs.get(key);
  if (!hit) {
    const [to, ti] = key[3];
    const [c1, c2] = [[a[0] + to[0], a[1] + to[1]], [b[0] + ti[0], b[1] + ti[1]]];
    const pts = [];
    const lens = [0];
    for (let i = 0;i <= 150; i++) {
      const s = i / 150;
      const u = 1 - s;
      const [w0, w1, w2, w3] = [u * u * u, 3 * u * u * s, 3 * u * s * s, s * s * s];
      pts.push([w0 * a[0] + w1 * c1[0] + w2 * c2[0] + w3 * b[0], w0 * a[1] + w1 * c1[1] + w2 * c2[1] + w3 * b[1]]);
      if (i)
        lens.push(lens[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    }
    hit = { pts, lens };
    arcs.set(key, hit);
  }
  const { pts, lens } = hit;
  const goal = lens[150] * y;
  if (goal <= 0)
    return pts[0];
  if (goal >= lens[150])
    return pts[150];
  let i = 1;
  while (lens[i] < goal)
    i++;
  const k = (goal - lens[i - 1]) / (lens[i] - lens[i - 1] || 1);
  return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k];
}
function at(v, f) {
  if (!isTrack(v))
    return v;
  if (f <= v[0][0])
    return v[0][1];
  for (let i = 0;i < v.length - 1; i++) {
    const [t0, a, e, bend] = v[i];
    const [t1, b] = v[i + 1];
    if (f >= t1)
      continue;
    if (e === 0)
      return a;
    const x = (f - t0) / (t1 - t0);
    const y = e ? bezier(e[0], e[1], e[2], e[3])(x) : x;
    return bend ? along(v[i], a, b, y) : mix(a, b, y);
  }
  return v[v.length - 1][1];
}
var shift = (track, by) => track.map(([t, v, e, bend]) => [t + by, v, e, bend]);
var mul = (m, n) => [
  m[0] * n[0] + m[2] * n[1],
  m[1] * n[0] + m[3] * n[1],
  m[0] * n[2] + m[2] * n[3],
  m[1] * n[2] + m[3] * n[3],
  m[0] * n[4] + m[2] * n[5] + m[4],
  m[1] * n[4] + m[3] * n[5] + m[5]
];
var mod = (a, n) => (a % n + n) % n;
var r2 = (v) => +v.toFixed(2);
var pt = (p) => `${r2(p[0])} ${r2(p[1])}`;
var lean = ([spin, by]) => {
  const [a, k] = [spin * Math.PI / 180, Math.cos(by * Math.PI / 180)];
  return [Math.cos(a), Math.sin(a) * k, -Math.sin(a), Math.cos(a) * k, 0, 0];
};
var onFace = (tilt, [x, y]) => {
  const t = lean(tilt);
  return [r2(t[0] * x + t[2] * y), r2(t[1] * x + t[3] * y)];
};
function poseOf(L, f, frames) {
  let [p, r, s, o, x] = [at(L.p ?? [0, 0], f), at(L.r ?? 0, f), at(L.s ?? [100, 100], f), at(L.o ?? 100, f), 0];
  const list = L.m ? Array.isArray(L.m) ? L.m : [L.m] : [];
  for (const m of list) {
    const g = mod(f - (m.at ?? 0), m.loop ?? frames);
    const k = m.k ?? 1;
    if (m.r)
      r += at(m.r, g) * k;
    if (m.p) {
      const d = at(m.p, g);
      p = [p[0] + d[0] * k, p[1] + d[1] * k];
    }
    if (m.s) {
      const d = at(m.s, g);
      s = [s[0] * (100 + (d[0] - 100) * k) / 100, s[1] * (100 + (d[1] - 100) * k) / 100];
    }
    if (m.o)
      o *= at(m.o, g) / 100;
    if (m.x)
      x += at(m.x, g) * k;
  }
  const [a, rad] = [L.a ?? [0, 0], r * Math.PI / 180];
  const [cos, sin, sx, sy] = [Math.cos(rad), Math.sin(rad), s[0] / 100, s[1] / 100];
  let m = [cos * sx, sin * sx, -sin * sy, cos * sy, 0, 0];
  const k = L.tilt ? Math.cos(L.tilt[1] * Math.PI / 180) : 1;
  if (L.tilt)
    m = mul(m, lean(L.tilt));
  m[4] = p[0] - (m[0] * a[0] + m[2] * a[1]);
  m[5] = p[1] - (m[1] * a[0] + m[3] * a[1]);
  return { m, o, x, k };
}
var paths = new Map;
var pathOf = (d) => {
  let hit = paths.get(d);
  if (!hit) {
    if (paths.size > 4000)
      paths.clear();
    hit = new Path2D(d);
    paths.set(d, hit);
  }
  return hit;
};
var samples = new Map;
function lengthOf(d, m) {
  let pts = samples.get(d);
  if (!pts) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", "path");
    el.setAttribute("d", d);
    const l = el.getTotalLength();
    pts = Array.from({ length: 65 }, (_, i) => {
      const q = el.getPointAtLength(l * i / 64);
      return [q.x, q.y];
    });
    if (samples.size > 4000)
      samples.clear();
    samples.set(d, pts);
  }
  let sum = 0;
  for (let i = 1;i < pts.length; i++) {
    const [dx, dy] = [pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]];
    sum += Math.hypot(m[0] * dx + m[2] * dy, m[1] * dx + m[3] * dy);
  }
  return sum;
}
function scene(icon, frame) {
  const f = mod(frame, icon.frames);
  const byId = new Map(icon.layers.filter((l) => l.id).map((l) => [l.id, l]));
  const memo = new Map;
  const world = (L) => {
    let hit = memo.get(L);
    if (!hit) {
      hit = poseOf(L, f, icon.frames);
      const up = L.parent ? byId.get(L.parent) : undefined;
      if (up)
        hit = { ...hit, m: mul(world(up).m, hit.m), k: world(up).k * hit.k };
      memo.set(L, hit);
    }
    return hit;
  };
  const parts = [];
  for (const L of icon.layers) {
    if (L.ip !== undefined && f < L.ip || L.op !== undefined && f >= L.op || !L.shapes.length)
      continue;
    const p = world(L);
    if (p.o > 0)
      parts.push({ L, pose: p, ds: L.shapes.map((S) => at(S.d, f)), trims: L.shapes.map((S) => S.trim === undefined ? 1 : at(S.trim, f)) });
  }
  return { f, ext: at(icon.extrude ?? [-4, 14], f), parts, world, byId };
}
function fingerprint({ ext, parts }) {
  let out = `${ext[0].toFixed(2)},${ext[1].toFixed(2)}`;
  for (const { L, pose, ds, trims } of parts) {
    out += `|${pose.m.map((v) => v.toFixed(2)).join()},${pose.o.toFixed(1)},${pose.x.toFixed(2)}`;
    L.shapes.forEach((S, i) => typeof S.d !== "string" && (out += `;${ds[i]}`));
    L.shapes.forEach((S, i) => S.trim !== undefined && (out += `;${trims[i].toFixed(3)}`));
  }
  return out;
}
function render(ctx, icon, sc, palette) {
  const base = ctx.getTransform();
  const colour = (c) => c[0] === "#" ? c : palette[c];
  const [W, ink, { ext, world, byId, f }] = [icon.line ?? 4, colour(icon.ink ?? "ink"), sc];
  const len = Math.hypot(ext[0], ext[1]) || 1;
  const dev = Math.sqrt(Math.abs(base.a * base.d - base.b * base.c)) || 1;
  const step = new DOMMatrix;
  ctx.save();
  ctx.miterLimit = 4;
  for (const { L, pose, ds, trims } of sc.parts) {
    const { m, o, x, k } = pose;
    const [det, dm] = [m[0] * m[3] - m[1] * m[2], new DOMMatrix(m)];
    const grow = Math.sqrt(Math.abs(det) / Math.abs(k || 1));
    ctx.globalAlpha = Math.min(1, o / 100);
    const mask = L.clip ? byId.get(L.clip) : undefined;
    if (mask) {
      ctx.save();
      const region = new Path2D;
      const mm = new DOMMatrix(world(mask).m);
      for (const s of mask.shapes)
        region.addPath(pathOf(at(s.d, f)), mm);
      ctx.setTransform(base);
      ctx.clip(region);
    }
    L.shapes.forEach((S, i) => {
      const d = ds[i];
      const path = new Path2D;
      path.addPath(pathOf(d), dm);
      const w = (S.line === false ? 0 : typeof S.line === "number" ? S.line : W) * grow;
      ctx.setTransform(base);
      ctx.lineCap = S.round ? "round" : "butt";
      ctx.lineJoin = S.round ? "round" : "miter";
      const depth = S.depth ?? 0;
      if (depth && S.fill) {
        const kk = depth + x / len;
        const [vx, vy] = [ext[0] * kk, ext[1] * kk];
        const n = Math.min(64, Math.max(2, Math.ceil(Math.hypot(vx, vy) * dev / 0.8)));
        const sweep = new Path2D;
        for (let j = n;j >= 0; j--)
          step.e = vx * j / n, step.f = vy * j / n, sweep.addPath(path, step);
        if (w) {
          ctx.strokeStyle = ink;
          ctx.lineWidth = w * 2;
          ctx.stroke(sweep);
        }
        ctx.fillStyle = colour(S.side ?? S.fill);
        ctx.fill(sweep);
        const auto = S.crease === false ? undefined : corners.get(d);
        if (w && (S.edges || auto)) {
          const vl = Math.hypot(vx, vy) || 1;
          const lines = [...S.edges ?? []];
          const faces = (nx, ny) => {
            const [wx, wy] = [(m[3] * nx - m[1] * ny) * Math.sign(det), (m[0] * ny - m[2] * nx) * Math.sign(det)];
            return (wx * vx + wy * vy) / (Math.hypot(wx, wy) * vl) > 0.05;
          };
          for (const [cx, cy, ax, ay, bx, by] of auto ?? [])
            if (faces(ax, ay) && faces(bx, by))
              lines.push([cx, cy]);
          ctx.strokeStyle = ink;
          ctx.lineWidth = w;
          ctx.beginPath();
          for (const [ex, ey] of lines) {
            const [px, py] = [m[0] * ex + m[2] * ey + m[4], m[1] * ex + m[3] * ey + m[5]];
            ctx.moveTo(px, py);
            ctx.lineTo(px + vx, py + vy);
          }
          ctx.stroke();
        }
      }
      if (S.fill) {
        if (w) {
          ctx.strokeStyle = ink;
          ctx.lineWidth = w * 2;
          ctx.stroke(path);
        }
        ctx.fillStyle = colour(S.fill);
        ctx.fill(path);
      } else if (w && trims[i] > 0) {
        ctx.strokeStyle = ink;
        ctx.lineWidth = w;
        if (trims[i] < 1) {
          const l = lengthOf(d, m);
          ctx.setLineDash([l * trims[i], l]);
        }
        ctx.stroke(path);
        ctx.setLineDash([]);
      }
    });
    if (mask)
      ctx.restore();
  }
  ctx.restore();
}
var themed = new Map;
var resolve = (p) => {
  if (!p)
    return RISO;
  const key = JSON.stringify(p);
  let hit = themed.get(key);
  if (!hit) {
    if (themed.size > 200)
      themed.clear();
    hit = { ...RISO, ...p };
    themed.set(key, hit);
  }
  return hit;
};
function draw(ctx, icon, frame, palette) {
  render(ctx, icon, scene(icon, frame), resolve(palette));
}
var lin = (c) => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
var gam = (c) => c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055;
function lch(color) {
  const h = color.length === 4 ? color.replace(/[0-9a-f]/gi, (c) => c + c) : color;
  const n = parseInt(h.slice(1, 7), 16);
  const [r, g, b] = [lin((n >> 16 & 255) / 255), lin((n >> 8 & 255) / 255), lin((n & 255) / 255)];
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  const [A, B] = [1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
  return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, Math.hypot(A, B), Math.atan2(B, A) * 180 / Math.PI];
}
function hex([L, C, H]) {
  const rgb = (c) => {
    const [A, B] = [c * Math.cos(H * Math.PI / 180), c * Math.sin(H * Math.PI / 180)];
    const [l, m, s] = [(L + 0.3963377774 * A + 0.2158037573 * B) ** 3, (L - 0.1055613458 * A - 0.0638541728 * B) ** 3, (L - 0.0894841775 * A - 1.291485548 * B) ** 3];
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
  };
  const fits = (c) => rgb(c).every((v) => v >= -0.0001 && v <= 1 + 0.0001);
  let [lo, hi] = [0, C];
  if (fits(C))
    lo = C;
  else
    for (let i = 0;i < 24; i++)
      fits((lo + hi) / 2) ? lo = (lo + hi) / 2 : hi = (lo + hi) / 2;
  return `#${rgb(lo).map((v) => Math.round(Math.min(1, Math.max(0, gam(v))) * 255).toString(16).padStart(2, "0")).join("")}`;
}
function hue(deg, from = RISO) {
  const out = { ...from };
  for (const k of ACCENTS) {
    const [L, C, H] = lch(from[k]);
    out[k] = hex([L, C, H + deg]);
  }
  return out;
}
function brand(primary, secondary, from = RISO) {
  const [, C, H] = lch(primary);
  const two = secondary ?? hex([0.42, C, H]);
  const [, C2, H2] = lch(two);
  return { ...from, main: primary, tint: hex([0.93, Math.min(C, 0.06), H]), hot: hex([0.6, C, H]), deep: two, gold: hex([0.86, Math.min(C2, 0.12), H2]), ok: hex([0.7, C2, H2]) };
}
function mono(color, from = RISO) {
  const [, C, H] = lch(color);
  const steps = { tint: 0.94, gold: 0.81, ok: 0.72, main: 0.64, hot: 0.55, deep: 0.45 };
  const out = { ...from };
  for (const k of ACCENTS)
    out[k] = hex([steps[k], Math.min(C, lch(from[k])[1]), H]);
  return out;
}
var rect = (x, y, w, h, r = 0) => poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], r);
var pill = (x, y, w, h) => rect(x, y, w, h, Math.min(w, h) / 2);
var ellipse = (cx, cy, rx, ry = rx) => `M${pt([cx - rx, cy])}A${r2(rx)} ${r2(ry)} 0 1 1 ${pt([cx + rx, cy])}A${r2(rx)} ${r2(ry)} 0 1 1 ${pt([cx - rx, cy])}Z`;
var corners = new Map;
function poly(points, r = 0) {
  const n = points.length;
  let d = "";
  let area = 0;
  for (let i = 0;i < n; i++)
    area += points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1];
  const marks = [];
  for (let i = 0;i < n; i++) {
    const [P, A, B] = [points[i], points[(i + n - 1) % n], points[(i + 1) % n]];
    const rad = typeof r === "number" ? r : r[i] ?? 0;
    const [ua, ub] = [[A[0] - P[0], A[1] - P[1]], [B[0] - P[0], B[1] - P[1]]];
    const [la, lb] = [Math.hypot(ua[0], ua[1]), Math.hypot(ub[0], ub[1])];
    const cos = (ua[0] * ub[0] + ua[1] * ub[1]) / (la * lb);
    const half = Math.acos(Math.max(-1, Math.min(1, cos))) / 2;
    let t = rad && half > 0.001 ? rad / Math.tan(half) : 0;
    t = Math.min(t, la / 2, lb / 2);
    const rr = t * Math.tan(half);
    const T1 = [P[0] + ua[0] / la * t, P[1] + ua[1] / la * t];
    const T2 = [P[0] + ub[0] / lb * t, P[1] + ub[1] / lb * t];
    const cross = ua[0] * ub[1] - ua[1] * ub[0];
    const sweep = cross < 0 ? 1 : 0;
    d += `${i ? "L" : "M"}${pt(T1)}A${r2(rr)} ${r2(rr)} 0 0 ${sweep} ${pt(T2)}`;
    const round = rad > 0 && t >= Math.min(la, lb) / 2 - 0.000001;
    if (Math.sign(cross) === -Math.sign(area) && !round) {
      let [bx, by] = [ua[0] / la + ub[0] / lb, ua[1] / la + ub[1] / lb];
      const bl = Math.hypot(bx, by) || 1;
      [bx, by] = [bx / bl, by / bl];
      const k = half > 0.001 ? rr / Math.sin(half) - rr : 0;
      const out = (u, l) => {
        const [nx, ny] = [-u[1] / l, u[0] / l];
        return nx * bx + ny * by > 0 ? [-nx, -ny] : [nx, ny];
      };
      const [na, nb] = [out(ua, la), out(ub, lb)];
      marks.push([P[0] + bx * k, P[1] + by * k, na[0], na[1], nb[0], nb[1]]);
    }
  }
  d += "Z";
  if (corners.size > 4000)
    corners.clear();
  corners.set(d, marks);
  return d;
}
function spark(cx, cy, r, pinch = 0.28) {
  const q = r * pinch;
  return `M${pt([cx, cy - r])}Q${pt([cx + q, cy - q])} ${pt([cx + r, cy])}Q${pt([cx + q, cy + q])} ${pt([cx, cy + r])}Q${pt([cx - q, cy + q])} ${pt([cx - r, cy])}Q${pt([cx - q, cy - q])} ${pt([cx, cy - r])}Z`;
}
function rosette(cx, cy, r, n = 8, bulge = 0.62) {
  let d = "";
  for (let i = 0;i <= n; i++) {
    const a = i / n * Math.PI * 2 - Math.PI / 2;
    const p = [cx + Math.cos(a) * r, cy + Math.sin(a) * r];
    const chord = 2 * r * Math.sin(Math.PI / n);
    d += i ? `A${r2(chord * bulge)} ${r2(chord * bulge)} 0 0 1 ${pt(p)}` : `M${pt(p)}`;
  }
  return d + "Z";
}
var ring = (cx, cy, r, hole) => ellipse(cx, cy, r) + `M${pt([cx - hole, cy])}A${r2(hole)} ${r2(hole)} 0 1 0 ${pt([cx + hole, cy])}A${r2(hole)} ${r2(hole)} 0 1 0 ${pt([cx - hole, cy])}Z`;
var star = (cx, cy, r, inner = 0.48, n = 5, round = 3) => poly(Array.from({ length: n * 2 }, (_, i) => {
  const [a, k] = [i / (n * 2) * Math.PI * 2 - Math.PI / 2, i % 2 ? inner : 1];
  return [cx + Math.cos(a) * r * k, cy + Math.sin(a) * r * k];
}), round);
function view(yaw, pitch) {
  const [a, e] = [yaw * Math.PI / 180, pitch * Math.PI / 180];
  return ([x, y, z]) => [
    r2(x * Math.cos(a) - y * Math.sin(a)),
    r2(-((x * Math.sin(a) + y * Math.cos(a)) * Math.sin(e) + z * Math.cos(e)))
  ];
}
var line = (...points) => points.map((p, i) => `${i ? "L" : "M"}${pt(p)}`).join("");
function arc(cx, cy, r, from, to) {
  const [a, b] = [from * Math.PI / 180, to * Math.PI / 180];
  const large = Math.abs(to - from) > 180 ? 1 : 0;
  return `M${pt([cx + Math.cos(a) * r, cy + Math.sin(a) * r])}A${r2(r)} ${r2(r)} 0 ${large} ${to > from ? 1 : 0} ${pt([cx + Math.cos(b) * r, cy + Math.sin(b) * r])}`;
}
var clock = { frame: 0, speed: 1, paused: false };
var BOUNCE = [
  [0, 0],
  [0.076, 0.5737],
  [0.1187, 0.8382],
  [0.1419, 0.9463],
  [0.1654, 1.0292],
  [0.1897, 1.0886],
  [0.2153, 1.1258],
  [0.2297, 1.137],
  [0.2448, 1.1424],
  [0.261, 1.1423],
  [0.2786, 1.1366],
  [0.3101, 1.1165],
  [0.3862, 1.0507],
  [0.4257, 1.0219],
  [0.4699, 0.9995],
  [0.5163, 0.9872],
  [0.5877, 0.9842],
  [0.8126, 1.0011],
  [1, 1]
];
function popBounce(t) {
  if (t <= 0)
    return 0;
  if (t >= 1)
    return 1;
  const i = BOUNCE.findIndex(([x]) => x >= t);
  const [[x0, y0], [x1, y1]] = [BOUNCE[i - 1], BOUNCE[i]];
  return y0 + (y1 - y0) * (t - x0) / (x1 - x0);
}
function present(canvas, icon, sc, e, palette, css) {
  const dpr = Math.min(3, window.devicePixelRatio || 1);
  const px = Math.max(1, Math.round(css * dpr));
  if (canvas.width !== px || canvas.height !== px)
    canvas.width = canvas.height = px;
  const ctx = canvas.getContext("2d");
  if (!ctx)
    return;
  const size = icon.size ?? 500;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, px, px);
  const b = popBounce(e);
  if (b <= 0)
    return;
  ctx.globalAlpha = Math.min(1, b);
  ctx.translate(px / 2, px / 2);
  ctx.rotate(-90 * (1 - b) * Math.PI / 180);
  ctx.scale(0.2 + 0.8 * b, 0.2 + 0.8 * b);
  ctx.translate(-px / 2, -px / 2);
  ctx.scale(px / size, px / size);
  render(ctx, icon, sc, palette);
}
function paint(canvas, icon, frame, e = 1, palette) {
  present(canvas, icon, scene(icon, frame), e, resolve(palette), canvas.clientWidth);
}
var live = new Set;
var [raf, last] = [0, 0];
var reduce;
var still = () => {
  if (reduce === undefined)
    reduce = typeof matchMedia === "undefined" ? null : matchMedia("(prefers-reduced-motion: reduce)");
  return !!reduce?.matches;
};
function frameOf({ icon, o, start }) {
  if (still())
    return icon.still ?? 0;
  const t = clock.frame - (start ?? 0) + (o.offset ?? 0);
  if (o.loop !== false)
    return t;
  return t < (icon.still || icon.frames) ? t : icon.still ?? 0;
}
function tick(now) {
  const dt = last ? Math.min(100, now - last) : 0;
  last = now;
  if (!clock.paused)
    clock.frame += dt / 1000 * FPS * clock.speed;
  for (const l of live) {
    if (!l.shown)
      continue;
    try {
      if (!l.seen)
        l.seen = now;
      if (l.o.loop === false && l.start === undefined)
        l.start = clock.frame;
      const e = l.o.enter === undefined || still() ? 1 : (now - l.seen - l.o.enter * 1000) / 1000;
      const [sc, css] = [scene(l.icon, frameOf(l)), l.css || l.canvas.clientWidth];
      const key = e < 1 ? "" : `${css}|${window.devicePixelRatio}|${fingerprint(sc)}`;
      if (key && key === l.key)
        continue;
      present(l.canvas, l.icon, sc, e, l.pal, css);
      l.key = key;
    } catch (err) {
      console.error(`fun-isometric: ${l.icon.name} stopped`, err);
      l.stop();
    }
  }
  raf = live.size ? requestAnimationFrame(tick) : 0;
}
function play(canvas, icon, opts = {}) {
  const io = typeof IntersectionObserver === "undefined" ? null : new IntersectionObserver(([en]) => l.shown = en.isIntersecting);
  const ro = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(([en]) => l.css = en.contentRect.width);
  const stop = () => {
    io?.disconnect();
    ro?.disconnect();
    live.delete(l);
  };
  const l = { canvas, icon, o: { ...opts }, pal: resolve(opts.palette), seen: 0, shown: !io, css: 0, key: "", stop };
  io?.observe(canvas);
  ro?.observe(canvas);
  live.add(l);
  if (!raf)
    last = 0, raf = requestAnimationFrame(tick);
  return {
    stop,
    replay: () => (l.start = clock.frame, l.key = ""),
    set: ({ icon: next, ...o }) => {
      if (next)
        l.icon = next;
      Object.assign(l.o, o);
      l.pal = resolve(l.o.palette);
      l.key = "";
    }
  };
}
export {
  ACCENTS,
  FPS,
  PALETTES,
  RISO,
  VIEWS,
  arc,
  at,
  bezier,
  brand,
  clock,
  draw,
  ellipse,
  hue,
  line,
  mono,
  onFace,
  paint,
  pill,
  play,
  poly,
  popBounce,
  rect,
  ring,
  rosette,
  shift,
  spark,
  star,
  view
};
