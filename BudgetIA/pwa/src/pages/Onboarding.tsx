import { useRef, useEffect } from "react";
import { ShieldCheck, Cloud, FileSpreadsheet } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { useOnboarding } from "../hooks/useOnboarding";
import { MessageBubble } from "../components/chat/MessageBubble";
import { ChatInput } from "../components/chat/ChatInput";
import { OnboardingActions } from "../components/onboarding/OnboardingActions";

export default function Onboarding() {
    const { 
        messages, 
        loading, 
        uiOptions, 
        googleFiles, 
        sendMessage, 
        uploadFile, 
        startGoogleAuth, 
        sendGoogleAuthCode,
        setGoogleFiles
    } = useOnboarding();

    const navigate = useNavigate();
    const location = useLocation();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [input, setInput] = React.useState(""); // Local input state

    // Scroll to bottom effect
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    // Handle Google Callback
    useEffect(() => {
        if (location.state && (location.state as any).googleAuthCode) {
            const { googleAuthCode } = location.state as any;
            // Clear state to prevent loop
            navigate(location.pathname, { replace: true, state: {} });
            sendGoogleAuthCode(googleAuthCode);
        }
    }, [location.state]); // eslint-disable-line

    const handleSend = () => {
        if (!input.trim()) return;
        sendMessage(input);
        setInput("");
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.[0]) {
            uploadFile(e.target.files[0]);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    return (
        <div className="flex flex-col h-[100dvh] bg-gray-950 text-white relative overflow-hidden">
            {/* Header */}
            <header className="bg-gray-900/50 backdrop-blur-md border-b border-gray-800 p-4 flex items-center justify-between shadow-sm z-10 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="relative h-8 w-8 overflow-hidden rounded-lg shadow-sm ring-1 ring-white/10 shrink-0">
                        <img src="/pwa-192x192.png" alt="Logo" className="h-full w-full object-cover" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold tracking-tight text-white leading-none">
                            Budget<span className="text-emerald-500">IA</span>
                        </h1>
                        <p className="text-[10px] text-gray-400 font-medium tracking-wide uppercase mt-0.5">
                            Configuração Inicial
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <ShieldCheck className="w-3 h-3 text-emerald-500" />
                    <span className="text-[10px] font-medium text-emerald-400">Ambiente Seguro</span>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-none">
                {messages.map((msg, index) => (
                     <MessageBubble 
                        key={index} 
                        message={{ role: msg.sender === 'agent' ? 'assistant' : 'user', content: msg.text }} 
                    />
                ))}
                {loading && (
                    <div className="flex justify-start">
                         <div className="bg-gray-800/80 text-gray-100 rounded-2xl rounded-tl-sm p-4 flex items-center space-x-2 border border-gray-700/50">
                             <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" />
                             <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce delay-75" />
                             <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce delay-150" />
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
                onChange={handleFileChange}
            />

            {/* Actions & Input */}
            <div className="bg-gray-900 border-t border-gray-800 p-4">
                {/* Contextual Buttons */}
                {!googleFiles && (
                    <OnboardingActions 
                        options={uiOptions} 
                        onSelect={sendMessage}
                        onUploadClick={() => fileInputRef.current?.click()}
                        onGoogleClick={startGoogleAuth}
                        disabled={loading}
                    />
                )}

                {/* Chat Input */}
                <div className="max-w-4xl mx-auto">
                     <ChatInput 
                        value={input}
                        onChange={setInput}
                        onSend={handleSend}
                        loading={loading}
                        showClear={false}
                        placeholder="Digite sua resposta..."
                        autoFocus={true}
                    />
                </div>
            </div>

            {/* GOOGLE DRIVE SELECTION MODAL */}
            {googleFiles && (
                <div className="absolute inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl max-w-md w-full max-h-[80vh] flex flex-col animate-fade-in-up">
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
                                    onClick={() => {
                                        setGoogleFiles(null);
                                        sendMessage(f.url);
                                    }}
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

import React from 'react'; // Add React import for useState
