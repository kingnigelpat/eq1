const CACHE_NAME = 'eq-v1';
const STATIC_ASSETS = [
    '/',
    '/app',
    '/welcome',
    '/login',
    '/signup',
    '/static/eq_style.css',
    '/static/RAE-removebg-preview.png',
    '/static/ethereal_aurora_bg.png',
    'https://cdn.jsdelivr.net/npm/sweetalert2@11'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
});

self.addEventListener('fetch', (event) => {
    // Only cache static files, let API/flask routes be fetched online 
    // but try to serve cached shell for app feeling
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
