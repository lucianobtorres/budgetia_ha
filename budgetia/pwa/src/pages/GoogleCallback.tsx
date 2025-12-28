import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export default function GoogleCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const processed = useRef(false); // Prevents double execution in Restricted Mode

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    console.log("[GoogleCallback] Code present:", !!code);
    console.log("[GoogleCallback] Error:", error);

    if (error) {
      alert(`Erro na autenticação Google: ${error}`);
      navigate('/onboarding');
      return;
    }

    if (code) {
      // Retorna para o onboarding passando o código via state do router
      // Isso evita expor o código na URL e permite que o Onboarding.tsx o processe
      navigate('/onboarding', { 
        replace: true,
        state: { 
          googleAuthCode: code,
          googleAuthState: state
        }
      });
    } else {
      console.warn("Callback sem código. Redirecionando para onboarding.");
      navigate('/onboarding', { replace: true });
    }
  }, [searchParams, navigate]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mb-4"></div>
      <p className="text-gray-400">Processando autenticação do Google...</p>
    </div>
  );
}
