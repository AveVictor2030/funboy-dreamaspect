var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

var COOKIE_NAME = "da_funboy";
var PATH_PREFIX = "/funboy";
function escapeHtml(value) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
__name(escapeHtml, "escapeHtml");
function requestPrefix(pathname) {
  if (pathname === PATH_PREFIX || pathname.startsWith(`${PATH_PREFIX}/`)) return PATH_PREFIX;
  return "";
}
__name(requestPrefix, "requestPrefix");
function cookiePath(prefix) {
  return prefix || "/";
}
__name(cookiePath, "cookiePath");
function homePath(prefix) {
  return prefix ? `${prefix}/` : "/";
}
__name(homePath, "homePath");
function enterPath(prefix) {
  return `${prefix}/enter`;
}
__name(enterPath, "enterPath");
function isEnterPath(pathname, prefix) {
  const enter = enterPath(prefix);
  return pathname === enter || pathname === `${enter}/`;
}
__name(isEnterPath, "isEnterPath");
function matchesPrefix(path, prefix) {
  if (!prefix) return true;
  return path === prefix || path.startsWith(`${prefix}/`);
}
__name(matchesPrefix, "matchesPrefix");
function cookieValue(request) {
  const raw = request.headers.get("Cookie") ?? "";
  for (const part of raw.split(";")) {
    const trimmed = part.trim();
    const i = trimmed.indexOf("=");
    if (i === -1) continue;
    if (trimmed.slice(0, i) !== COOKIE_NAME) continue;
    try {
      return decodeURIComponent(trimmed.slice(i + 1));
    } catch {
      return trimmed.slice(i + 1);
    }
  }
  return "";
}
__name(cookieValue, "cookieValue");
function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) {
    out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return out === 0;
}
__name(timingSafeEqual, "timingSafeEqual");
async function gateToken(password) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`da-funboy:${password}`));
  return [...new Uint8Array(buf)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}
