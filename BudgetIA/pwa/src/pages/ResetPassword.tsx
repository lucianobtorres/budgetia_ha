import { useState, useEffect } from 'react';
import { AuthService } from '../services/auth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Lock, CheckCircle, AlertTriangle } from 'lucide-react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
        setError("Token inválido ou não encontrado.");
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!token) return;

    if (password !== confirmPass) {
        setError("As senhas não coincidem.");
        return;
    }

    if (password.length < 6) {
        setError("A senha deve ter no mínimo 6 caracteres.");
        return;
    }

    setLoading(true);

    try {
      await AuthService.resetPassword(token, password);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: any) {
      setError(err.message || "Erro ao redefinir senha.");
    } finally {
      setLoading(false);
    }
  };

  const Background = () => (
        <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/40 via-gray-900 to-black opacity-90"></div>
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"></div>
        </div>
  );

  const Logo = () => (
        <div className="flex items-center gap-3 mb-8">
             <div className="relative h-12 w-12 overflow-hidden rounded-xl shadow-black/50 shadow-md ring-1 ring-white/20 shrink-0 group">
                 <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                 <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover" />
            </div>
            <div className="text-2xl font-bold tracking-tight leading-normal whitespace-nowrap drop-shadow-sm flex items-center">
                <span className="text-transparent bg-clip-text bg-gradient-to-br from-white to-gray-400">Budget</span>
                <span className="text-emerald-400 drop-shadow-glow">IA</span>
            </div>
        </div>
  );

  if (success) {
    return (
      <div className="min-h-screen w-full bg-gray-950 flex items-center justify-center p-4 relative overflow-hidden">
        <Background />
        <div className="w-full max-w-md relative z-10 flex flex-col items-center">
             <Logo />
             <div className="w-full bg-gray-900/50 p-8 rounded-3xl border border-white/10 backdrop-blur-xl text-center shadow-2xl">
                 <div className="h-16 w-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 ring-1 ring-emerald-500/20">
                    <CheckCircle className="h-8 w-8 text-emerald-500" />
                 </div>
                 <h2 className="text-2xl font-bold text-white mb-2">Senha Atualizada!</h2>
                 <p className="text-gray-400 mb-6">
                   Sua senha foi redefinida com sucesso. <br/> Você será redirecionado em instantes...
                 </p>
                 <Button onClick={() => navigate('/login')} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white" variant="outline">
                    Fazer Login Agora
                 </Button>
            </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gray-950 flex items-center justify-center p-4 relative overflow-hidden">
        <Background />
       <div className="w-full max-w-md relative z-10 flex flex-col items-center">
          <Logo />
          <div className="w-full bg-gray-900/50 p-8 rounded-3xl border border-white/10 backdrop-blur-xl shadow-2xl">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-white">Nova Senha</h2>
                <p className="mt-2 text-sm text-gray-400">Crie uma senha forte para proteger sua conta.</p>
              </div>

              <form className="space-y-6" onSubmit={handleSubmit}>
                {error && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs flex items-center gap-2 justify-center">
                    <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
                  </div>
                )}

                <div className="space-y-4">
                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Lock className="h-5 w-5 text-gray-500 group-focus-within:text-emerald-400 transition-colors" />
                        </div>
                        <Input
                          type="password"
                          required
                          className="pl-10 py-6 bg-black/20 border-white/10 focus:border-emerald-500/50 focus:ring-emerald-500/20 transition-all rounded-xl"
                          placeholder="Nova Senha"
                          variant="glass"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Lock className="h-5 w-5 text-gray-500 group-focus-within:text-emerald-400 transition-colors" />
                        </div>
                        <Input
                          type="password"
                          required
                          className="pl-10 py-6 bg-black/20 border-white/10 focus:border-emerald-500/50 focus:ring-emerald-500/20 transition-all rounded-xl"
                          placeholder="Confirmar Senha"
                          variant="glass"
                          value={confirmPass}
                          onChange={(e) => setConfirmPass(e.target.value)}
                        />
                    </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading || !token}
                  isLoading={loading}
                  className="w-full py-6 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold shadow-lg shadow-emerald-500/20"
                >
                  Redefinir Senha
                </Button>
              </form>
           </div>
           <p className="text-gray-600 text-xs mt-8">© 2026 BudgetIA Security</p>
       </div>
    </div>
  );
}
