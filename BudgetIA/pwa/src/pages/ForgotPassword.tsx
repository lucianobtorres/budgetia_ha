import { useState } from 'react';
import { AuthService } from '../services/auth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await AuthService.forgotPassword(email);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Erro ao enviar email.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-8 bg-gray-900/50 p-8 rounded-2xl border border-white/10 backdrop-blur-xl">
          <div className="text-center">
             <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
             <h2 className="mt-4 text-3xl font-bold text-white">Email Enviado!</h2>
             <p className="mt-2 text-gray-400">
               Se o email <b>{email}</b> estiver cadastrado, você receberá um link para redefinir sua senha em instantes.
             </p>
          </div>
          
          <div className="mt-6">
            <Link to="/login">
              <Button className="w-full" variant="outline">Voltar ao Login</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
       <div className="w-full max-w-md space-y-8 bg-gray-900/50 p-8 rounded-2xl border border-white/10 backdrop-blur-xl">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-white">Recuperar Senha</h2>
            <p className="mt-2 text-gray-400">Digite seu email para receber um link de redefinição.</p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  type="email"
                  required
                  className="pl-10 py-3"
                  placeholder="Seu email cadastrado"
                  variant="glass"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
            </div>

            <Button
              type="submit"
              disabled={loading}
              isLoading={loading}
              className="w-full"
            >
              Enviar Link
            </Button>

            <div className="text-center">
              <Link to="/login" className="text-sm text-gray-400 hover:text-primary flex items-center justify-center gap-2">
                 <ArrowLeft className="w-4 h-4" /> Voltar ao Login
              </Link>
            </div>
          </form>
       </div>
    </div>
  );
}
