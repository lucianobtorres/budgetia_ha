import { useState } from 'react';
import { User, Lock, ArrowRight } from 'lucide-react';
import { AuthService } from '../../services/auth';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface LoginFormProps {
    onLogin: (user: string) => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        
        if (!username.trim() || !password.trim()) {
            setError("Preencha todos os campos");
            return;
        }

        setLoading(true);
        try {
            const data = await AuthService.login(username, password);
            onLogin(data.user.username);
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Erro de conexão com o servidor.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-sm p-3 rounded-lg text-center">
                    {error}
                </div>
            )}
            <div className="space-y-4">
                <div>
                    <label htmlFor="username" className="sr-only">ID de Usuário</label>
                    <Input
                        id="username"
                        name="username"
                        type="text"
                        required
                        icon={User}
                        placeholder="Usuário"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="password" className="sr-only">Senha</label>
                    <Input
                        id="password"
                        name="password"
                        type="password"
                        required
                        icon={Lock}
                        placeholder="Senha"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
            </div>

            <Button
                type="submit"
                disabled={loading}
                isLoading={loading}
                className="w-full"
                icon={!loading ? ArrowRight : undefined}
            >
                Entrar
            </Button>
        </form>
    );
}
