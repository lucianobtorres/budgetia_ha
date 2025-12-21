import { useState, useEffect, useRef } from "react";
import { Send, Upload, Cloud, ArrowRight, ShieldCheck, FileSpreadsheet, Play, CheckCircle } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

interface Message {
    sender: "agent" | "user";
    text: string;
}

interface OnboardingStateData {
    state: string;
    progress: number;
    ui_options: string[];
    initial_message: string | null;
}

export default function Onboarding() {
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [uiOptions, setUiOptions] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        checkState();
    }, []);

    const checkState = async () => {
        try {
            const userId = localStorage.getItem('budgetia_user_id') || "default_user";
            const res = await fetch('http://localhost:8000/onboarding/state', {
                headers: { 'X-User-ID': userId }
            });
            const data: OnboardingStateData = await res.json();
            
            if (data.state === "COMPLETE") {
                navigate("/");
                return;
            }

            setUiOptions(data.ui_options);
            
            // If there's an initial message and chat is empty, show it
            if (data.initial_message && messages.length === 0) {
                 setMessages([{ sender: "agent", text: data.initial_message }]);
            } else if (messages.length === 0) {
                 // Trigger chat to get greeting if needed (or just wait)
                 // Actually, the API's get_initial_message handles the auto-greeting logic
                 // If it returned null, maybe we should just say hi?
                 // But wait, get_initial_message only returns IF it generated one.
                 // If we reload the page, we might lose history if we don't fetch it.
                 // The API doesn't expose history yet. Ideally it should.
                 // For now, let's assume session persistence. 
            }
        } catch (e) {
            console.error("Failed to check state", e);
        }
    };



    // --- GOOGLE SHEETS SELECTION ---
    interface GoogleFile {
        id: string;
        name: string;
        url: string;
    }
    const [googleFiles, setGoogleFiles] = useState<GoogleFile[] | null>(null);

    const handleApiResponse = (data: any) => {
        // 1. Add message
        // Hide technical tags from user
        const cleanText = data.message.replace(/\[UI_ACTION:.*?\]/g, "").trim();
        if (cleanText) {
            setMessages(prev => [...prev, { sender: "agent", text: cleanText }]);
        }

        // 2. Update Options
        setUiOptions(data.ui_options);

        // 3. Check for Google Files
        if (data.google_files_list && data.google_files_list.length > 0) {
            // Map backend keys to frontend interface
            const mappedFiles = data.google_files_list.map((f: any) => ({
                id: f.id,
                name: f.name,
                url: f.webViewLink, 
                icon: f.iconLink
            }));
            console.log("Arquivos recebidos:", mappedFiles);
            setGoogleFiles(mappedFiles);
        }

        // 4. Check completion
        if (data.state === "COMPLETE") {
            setTimeout(() => navigate("/"), 2000);
        }
    };

    const selectGoogleFile = (file: GoogleFile) => {
        setGoogleFiles(null); // Close modal
        sendMessage(file.url); // Send URL to agent to finalize
    };

    const sendMessage = async (text: string) => {
        if (!text.trim()) return;
        
        const userId = localStorage.getItem('budgetia_user_id') || "default_user";
        const newMessages = [...messages, { sender: "user", text } as Message];
        setMessages(newMessages);
        setInputValue("");
        setLoading(true);

        try {
            const res = await fetch('http://localhost:8000/onboarding/chat', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-User-ID': userId
                },
                body: JSON.stringify({ text })
            });
            
            const data = await res.json();
            handleApiResponse(data);
            
        } catch (error) {
            setMessages(prev => [...prev, { sender: "agent", text: "Erro ao comunicar com o servidor. Tente novamente." }]);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const userId = localStorage.getItem('budgetia_user_id') || "default_user";
        const formData = new FormData();
        formData.append("file", file);

        try {
            setMessages(prev => [...prev, { sender: "user", text: `Enviando arquivo: ${file.name}...` }]);

            const res = await fetch('http://localhost:8000/onboarding/upload', {
                method: 'POST',
                headers: { 'X-User-ID': userId },
                body: formData
            });
            
            const data = await res.json();
            handleApiResponse(data);

        } catch (error) {
             setMessages(prev => [...prev, { sender: "agent", text: "Falha no upload." }]);
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    // NOVO: Lê estado passado pelo GoogleCallback
    const { state } = useLocation();

    useEffect(() => {
        if (state && (state as any).googleAuthCode) {
            const { googleAuthCode } = state as any;
            navigate(location.pathname, { replace: true, state: {} });
            sendGoogleAuthCode(googleAuthCode);
        }
    }, [state]);

    const sendGoogleAuthCode = async (code: string) => {
        const userId = localStorage.getItem('budgetia_user_id') || "default_user";
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/onboarding/google-auth', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-User-ID': userId
                },
                body: JSON.stringify({ 
                    code,
                    redirect_uri: "http://localhost:5173/google-callback"
                })
            });
            const data = await res.json();
            handleApiResponse(data);
            
        } catch (error) {
            setMessages(prev => [...prev, { sender: "agent", text: "Erro ao autenticar com Google." }]);
        } finally {
            setLoading(false);
        }
    }

    const startGoogleAuth = async () => {
        const userId = localStorage.getItem('budgetia_user_id') || "default_user";
        try {
            const redirectUri = encodeURIComponent("http://localhost:5173/google-callback");
            const res = await fetch(`http://localhost:8000/onboarding/google-auth-url?redirect_uri=${redirectUri}`, {
                headers: { 'X-User-ID': userId }
            });
            const data = await res.json();
            
            if (data.url) {
                window.location.href = data.url;
            } else {
                alert("Erro ao gerar URL de autenticação.");
            }
        } catch (error) {
            console.error("Erro ao iniciar auth Google", error);
            alert("Erro ao iniciar autenticação Google.");
        }
    };

    // Helper to map UI Options to Icons/Actions
    const renderOptionButton = (option: string) => {
        let icon = <ArrowRight className="w-4 h-4" />;
        let style = "bg-emerald-600 hover:bg-emerald-500 text-white";
        // Explicitly type onClick to allow both async and sync void functions
        let onClick: () => void | Promise<void> = () => sendMessage(option);

        if (option.includes("Upload") || option.includes("📤")) {
            icon = <Upload className="w-4 h-4" />;
            style = "bg-blue-600 hover:bg-blue-500 text-white";
            onClick = () => fileInputRef.current?.click();
        } else if (option.includes("Google") || option.includes("☁️")) {
             icon = <Cloud className="w-4 h-4" />;
             style = "bg-orange-600 hover:bg-orange-500 text-white";
             onClick = startGoogleAuth;
        } else if (option.includes("Zero") || option.includes("🚀")) {
             icon = <FileSpreadsheet className="w-4 h-4" />;
        } else if (option.includes("Certo") || option.includes("✅")) {
             icon = <CheckCircle className="w-4 h-4" />;
             style = "bg-green-600 hover:bg-green-500 text-white";
        }

        return (
            <button
                key={option}
                onClick={onClick}
                disabled={loading || uploading}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium shadow-lg transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 ${style}`}
            >
                {icon}
                {option}
            </button>
        );
    };

    return (
        <div className="flex flex-col h-screen bg-gray-950 text-white relative">
            {/* Header */}
            <header className="bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between shadow-md z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
                        <Play className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                            Configuração Inicial
                        </h1>
                        <p className="text-xs text-gray-400">BudgetIA Setup</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                    <ShieldCheck className="w-4 h-4" />
                    <span>Ambiente Seguro</span>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${
                                msg.sender === "user"
                                    ? "bg-emerald-600 text-white rounded-tr-none"
                                    : "bg-gray-800 text-gray-100 rounded-tl-none border border-gray-700"
                            }`}
                        >
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                        </div>
                    </div>
                ))}
                {(loading || uploading) && (
                    <div className="flex justify-start">
                        <div className="bg-gray-800 rounded-2xl p-4 rounded-tl-none border border-gray-700 animate-pulse">
                            <span className="flex gap-1">
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                            </span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Hidden File Input */}
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileUpload}
            />

            {/* Actions & Input */}
            <div className="bg-gray-900 border-t border-gray-800 p-4">
                {/* Contextual Buttons */}
                {uiOptions.length > 0 && !googleFiles && (
                    <div className="flex flex-wrap gap-3 justify-center mb-4 animate-fade-in-up">
                        {uiOptions.map(renderOptionButton)}
                    </div>
                )}

                {/* Text Input */}
                <form
                     onSubmit={(e) => {
                        e.preventDefault();
                        sendMessage(inputValue);
                    }}
                    className="flex gap-2 max-w-4xl mx-auto"
                >
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Digite sua mensagem..."
                        className="flex-1 bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder-gray-600"
                        disabled={loading || uploading}
                    />
                    <button
                        type="submit"
                        disabled={loading || uploading || !inputValue.trim()}
                        className="bg-emerald-600 text-white p-3 rounded-xl hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>

            {/* GOOGLE DRIVE SELECTION MODAL */}
            {googleFiles && (
                <div className="absolute inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
                    <div className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl max-w-md w-full max-h-[80vh] flex flex-col">
                        <div className="p-6 border-b border-gray-800">
                             <h2 className="text-xl font-bold flex items-center gap-2 text-white">
                                <Cloud className="text-emerald-500" />
                                Escolha sua Planilha
                             </h2>
                             <p className="text-sm text-gray-400 mt-1">
                                Selecione a planilha que você deseja que a IA gerencie.
                             </p>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-2">
                            {googleFiles.map((f) => (
                                <button
                                    key={f.id}
                                    onClick={() => selectGoogleFile(f)}
                                    className="w-full text-left p-4 rounded-xl bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-emerald-500/50 transition-all flex items-center gap-3 group"
                                >
                                    <FileSpreadsheet className="text-green-500 w-8 h-8 group-hover:scale-110 transition-transform" />
                                    <div>
                                        <p className="font-medium text-gray-200 group-hover:text-emerald-400 transition-colors">{f.name}</p>
                                        <p className="text-xs text-gray-500">ID: {f.id.slice(0, 10)}...</p>
                                    </div>
                                </button>
                            ))}
                        </div>
                        <div className="p-4 border-t border-gray-800">
                            <button
                                onClick={() => setGoogleFiles(null)}
                                className="w-full py-3 rounded-xl border border-gray-700 text-gray-400 hover:bg-gray-800 transition-colors"
                            >
                                Cancelar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
