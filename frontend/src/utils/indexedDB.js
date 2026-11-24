// PHC Bridge IndexedDB Storage Engine for Offline-First Care Coordination

const DB_NAME = 'phc_bridge_offline_db';
const DB_VERSION = 1;

export function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offline_queue')) {
        db.createObjectStore('offline_queue', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('cached_referrals')) {
        db.createObjectStore('cached_referrals', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('cached_patients')) {
        db.createObjectStore('cached_patients', { keyPath: 'id' });
      }
    };

    request.onsuccess = (event) => resolve(event.target.result);
    request.onerror = (event) => reject(event.target.error);
  });
}

export async function queueOfflineReferral(item) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('offline_queue', 'readwrite');
    const store = tx.objectStore('offline_queue');
    const record = {
      ...item,
      id: item.id || `OFFLINE-${Date.now()}-${Math.random().toString(36).substr(2, 5).toUpperCase()}`,
      queued_at: new Date().toISOString()
    };
    const req = store.put(record);
    req.onsuccess = () => resolve(record);
    req.onerror = () => reject(req.error);
  });
}

export async function getOfflineQueue() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('offline_queue', 'readonly');
    const store = tx.objectStore('offline_queue');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

export async function clearOfflineQueue() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('offline_queue', 'readwrite');
    const store = tx.objectStore('offline_queue');
    const req = store.clear();
    req.onsuccess = () => resolve(true);
    req.onerror = () => reject(req.error);
  });
}

export async function cacheReferrals(referrals) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('cached_referrals', 'readwrite');
    const store = tx.objectStore('cached_referrals');
    referrals.forEach(r => store.put(r));
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
  });
}

export async function getCachedReferrals() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('cached_referrals', 'readonly');
    const store = tx.objectStore('cached_referrals');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}
