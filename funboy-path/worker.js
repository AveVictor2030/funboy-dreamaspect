export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    let path = url.pathname;
    if (path === "/funboy") {
      path = "/funboy/";
    }
    if (!path.startsWith("/funboy/") && path !== "/funboy/") {
      return new Response("Not found", { status: 404 });
    }

    if (path === "/funboy/enter" && request.method === "POST") {
      return handleEnter(request, env);
    }

    const assetRel = path.slice("/funboy".length) || "/";
    if (assetRel === "/BrownLL-Regular.otf") {
      return env.ASSETS.fetch(assetRequest(assetRel, request));
    }

    if (!(await validSession(request, env))) {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return new Response("Unauthorized", { status: 401 });
      }
      if (assetRel === "/" || assetRel === "/index.html") {
        return loginPage(env);
      }
      return loginPage(env);
    }

    const file =
      assetRel === "/" || assetRel === ""
        ? "/index.html"
        : assetRel.endsWith("/")
          ? assetRel + "index.html"
          : assetRel;
    return env.ASSETS.fetch(assetRequest(file, request));
  },
};

function assetRequest(path, request) {
  const u = new URL(request.url);
  u.pathname = path;
  return new Request(u.toString(), request);
}

async function handleEnter(request, env) {
  const form = await request.formData();
  const password = String(form.get("password") || "");
  const next = String(form.get("next") || "/funboy/");
  if (!env.FUNBOY_PASSWORD || password !== env.FUNBOY_PASSWORD) {
    return loginPage(env, true);
  }
  const token = await sessionToken(env);
  const headers = new Headers();
  headers.set("Location", next.startsWith("/funboy") ? next : "/funboy/");
  headers.append(
    "Set-Cookie",
    `da_funboy=${token}; Path=/funboy; HttpOnly; Secure; SameSite=Lax; Max-Age=1209600`,
  );
  headers.set("Cache-Control", "no-store");
  return new Response(null, { status: 302, headers });
}

async function validSession(request, env) {
  const cookie = parseCookie(request.headers.get("Cookie") || "").da_funboy;
  if (!cookie || !env.FUNBOY_PASSWORD) return false;
  const expected = await sessionToken(env);
  return cookie === expected;
}

async function sessionToken(env) {
  const msg = new TextEncoder().encode(
    `da_funboy|${env.COOKIE_SALT || "dreamaspect"}|${env.FUNBOY_PASSWORD}`,
  );
  const hash = await crypto.subtle.digest("SHA-256", msg);
  return hex(new Uint8Array(hash));
}

function parseCookie(header) {
  const out = {};
  header.split(";").forEach((part) => {
    const i = part.indexOf("=");
    if (i === -1) return;
    out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
  });
  return out;
}

function hex(bytes) {
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function loginPage(env, bad) {
  const err = bad
    ? '<p class="err">That password did not match. Try again.</p>'
    : "";
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex" />
  <title>FUNBOY</title>
  <style>
    @font-face {
      font-family: "BrownLL";
      src: url("/funboy/BrownLL-Regular.otf") format("opentype");
      font-weight: 100 900;
      font-style: normal;
      font-display: swap;
    }
    :root { --brown: #8d3f29; --brown-dark: #6e2f1e; --green: #1B9500; }
    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    body { background: #fff; color: #000; font-family: "BrownLL", Brown, sans-serif; line-height: 1.5; }
    .bar { background: var(--brown); color: #fff; }
    .inner { width: min(1000px, calc(100% - 2rem)); margin: 0 auto; }
    .bar .inner { min-height: 56px; display: flex; align-items: center; }
    .brand { margin: 0; font-size: 14px; letter-spacing: .04em; text-transform: uppercase; }
    .hero { background: var(--brown); color: #fff; padding: 48px 0 56px; }
    h1 { font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 500; letter-spacing: -0.025em; margin: 0; }
    .lead { margin: 12px 0 0; max-width: 22rem; color: rgba(255,255,255,.88); font-size: 15px; }
    form { margin-top: 1.75rem; max-width: 22rem; }
    label { display: block; font-size: 12px; letter-spacing: .04em; text-transform: uppercase; margin-bottom: 6px; }
    input[type=password] { width: 100%; padding: 12px 14px; border: 1px solid rgba(255,255,255,.35); border-radius: 8px; background: rgba(255,255,255,.12); color: #fff; font: inherit; }
    button { margin-top: 14px; width: 100%; padding: 12px 16px; border: 0; border-radius: 8px; background: #000; color: #fff; font: inherit; font-size: 14px; letter-spacing: .04em; text-transform: uppercase; cursor: pointer; }
    .err { color: #ffc9c9; font-size: 14px; margin: 0 0 12px; }
  </style>
</head>
<body>
  <header class="bar"><div class="inner"><p class="brand">Dream Aspect · FUNBOY</p></div></header>
  <main class="hero"><div class="inner">
    <h1>Welcome, FUNBOY.</h1>
    <p class="lead">Enter the password to open this report.</p>
    ${err}
    <form method="post" action="/funboy/enter">
      <input type="hidden" name="next" value="/funboy/" />
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" autofocus required />
      <button type="submit">Enter</button>
    </form>
  </div></main>
</body>
</html>`;
  return new Response(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
