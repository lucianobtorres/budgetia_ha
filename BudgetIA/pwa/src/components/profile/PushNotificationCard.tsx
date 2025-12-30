import { Bell, BellOff, Loader2 } from 'lucide-react';
import { usePushNotifications } from '../../hooks/usePushNotifications';
import { Button } from '../ui/Button';

export function PushNotificationCard() {
  const { isSubscribed, loading, enablePush, disablePush, permission } = usePushNotifications();

  return (
    <div className="bg-surface-card/40 backdrop-blur border border-border/50 rounded-2xl p-5 hover:border-primary/20 transition-all group">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`h-12 w-12 rounded-xl flex items-center justify-center transition-colors ${isSubscribed ? 'bg-primary/20 text-primary-light' : 'bg-surface-hover/50 text-text-secondary'}`}>
            {loading ? <Loader2 className="animate-spin" size={24} /> : (
                isSubscribed ? <Bell size={24} /> : <BellOff size={24} />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Notificações Push</h3>
            <p className="text-sm text-text-muted">
              {isSubscribed 
                ? "Ativo neste dispositivo" 
                : "Receba alertas mesmo com o app fechado"}
            </p>
            {permission === 'denied' && (
                <p className="text-xs text-danger mt-1">⚠️ Permissão bloqueada no navegador.</p>
            )}
          </div>
        </div>

        <Button
          onClick={isSubscribed ? disablePush : enablePush}
          disabled={loading || permission === 'denied'}
          variant={isSubscribed ? "danger" : "primary"}
          isLoading={loading}
          className="px-4 py-2" // Button component handles size, but we can keep padding if needed or rely on default size="md"
        >
          {isSubscribed ? 'Desativar' : 'Ativar'}
        </Button>
      </div>
    </div>
  );
}
