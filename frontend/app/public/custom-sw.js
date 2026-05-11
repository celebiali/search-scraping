self.addEventListener('push', (event) => {
  console.log('Push event received:', event);
  let data = {};
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      console.warn('Push data is not JSON:', event.data.text());
      data = { title: 'Fiyat Takibi', body: event.data.text() };
    }
  }

  const title = data.title || 'Fiyat Takibi';
  const options = {
    body: data.body || 'Bir güncelleme var!',
    vibrate: [100, 50, 100],
    tag: 'price-alert',
    renotify: true,
    data: {
      url: data.url || '/'
    }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data.url;
  
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});
