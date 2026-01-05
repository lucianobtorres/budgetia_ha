import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, Sparkles, TrendingUp, ShieldCheck } from 'lucide-react';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';

interface LoginProps {
    onLogin: (user: string) => void;
}
export default function Login({ onLogin }: LoginProps) {
    const [isRegistering, setIsRegistering] = useState(false);
    const navigate = useNavigate();

    return (
        <div className="flex min-h-screen w-full bg-gray-950">
            {/* Left Side - Brand & Marketing (Hidden on mobile) */}
            <div className="hidden lg:flex w-1/2 relative bg-emerald-900 overflow-hidden flex-col justify-between p-12">
                {/* Background Decoration */}
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-900 via-gray-900 to-black opacity-90"></div>
                <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl"></div>
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>

                {/* Header Logo */}
                <Link 
                    to="/landing"
                    className="relative z-10 flex items-center gap-4 cursor-pointer hover:opacity-80 transition-opacity"
                >
                     <div className="relative h-16 w-16 overflow-hidden rounded-2xl shadow-black/50 shadow-md ring-1 ring-white/20 shrink-0 group">
                         <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                         <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover transform group-hover:scale-105 transition-transform duration-500" />
                    </div>
                    <div className="text-4xl font-bold tracking-tight leading-normal whitespace-nowrap drop-shadow-sm flex items-center py-1">
                        <span className="text-transparent bg-clip-text bg-gradient-to-br from-white to-gray-400">Budget</span>
                        <span className="text-emerald-400 drop-shadow-glow">IA</span>
                    </div>
                </Link>

                {/* Hero Content */}
                <div className="relative z-10 space-y-6 max-w-lg">
                    <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
                        Domine suas finanças com Inteligência Artificial
                    </h1>
                    <p className="text-lg text-emerald-100/80 leading-relaxed">
                        Junte-se a milhares de usuários que estão transformando sua vida financeira. 
                        Nossa IA analisa seus gastos, prevê tendências e ajuda você a tomar as melhores decisões.
                    </p>
                    
                    <div className="flex gap-6 pt-4">
                        <div className="flex items-center gap-2 text-emerald-200/90">
                            <Sparkles className="h-5 w-5 text-emerald-400" />
                            <span className="text-sm font-medium">Insights IA</span>
                        </div>
                        <div className="flex items-center gap-2 text-emerald-200/90">
                            <ShieldCheck className="h-5 w-5 text-emerald-400" />
                            <span className="text-sm font-medium">100% Seguro</span>
                        </div>
                    </div>
                </div>

                {/* Footer Quote */}
                <div className="relative z-10">
                    <blockquote className="border-l-2 border-emerald-500 pl-4 py-1">
                        <p className="text-emerald-100/60 italic text-sm">
                            "A melhor maneira de prever o futuro é criá-lo. O BudgetIA me ajudou a criar o futuro financeiro que eu sempre quis."
                        </p>
                    </blockquote>
                </div>
            </div>

            {/* Right Side - Login Form */}
            <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-20 relative z-20">
                {/* Mobile Brand Header */}
                <div className="flex flex-row items-center justify-center gap-3 mb-8 lg:hidden animate-in fade-in slide-in-from-top-4 duration-700">
                     <div className="relative h-16 w-16 overflow-hidden rounded-xl shadow-black/50 shadow-md ring-1 ring-white/20 shrink-0">
                        <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover" />
                    </div>
                    <div className="text-2xl font-bold tracking-tight leading-normal whitespace-nowrap drop-shadow-sm flex items-center">
                        <span className="text-transparent bg-clip-text bg-gradient-to-br from-white to-gray-400">Budget</span>
                        <span className="text-emerald-400 drop-shadow-glow">IA</span>
                    </div>
                </div>

                <div className="w-full max-w-sm space-y-8">
                   <div className="text-center lg:text-left">
                        <h2 className="text-3xl font-bold tracking-tight text-white">
                             {isRegistering ? "Crie sua conta" : "Bem-vindo de volta"}
                        </h2>
                        <p className="mt-2 text-sm text-gray-400">
                             {isRegistering ? "Comece sua jornada financeira hoje" : "Entre com suas credenciais para acessar"}
                        </p>
                    </div>

                    <div className="lg:bg-transparent lg:border-none p-0">
                        {isRegistering ? <RegisterForm onLogin={onLogin} /> : <LoginForm onLogin={onLogin} />}
                    </div>

                    <div className="text-center">
                        <p className="text-sm text-gray-400 mb-2">
                             {isRegistering ? "Já tem uma conta?" : "Ainda não tem uma conta?"}
                        </p>
                        <button
                            onClick={() => setIsRegistering(!isRegistering)}
                            className="text-emerald-400 hover:text-emerald-300 text-sm font-semibold hover:underline transition-colors"
                        >
                            {isRegistering ? "Entre com suas credenciais" : "Crie uma conta gratuitamente"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
