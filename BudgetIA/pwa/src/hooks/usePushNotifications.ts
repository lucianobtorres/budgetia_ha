import { useState, useEffect } from 'react';
import { PushService } from '../services/push-service';
import { toast } from 'sonner';
import { VAPID_PUBLIC_KEY as VAPID_FALLBACK } from '../utils/constants';

// You should put this in your .env as VITE_VAPID_PUBLIC_KEY
// For now, if it's missing, we can warn.
const VAPID_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY || VAPID_FALLBACK;

export function usePushNotifications() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const perm = await PushService.getPermissionStatus();
      setPermission(perm);

      const sub = await PushService.getSubscription();
      setIsSubscribed(!!sub);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const enablePush = async () => {
    if (!VAPID_KEY) {
      toast.error('Chave VAPID não configurada no sistema.');
      console.error("Missing VITE_VAPID_PUBLIC_KEY");
      return;
    }

    setLoading(true);
    const success = await PushService.subscribe(VAPID_KEY);
    if (success) {
      setIsSubscribed(true);
      setPermission('granted');
      toast.success('Notificações ativadas! 🚀');
    } else {
      toast.error('Erro ao ativar notificações. Verifique as permissões.');
    }
    setLoading(false);
  };

  const disablePush = async () => {
    setLoading(true);
    const success = await PushService.unsubscribe();
    if (success) {
      setIsSubscribed(false);
      toast.info('Notificações desativadas.');
    }
    setLoading(false);
  };

  return {
    isSubscribed,
    permission,
    loading,
    enablePush,
    disablePush
  };
}
