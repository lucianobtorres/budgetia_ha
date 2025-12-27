import { fetchAPI } from './api';

// Helper to convert VAPID key
function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const PushService = {
  /**
   * Checks if Push is supported and permission status
   */
  async getPermissionStatus(): Promise<NotificationPermission> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      return 'denied'; // Not supported, treat as denied
    }
    return Notification.permission;
  },

  /**
   * Request permission and Subscribe to Push
   */
  async subscribe(vapidPublicKey: string): Promise<boolean> {
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        throw new Error('Permission denied');
      }

      // Wait for SW to be ready
      const registration = await navigator.serviceWorker.ready;

      // Subscribe
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      });

      // Send to Backend
      // We parse the subscription to get keys easily
      const subJson = subscription.toJSON();
      
      await fetchAPI('/notifications/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: subJson.endpoint,
          keys: subJson.keys // { p256dh, auth }
        })
      });

      return true;

    } catch (error) {
      console.error('Failed to subscribe to push:', error);
      return false;
    }
  },

  /**
   * Unsubscribe
   */
  async unsubscribe(): Promise<boolean> {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      
      if (subscription) {
        // Unsubscribe from backend first (best effort)
        await fetchAPI('/notifications/unsubscribe', {
            method: 'POST',
            body: JSON.stringify({ endpoint: subscription.endpoint }) // Usually query param or body? Let's assume body or query based on router
        }).catch(err => console.warn("Backend unsubscribe failed", err));

        // Unsubscribe from browser
        await subscription.unsubscribe();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to unsubscribe:', error);
      return false;
    }
  },

  /**
   * Check if currently subscribed
   */
  async getSubscription(): Promise<PushSubscription | null> {
    const registration = await navigator.serviceWorker.ready;
    return registration.pushManager.getSubscription();
  }
};
