const CACHE = 'kiselgram-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('push', (e) => {
  let data = {title: 'Kiselgram', body: '', icon: '/static/img/icon.png', tag: 'default'};
  try { data = e.data ? e.data.json() : data; } catch(_) {}
  const opts = {
    body: data.body,
    icon: data.icon || '/static/img/icon.png',
    badge: '/static/img/icon.png',
    tag: data.tag || 'default',
    data: {url: data.url || '/'}
  };
  e.waitUntil(self.registration.showNotification(data.title, opts));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = e.notification.data?.url || '/';
  e.waitUntil(clients.openWindow(url));
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});
