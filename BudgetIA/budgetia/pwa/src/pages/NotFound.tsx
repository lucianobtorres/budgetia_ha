import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { AlertCircle } from "lucide-react";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center bg-gray-950">
      <div className="p-4 bg-gray-900 rounded-full mb-6 relative">
          <div className="absolute inset-0 bg-red-500/10 rounded-full animate-pulse" />
          <AlertCircle className="w-12 h-12 text-red-400 relative z-10" />
      </div>
      
      <h1 className="text-3xl font-bold text-white mb-2">404</h1>
      <h2 className="text-xl font-medium text-gray-300 mb-4">Página não encontrada</h2>
      
      <p className="text-gray-400 max-w-sm mb-8 leading-relaxed">
        Opa! Parece que o link que você tentou acessar não existe ou foi removido.
      </p>

      <Button onClick={() => navigate("/")} variant="primary" size="lg" className="w-full max-w-xs shadow-lg shadow-emerald-500/10">
        Voltar para os Trilhos
      </Button>
    </div>
  );
}
