(() => {
  const handler = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.kk;
  if (!handler) return;

  const call = async (cmd, args) => {
    const raw = await handler.postMessage(JSON.stringify({ cmd, args: args || {} }));
    const out = JSON.parse(raw);
    if (out.error) throw new Error(out.error);
    return out.result;
  };

  const plainHeaders = (h) => {
    const out = {};
    if (!h) return out;
    if (typeof Headers !== "undefined" && h instanceof Headers) {
      h.forEach((v, k) => { out[k] = v; });
      return out;
    }
    if (Array.isArray(h)) {
      for (const [k, v] of h) out[k] = String(v);
      return out;
    }
    for (const k of Object.keys(h)) out[k] = String(h[k]);
    return out;
  };

  const encodeBody = async (body) => {
    if (body === undefined || body === null) return null;
    let bytes;
    if (typeof body === "string") bytes = new TextEncoder().encode(body);
    else if (body instanceof Blob) bytes = new Uint8Array(await body.arrayBuffer());
    else if (body instanceof ArrayBuffer) bytes = new Uint8Array(body);
    else if (ArrayBuffer.isView(body)) bytes = new Uint8Array(body.buffer, body.byteOffset, body.byteLength);
    else bytes = new TextEncoder().encode(String(body));
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(s);
  };

  const nativeFetch = async (input, init) => {
    const o = init || {};
    const url = typeof input === "string" ? input : (input && input.url) || String(input);
    const r = await call("http", {
      url,
      method: (o.method || "GET").toUpperCase(),
      headers: plainHeaders(o.headers),
      body: await encodeBody(o.body)
    });
    const bin = atob(r.body || "");
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const noBody = [101, 103, 204, 205, 304].includes(r.status) || (o.method || "").toUpperCase() === "HEAD";
    return new Response(noBody ? null : bytes, { status: r.status, statusText: r.reason || "", headers: r.headers || {} });
  };

  const closeWindow = () => call("quit");

  window.__TAURI__ = Object.freeze({
    fs: Object.freeze({
      readTextFile: (path) => call("read", { path: String(path) }),
      writeTextFile: (path, contents) => call("write", { path: String(path), contents: String(contents) })
    }),
    dialog: Object.freeze({
      open: (opts) => call("open", opts || {}),
      save: (opts) => call("save", opts || {})
    }),
    http: Object.freeze({ fetch: nativeFetch }),
    window: Object.freeze({ getCurrentWindow: () => ({ close: closeWindow }) }),
    process: Object.freeze({ exit: closeWindow })
  });
})();
