const CACHE_NAME = 'eq-v2'; // Updated version to force refresh
const STATIC_ASSETS = [
    '/',
    '/app',
    '/welcome',
    '/login',
    '/signup',
    '/static/eq_style.css',
    '/static/Rae-logo.png',
    'https://cdn.jsdelivr.net/npm/sweetalert2@11'
];

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
});

self.addEventListener('activate', (event) => {
    // Clear old caches
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Network First strategy for the app pages to avoid the "frozen/outdated" crash
    if (STATIC_ASSETS.some(url => event.request.url.includes(url))) {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
    } else {
        event.respondWith(
            caches.match(event.request).then((response) => {
                return response || fetch(event.request);
            })
        );
    }
});
