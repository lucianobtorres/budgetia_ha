import { useState } from 'react';
import { AuthService } from '../../services/auth';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface RegisterFormProps {
    onLogin: (user: string) => void;
}

export function RegisterForm({ onLogin }: RegisterFormProps) {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPass, setConfirmPass] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!name || !email || !password || !confirmPass) {
            setError("Preencha todos os campos");
            return;
        }

        if (password !== confirmPass) {
            setError("As senhas não coincidem");
            return;
        }
        
        if (password.length < 6) {
            setError("Senha deve ter no mínimo 6 caracteres");
            return;
        }

        setLoading(true);
        try {
            // Register creates user and returns the auto-generated username
            await AuthService.register(name, email, password);
            
            // Show success message instead of auto-login
            setError(""); // Clean any previous error
            
            // Success State UI (We replace the form content)
            const successContent = (
                <div className="text-center py-6 animate-in fade-in zoom-in duration-300">
                    <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/30">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 17a2 2 0 0 1-2 2h-2"/><path d="M4 17a2 2 0 0 0 2 2h2"/><path d="M9 17h6"/><path d="M9 13h6"/><path d="M11 9h2"/><path d="M22 6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h20"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Conta Criada!</h3>
                    <p className="text-gray-300 text-sm mb-6">
                        Enviamos um link de confirmação para <strong>{email}</strong>. <br/>
                        Verifique sua caixa de entrada (e spam) para ativar sua conta.
                    </p>
                    <Button 
                        onClick={() => window.location.reload()} // Go back to login "mode"
                        className="w-full bg-white/10 hover:bg-white/20 text-white"
                        variant="outline"
                    >
                        Voltar para Login
                    </Button>
                </div>
            );
            
            // Render the success content via a callback or state in the parent? 
            // Since this component is inside the Login page, we can assume we want to stay here.
            // Let's hide the form and show this.
            setSuccessMode(true);
            return;

        } catch (err: any) {
            console.error(err);
            setError(err.message || "Falha no registro");
        } finally {
            setLoading(false);
        }
    };

    const [successMode, setSuccessMode] = useState(false);

    if (successMode) {
        return (
            <div className="mt-8 space-y-4">
                 <div className="text-center py-6 animate-in fade-in zoom-in duration-300">
                    <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/30">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 17a2 2 0 0 1-2 2h-2"/><path d="M4 17a2 2 0 0 0 2 2h2"/><path d="M9 17h6"/><path d="M9 13h6"/><path d="M11 9h2"/><path d="M22 6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h20"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Conta Criada!</h3>
                    <p className="text-gray-300 text-sm mb-6">
                        Enviamos um link de confirmação para <span className="text-emerald-400">{email}</span>. <br/>
                        Verifique sua caixa de entrada para ativar sua conta.
                    </p>
                    <Button 
                        onClick={() => window.location.reload()} 
                        className="w-full"
                    >
                        Voltar para Login
                    </Button>
                </div>
            </div>
        )
    }

    return (
         <form className="mt-8 space-y-4" onSubmit={handleRegister}>
            {error && (
                <h2 className="mt-6 text-center text-sm font-bold text-red-500">
                    {error}
                </h2>
            )}
            
            <Input
                type="text"
                required
                className="py-3 px-4"
                placeholder="Nome Completo"
                variant="glass"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            
            <Input
                type="email"
                required
                className="py-3 px-4"
                placeholder="E-mail"
                variant="glass"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />

            <Input
                type="password"
                required
                className="py-3 px-4"
                placeholder="Senha (mín. 6)"
                variant="glass"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />

            <Input
                type="password"
                required
                className="py-3 px-4"
                placeholder="Confirmar Senha"
                variant="glass"
                value={confirmPass}
                onChange={(e) => setConfirmPass(e.target.value)}
            />

            <Button
                type="submit"
                disabled={loading}
                isLoading={loading}
                className="w-full"
            >
                Criar Conta
            </Button>
        </form>
    );
}
