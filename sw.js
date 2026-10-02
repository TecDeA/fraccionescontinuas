/*
 * Service Worker de "Fracciones Continuas".
 *
 * IMPORTANTE (aislamiento multi-portal):
 * - Se registra SIEMPRE con URL relativa ('./sw.js'), por lo que su alcance
 *   (scope) queda limitado a la subcarpeta donde esté desplegada la app
 *   (p. ej. /fraccionescontinuas/). Nunca controla la raíz del portal
 *   (angelmicelti.github.io o tecdea.github.io) ni otras subcarpetas.
 * - El registro se omite si la app se sirve en la raíz del dominio o desde
 *   file:// (ver guard en index.html).
 */
const CACHE_VERSION = 'fraccionescontinuas-v1';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './favicon.ico',
  './icons/icon-48.png',
  './icons/icon-72.png',
  './icons/icon-96.png',
  './icons/icon-144.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-192.png',
  './icons/maskable-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Solo gestionamos peticiones dentro de nuestro propio alcance (scope),
  // para no interferir con el portal anfitrión ni con otros Service Workers.
  if (url.origin !== self.location.origin) {
    // Recursos CDN (Tailwind, KaTeX, Lucide): stale-while-revalidate, sin
    // interrumpir la red. Si fallan, servimos la última copia en caché.
    event.respondWith(
      caches.open(CACHE_VERSION).then(async (cache) => {
        const cached = await cache.match(req);
        const network = fetch(req).then((res) => {
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        }).catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // Navegación: red primero con respaldo offline al app shell.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put('./index.html', copy));
          return res;
        })
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Mismo origen y dentro del alcance: cache-first con actualización en segundo plano.
  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req).then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
