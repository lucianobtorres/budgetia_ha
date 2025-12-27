import { useState, useEffect, useCallback } from "react";
import { fetchAPI } from "../services/api"; // Unified API fetcher
import { useNavigate } from "react-router-dom";

export interface Message {
    sender: "agent" | "user";
    text: string;
}

export interface GoogleFile {
    id: string;
    name: string;
    url: string;
    icon?: string;
}

interface OnboardingStateData {
    state: string;
    progress: number;
    ui_options: string[];
    initial_message: string | null;
    google_files_list?: any[];
}

export function useOnboarding() {
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([]);
    const [uiOptions, setUiOptions] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [googleFiles, setGoogleFiles] = useState<GoogleFile[] | null>(null);

    // Helper to process backend response
    const handleApiResponse = useCallback((data: any) => {
        // 1. Add message (clean tags)
        if (data.message) {
             const cleanText = data.message.replace(/\[UI_ACTION:.*?\]/g, "").trim();
             if (cleanText) {
                 setMessages(prev => [...prev, { sender: "agent", text: cleanText }]);
             }
        }

        // 2. Update Options
        if (data.ui_options) {
            console.log("Onboarding UI Options:", data.ui_options);
            setUiOptions(data.ui_options);
        }

        // 3. Check for Google Files
        if (data.google_files_list && data.google_files_list.length > 0) {
            const mappedFiles = data.google_files_list.map((f: any) => ({
                id: f.id,
                name: f.name,
                url: f.webViewLink, 
                icon: f.iconLink
            }));
            setGoogleFiles(mappedFiles);
        }

        // 4. Check completion
        if (data.state === "COMPLETE") {
            setTimeout(() => navigate("/"), 2000);
        }
    }, [navigate]);

    // Initial Check
    useEffect(() => {
        const checkState = async () => {
            try {
                const data: OnboardingStateData = await fetchAPI('/onboarding/state');
                
                if (data.state === "COMPLETE") {
                    navigate("/");
                    return;
                }

                setUiOptions(data.ui_options);
                
                if (data.initial_message && messages.length === 0) {
                     setMessages([{ sender: "agent", text: data.initial_message }]);
                }
            } catch (e) {
                console.error("Failed to check state", e);
            }
        };
        checkState();
    }, []); // eslint-disable-line

    const sendMessage = async (text: string) => {
        if (!text.trim()) return;
        
        const newMessages = [...messages, { sender: "user", text } as Message];
        setMessages(newMessages);
        setLoading(true);

        try {
            const data = await fetchAPI('/onboarding/chat', {
                method: 'POST',
                body: JSON.stringify({ text })
            });
            handleApiResponse(data);
        } catch (error) {
            setMessages(prev => [...prev, { sender: "agent", text: "Erro ao comunicar com o servidor." }]);
        } finally {
            setLoading(false);
        }
    };

    const uploadFile = async (file: File) => {
        setLoading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            setMessages(prev => [...prev, { sender: "user", text: `Enviando arquivo: ${file.name}...` }]);
            
            // fetchAPI handles JSON, but for FormData we might need standard fetch or adjust helper?
            // fetchAPI usually sets Content-Type: application/json. 
            // Let's use standard fetch for upload to let browser set boundary.
             const userId = localStorage.getItem('budgetia_user_id') || "";
             const res = await fetch('/api/onboarding/upload', {
                method: 'POST',
                headers: { 'X-User-ID': userId }, // No Content-Type, browser sets it
                body: formData
            });
            const data = await res.json();
            handleApiResponse(data);

        } catch (error) {
             setMessages(prev => [...prev, { sender: "agent", text: "Falha no upload." }]);
        } finally {
            setLoading(false);
        }
    };

    const startGoogleAuth = async () => {
        try {
            const redirectUri = encodeURIComponent(`${window.location.origin}/google-callback`);
            const data = await fetchAPI(`/onboarding/google-auth-url?redirect_uri=${redirectUri}`);
            
            if (data.url) {
                window.location.href = data.url;
            } else {
                alert("Erro ao gerar URL.");
            }
        } catch (error) {
            console.error("Erro auth Google", error);
        }
    };

    const sendGoogleAuthCode = async (code: string) => {
        setLoading(true);
        try {
            const data = await fetchAPI('/onboarding/google-auth', {
                method: 'POST',
                body: JSON.stringify({ 
                    code,
                    redirect_uri: `${window.location.origin}/google-callback`
                })
            });
            handleApiResponse(data);
        } catch (error) {
            setMessages(prev => [...prev, { sender: "agent", text: "Erro ao autenticar com Google." }]);
        } finally {
            setLoading(false);
        }
    };

    return {
        messages,
        loading,
        uiOptions,
        googleFiles,
        sendMessage,
        uploadFile,
        startGoogleAuth,
        sendGoogleAuthCode,
        setGoogleFiles
    };
}
