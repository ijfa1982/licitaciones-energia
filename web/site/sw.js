// Permite instalar la web como app y abrirla sin conexión con los últimos datos descargados.
const CACHE = "licitaciones-v4";
const BASE = ["./", "index.html", "estilos.css", "app.js", "config.js", "manifest.webmanifest", "img/icono-192.png", "provincias.js"];
self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(BASE))));
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))));
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  // Red primero (datos y páginas al día); si no hay conexión, lo guardado.
  e.respondWith(fetch(e.request).then((r) => {
    const copia = r.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copia));
    return r;
  }).catch(() => caches.match(e.request)));
});