__name(gateToken, "gateToken");
async function hasGateCookie(request, password) {
  const got = cookieValue(request);
  if (!got) return false;
  return timingSafeEqual(got, await gateToken(password));
}
__name(hasGateCookie, "hasGateCookie");
function isGateAsset(assetPath) {
  return assetPath === "/BrownLL-Regular.otf" || assetPath.endsWith("/BrownLL-Regular.otf");
}
__name(isGateAsset, "isGateAsset");
function safeNext(raw, prefix, origin) {
  const fallback = homePath(prefix);
  if (!raw || raw.includes("\\")) return fallback;
  try {
    const url = new URL(raw, origin);
    if (url.origin !== origin) return fallback;
    if (isEnterPath(url.pathname, prefix)) return fallback;
    if (prefix) {
      if (!matchesPrefix(url.pathname, prefix)) return fallback;
    }
    return `${url.pathname}${url.search}`;
  } catch {
    return fallback;
  }
}
__name(safeNext, "safeNext");
function rewriteToAsset(request, prefix) {
  const url = new URL(request.url);
  const path = url.pathname;
  if (path === PATH_PREFIX) {
    return Response.redirect(new URL(`${PATH_PREFIX}/${url.search}`, url).href, 307);
  }
  const assetUrl = new URL(request.url);
  if (prefix === PATH_PREFIX) {
    assetUrl.pathname = path.slice(PATH_PREFIX.length) || "/";
  }
  return new Request(assetUrl, request);
}
__name(rewriteToAsset, "rewriteToAsset");
function loginHtml({ prefix, name, error, next }) {
  const font = `${prefix}/BrownLL-Regular.otf`;
  const action = enterPath(prefix);
  const heading = name ? `Welcome, ${escapeHtml(name)}.` : "Welcome.";
  const err = error ? `<p class="err" role="alert">That password does not match.</p>` : "";
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex" />
  <title>FUNBOY</title>
  <style>
    @font-face {
      font-family: "BrownLL";
      src: url("${font}") format("opentype");
      font-weight: 100 900;
      font-style: normal;
      font-display: swap;
    }
    :root { --brown: #8d3f29; --brown-dark: #6e2f1e; --green: #1B9500; }
    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    body {
      background: #fff;
      color: #000;
      font-family: "BrownLL", Brown, sans-serif;
      line-height: 1.5;
    }
    .bar { background: var(--brown); color: #fff; }
    .inner { width: min(1000px, calc(100% - 2rem)); margin: 0 auto; }
    .bar .inner { min-height: 56px; display: flex; align-items: center; }
    .brand {
      margin: 0;
      font-size: 14px;
      letter-spacing: .04em;
      text-transform: uppercase;
    }
    .hero { background: var(--brown); color: #fff; padding: 48px 0 56px; }
    h1 { font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 500; letter-spacing: -0.025em; margin: 0; }
    .lead { margin: 12px 0 0; max-width: 22rem; color: rgba(255,255,255,.88); font-size: 15px; }
    form { margin-top: 1.75rem; max-width: 22rem; }
    label {
      display: block;
      font-size: 12px;
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    input[type="password"] {
      display: block;
      width: 100%;
      margin-top: 0.4rem;
      height: 2.75rem;
      padding: 0 0.75rem;
      border: 1px solid rgba(255,255,255,.28);
      background: #fff;
      color: #000;
      font-family: inherit;
      font-size: 16px;
      border-radius: 8px;
    }
    input[type="password"]:focus {
      outline: 2px solid #fff;
      outline-offset: 2px;
    }
    .err { margin: 0.6rem 0 0; font-size: 0.85rem; color: #fff; }
    button {
      --mx: 0; --my: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-top: 1rem;
      height: 2.75rem;
      padding: 0 1.25rem;
      border: 0;
      border-radius: 8px;
      background: #000;
      color: #fff;
      font-family: inherit;
      font-size: 0.95rem;
      letter-spacing: .04em;
      text-transform: uppercase;
      cursor: pointer;
      transform: translate3d(calc(var(--mx) * 5px), calc(var(--my) * 4px), 0);
      transition: transform 0.75s cubic-bezier(0.22, 1, 0.36, 1), background-color 0.2s ease, box-shadow 0.35s ease;
    }
    @media (hover: hover) and (pointer: fine) {
      button:hover {
        background: var(--brown-dark);
        transform: translate3d(calc(var(--mx) * 5px), calc(var(--my) * 4px - 5px), 0);
        box-shadow: 0 8px 20px rgba(0,0,0,.18);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      button, button:hover { transform: none; box-shadow: none; transition: background-color 0.2s ease; }
    }
  </style>
</head>
<body>
  <header class="bar"><div class="inner"><p class="brand">FUNBOY</p></div></header>
  <main class="hero">
    <div class="inner">
      <h1>${heading}</h1>
      <p class="lead">Enter the password to open this report.</p>
      <form method="post" action="${action}">
        <input type="hidden" name="next" value="${escapeHtml(next)}" />
        <label for="password">Password</label>
        <input id="password" name="password" type="password" autocomplete="current-password" autofocus required />
        ${err}
        <button type="submit">Enter</button>
      </form>
    </div>
  </main>
  <script>
    (function () {
      var fine = window.matchMedia("(hover: hover) and (pointer: fine)");
      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
      if (!fine.matches || reduce.matches) return;
      var btn = document.querySelector("button");
      if (!btn) return;
      btn.addEventListener("pointermove", function (event) {
        var box = btn.getBoundingClientRect();
        if (!box.width || !box.height) return;
        var x = ((event.clientX - box.left) / box.width) * 2 - 1;
        var y = ((event.clientY - box.top) / box.height) * 2 - 1;
        btn.style.setProperty("--mx", Math.max(-1, Math.min(1, x)).toFixed(3));
        btn.style.setProperty("--my", Math.max(-1, Math.min(1, y)).toFixed(3));
      });
      btn.addEventListener("pointerleave", function () {
        btn.style.setProperty("--mx", "0");
        btn.style.setProperty("--my", "0");
      });
    })();
  <\/script>
</body>
</html>`;
}
__name(loginHtml, "loginHtml");
function loginResponse(prefix, url, name, error) {
  const next = safeNext(url.searchParams.get("next") || `${url.pathname}${url.search}`, prefix, url.origin);
  const html = loginHtml({ prefix, name, error, next });
  return new Response(html, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store, must-revalidate",
      "cdn-cache-control": "no-store"
    }
  });
}
__name(loginResponse, "loginResponse");
async function handleEnter(request, prefix, password, name) {
  const url = new URL(request.url);
  let form;
  try {
    form = await request.formData();
  } catch {
    return loginResponse(prefix, url, name, true);
  }
  const submitted = String(form.get("password") ?? "").trim();
  const next = safeNext(String(form.get("next") ?? ""), prefix, url.origin);
  if (submitted !== password) {
    return loginResponse(prefix, new URL(`${homePath(prefix)}?next=${encodeURIComponent(next)}`, url.origin), name, true);
  }
  const token = await gateToken(password);
  const dest = new URL(next, url.origin);
  const path = cookiePath(prefix);
  return new Response(null, {
    status: 302,
    headers: {
      location: dest.href,
      "set-cookie": `${COOKIE_NAME}=${token}; Path=${path}; HttpOnly; Secure; SameSite=Lax; Max-Age=1209600`,
      "cache-control": "no-store"
    }
  });
}
__name(handleEnter, "handleEnter");
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const prefix = requestPrefix(url.pathname);
    const password = String(env.PORTAL_PASSWORD ?? "").trim();
    const name = String(env.PORTAL_GATE_NAME ?? "FUNBOY");
    if (password && request.method === "POST" && isEnterPath(url.pathname, prefix)) {
      return handleEnter(request, prefix, password, name);
    }
    const rewritten = rewriteToAsset(request, prefix);
    if (rewritten instanceof Response) return rewritten;
    const assetPath = new URL(rewritten.url).pathname;
    if (password) {
      const signedIn = await hasGateCookie(request, password);
      if (isEnterPath(url.pathname, prefix)) {
        if (signedIn) return Response.redirect(new URL(homePath(prefix), url).href, 302);
        return loginResponse(prefix, url, name, false);
      }
      if (!signedIn && !isGateAsset(assetPath)) {
        return loginResponse(prefix, url, name, false);
      }
    }
    let current = rewritten;
    let res = await env.ASSETS.fetch(current);
    for (let hop = 0; hop < 5; hop++) {
      if (![301, 302, 303, 307, 308].includes(res.status)) break;
      const loc = res.headers.get("Location");
      if (!loc) break;
      current = new Request(new URL(loc, current.url).href, current);
      res = await env.ASSETS.fetch(current);
    }
    const headers = new Headers(res.headers);
    const type = headers.get("content-type") ?? "";
    if (!type.includes("text/html")) return res;
    headers.set("Cache-Control", "no-store, must-revalidate");
    return new Response(res.body, { status: res.status, headers });
  }
};
