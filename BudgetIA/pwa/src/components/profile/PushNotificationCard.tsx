import { Bell, BellOff, Loader2 } from 'lucide-react';
import { usePushNotifications } from '../../hooks/usePushNotifications';
import { Button } from '../ui/Button';

export function PushNotificationCard() {
  const { isSubscribed, loading, enablePush, disablePush, permission } = usePushNotifications();

  return (
    <div className="bg-gray-800/40 backdrop-blur border border-gray-700/50 rounded-2xl p-5 hover:border-emerald-500/20 transition-all group">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`h-12 w-12 rounded-xl flex items-center justify-center transition-colors ${isSubscribed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700/50 text-gray-400'}`}>
            {loading ? <Loader2 className="animate-spin" size={24} /> : (
                isSubscribed ? <Bell size={24} /> : <BellOff size={24} />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Notificações Push</h3>
            <p className="text-sm text-gray-400">
              {isSubscribed 
                ? "Ativo neste dispositivo" 
                : "Receba alertas mesmo com o app fechado"}
            </p>
            {permission === 'denied' && (
                <p className="text-xs text-red-400 mt-1">⚠️ Permissão bloqueada no navegador.</p>
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
