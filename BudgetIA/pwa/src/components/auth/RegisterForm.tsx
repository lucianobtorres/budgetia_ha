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
                <h2 className="mt-6 text-center text-3xl font-extrabold text-text-primary">
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
                type="text"
                required
                className="py-3 px-4"
                placeholder="Usuário (Login)"
                variant="glass"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
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
