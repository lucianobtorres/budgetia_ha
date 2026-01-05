import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { AuthService } from '../services/auth';
import { Button } from '../components/ui/Button';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Token de verificação inválido ou ausente.');
      return;
    }

    AuthService.verifyEmail(token)
      .then(() => {
        setStatus('success');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.message || "Erro ao verificar email. O link pode ter expirado.");
      });
  }, [token]);

  return (
    <div className="min-h-screen w-full bg-gray-950 flex items-center justify-center p-4 relative overflow-hidden selection:bg-emerald-500/30">
        {/* Background Gradients */}
        <div className="absolute inset-0 pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/40 via-gray-900 to-black opacity-90"></div>
                <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        </div>

      <div className="w-full max-w-md relative z-10 flex flex-col items-center gap-8">
        
        {/* Logo */}
        <div className="flex items-center gap-3">
             <div className="relative h-12 w-12 overflow-hidden rounded-xl shadow-black/50 shadow-md ring-1 ring-white/20 shrink-0 group">
                 <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                 <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover" />
            </div>
            <div className="text-2xl font-bold tracking-tight leading-normal whitespace-nowrap drop-shadow-sm flex items-center">
                <span className="text-transparent bg-clip-text bg-gradient-to-br from-white to-gray-400">Budget</span>
                <span className="text-emerald-400 drop-shadow-glow">IA</span>
            </div>
        </div>

        <div className="w-full bg-gray-900/50 p-8 rounded-3xl border border-white/10 backdrop-blur-xl text-center shadow-2xl shadow-emerald-900/20">
            {status === 'loading' && (
            <div className="flex flex-col items-center py-6">
                <Loader2 className="h-12 w-12 text-emerald-500 animate-spin mb-6" />
                <h2 className="text-xl font-bold text-white">Verificando Email...</h2>
                <p className="text-gray-400 text-sm mt-2">Aguarde um momento.</p>
            </div>
            )}

            {status === 'success' && (
            <div className="flex flex-col items-center py-4">
                <div className="h-16 w-16 bg-emerald-500/10 rounded-full flex items-center justify-center mb-6 ring-1 ring-emerald-500/20">
                    <CheckCircle className="h-8 w-8 text-emerald-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Email Verificado!</h2>
                <p className="text-gray-400 mb-8 max-w-[80%] mx-auto">Sua conta foi ativada com sucesso. Você já pode acessar o sistema.</p>
                <Button 
                    onClick={() => navigate('/login')} 
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                >
                    Ir para Login
                </Button>
            </div>
            )}

            {status === 'error' && (
            <div className="flex flex-col items-center py-4">
                <div className="h-16 w-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6 ring-1 ring-red-500/20">
                     <XCircle className="h-8 w-8 text-red-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Falha na Verificação</h2>
                <p className="text-red-300/80 mb-8 text-sm bg-red-950/30 px-4 py-2 rounded-lg border border-red-500/10">{message}</p>
                <Button onClick={() => navigate('/login')} variant="outline" className="w-full border-white/10 hover:bg-white/5 mb-4">
                    Voltar ao Login
                </Button>
                
                <div className="pt-4 border-t border-white/5 w-full">
                    <p className="text-gray-500 text-xs mb-3">O link expirou?</p>
                     <Button 
                        onClick={async () => {
                            const email = prompt("Confirme seu email para reenvio:");
                            if(email) {
                                try {
                                    await AuthService.resendVerification(email);
                                    alert("Novo link enviado! Verifique sua caixa de entrada.");
                                    navigate('/login');
                                } catch(e: any) {
                                    alert(e.message || "Erro ao reenviar.");
                                }
                            }
                        }}
                        size="sm"
                        variant="ghost" 
                        className="text-emerald-400 hover:text-emerald-300 w-full"
                    >
                        Reenviar Email de Verificação
                    </Button>
                </div>
            </div>
            )}
        </div>
        
        <p className="text-gray-600 text-xs">© 2026 BudgetIA Security</p>
      </div>
    </div>
  );
}
