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
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPass, setConfirmPass] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!name || !email || !username || !password || !confirmPass) {
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
            await AuthService.register(name, email, username, password);
            
            // Auto login after register
            const loginData = await AuthService.login(username, password);
            onLogin(loginData.user.username);
            
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Falha no registro");
        } finally {
            setLoading(false);
        }
    };

    return (
         <form className="mt-8 space-y-4" onSubmit={handleRegister}>
            {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-sm p-3 rounded-lg text-center">
                    {error}
                </div>
            )}
            
            <Input
                type="text"
                required
                className="py-3 px-4"
                placeholder="Nome Completo"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            
            <Input
                type="email"
                required
                className="py-3 px-4"
                placeholder="E-mail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />

            <Input
                type="text"
                required
                className="py-3 px-4"
                placeholder="Usuário (Login)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
            />

            <Input
                type="password"
                required
                className="py-3 px-4"
                placeholder="Senha (mín. 6)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />

            <Input
                type="password"
                required
                className="py-3 px-4"
                placeholder="Confirmar Senha"
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
