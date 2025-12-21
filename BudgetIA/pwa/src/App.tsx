import { useState, useEffect } from "react";
import { Routes, Route, useNavigate, useLocation, Navigate } from "react-router-dom";
import { Layout } from "./layouts/Layout";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Profile from "./pages/Profile";
import Transactions from "./pages/Transactions";
import Budgets from "./pages/Budgets";
import Notifications from "./pages/Notifications";
import Onboarding from "./pages/Onboarding";
import GoogleCallback from "./pages/GoogleCallback";
import { User, Lock, ArrowRight } from "lucide-react";

function LoginScreen({ onLogin }: { onLogin: (user: string) => void }) {
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

function LoginForm({ onLogin }: { onLogin: (user: string) => void }) {
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
            const res = await fetch('http://localhost:8000/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (res.ok) {
                const data = await res.json();
                onLogin(data.user.username);
            } else {
                const err = await res.json();
                setError(err.detail || "Falha no login");
            }
        } catch (err) {
            setError("Erro de conexão com o servidor");
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
                    <div className="relative">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <User className="h-5 w-5 text-gray-500" aria-hidden="true" />
                        </div>
                        <input
                            id="username"
                            name="username"
                            type="text"
                            required
                            className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 pl-10 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                            placeholder="Usuário"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                </div>
                <div>
                    <label htmlFor="password" className="sr-only">Senha</label>
                    <div className="relative">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <Lock className="h-5 w-5 text-gray-500" aria-hidden="true" />
                        </div>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            required
                            className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 pl-10 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                            placeholder="Senha"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            <button
                type="submit"
                disabled={loading}
                className="group relative flex w-full justify-center rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all disabled:opacity-50"
            >
                {loading ? "Entrando..." : (
                    <>
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                            <ArrowRight className="h-5 w-5 text-emerald-300 group-hover:text-emerald-100" />
                        </span>
                        Entrar
                    </>
                )}
            </button>
        </form>
    );
}

function RegisterForm({ onLogin }: { onLogin: (user: string) => void }) {
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
            const res = await fetch('http://localhost:8000/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, username, password })
            });

            if (res.ok) {
                 // Auto login after register
                 const loginRes = await fetch('http://localhost:8000/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                if (loginRes.ok) {
                    const data = await loginRes.json();
                    onLogin(data.user.username);
                } else {
                     // Should not happen, but fallback
                    window.location.reload();
                }

            } else {
                const err = await res.json();
                setError(err.detail || "Falha no registro");
            }
        } catch (err) {
            setError("Erro de conexão com o servidor");
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
            
            <input
                type="text"
                required
                className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 px-4 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                placeholder="Nome Completo"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            
            <input
                type="email"
                required
                className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 px-4 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                placeholder="E-mail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />

            <input
                type="text"
                required
                className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 px-4 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                placeholder="Usuário (Login)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
            />

            <input
                type="password"
                required
                className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 px-4 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                placeholder="Senha (mín. 6)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />

            <input
                type="password"
                required
                className="block w-full rounded-lg border border-gray-700 bg-gray-950 py-3 px-4 text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 sm:text-sm"
                placeholder="Confirmar Senha"
                value={confirmPass}
                onChange={(e) => setConfirmPass(e.target.value)}
            />

            <button
                type="submit"
                disabled={loading}
                className="group w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all disabled:opacity-50"
            >
                {loading ? "Criando Conta..." : "Criar Conta"}
            </button>
        </form>
    );
}


function App() {
  const [user, setUser] = useState<string | null>(localStorage.getItem('budgetia_user_id'));
  const [onboardingStatus, setOnboardingStatus] = useState<string>("UNKNOWN");
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = (username: string) => {
      localStorage.setItem('budgetia_user_id', username);
      setUser(username);
  };

  useEffect(() => {
      if (user) {
          // Check onboarding status
          const checkOnboarding = async () => {
              try {
                  const res = await fetch('http://localhost:8000/onboarding/state', {
                      headers: { 'X-User-ID': user }
                  });
                  const data = await res.json();
                  setOnboardingStatus(data.state); // Set onboarding status
                  
                  // If not complete and not already on onboarding page
                  if (data.state !== "COMPLETE") {
                      // Avoid redirect loop if already on onboarding or callback
                      if (location.pathname !== "/onboarding" && location.pathname !== "/google-callback") {
                          navigate("/onboarding");
                      }
                  }
              } catch (e) {
                  console.error("Failed to check onboarding status", e);
              }
          };
          checkOnboarding();
      }
  }, [user, navigate, location.pathname]);

  if (!user) {
      return (
          <>
            <LoginScreen onLogin={handleLogin} />
             {/* Render RegisterForm logic implicitly inside LoginScreen */}
          </>
      );
  }

  return (
    <Routes>
      <Route path="/onboarding" element={
          onboardingStatus === 'COMPLETE' ? <Navigate to="/" replace /> : <Onboarding />
      } />
      <Route path="/google-callback" element={<GoogleCallback />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<Chat />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="budgets" element={<Budgets />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="profile" element={<Profile />} />
      </Route>
    </Routes>
  );
}

export default App;


