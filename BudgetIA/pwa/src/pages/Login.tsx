import { useState } from 'react';
import { Lock } from 'lucide-react';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';

interface LoginProps {
    onLogin: (user: string) => void;
}

export default function Login({ onLogin }: LoginProps) {
    const [isRegistering, setIsRegistering] = useState(false);

    return (
        <div className="flex h-screen items-center justify-center bg-gray-950 p-4">
            <div className="w-full max-w-md space-y-8 bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-xl">
                <div className="text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 mb-4">
                        <Lock className="h-8 w-8 text-emerald-500" />
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Bem-vindo ao BudgetIA</h2>
                    <p className="mt-2 text-sm text-gray-400">
                        {isRegistering ? "Crie sua conta" : "Entre com suas credenciais"}
                    </p>
                </div>

                {isRegistering ? <RegisterForm onLogin={onLogin} /> : <LoginForm onLogin={onLogin} />}

                <div className="text-center">
                    <button
                        onClick={() => setIsRegistering(!isRegistering)}
                        className="text-emerald-400 hover:text-emerald-300 text-sm font-medium hover:underline"
                    >
                        {isRegistering ? "Já tem conta? Entre aqui." : "Não tem conta? Crie uma agora."}
                    </button>
                </div>
            </div>
        </div>
    );
}
