const API_BASE_URL = '/api'; // Proxied by Vite
import { STORAGE_KEYS, DEFAULT_USER_FALLBACK } from '../utils/constants';
import { toast } from 'sonner';

interface RequestOptions extends RequestInit {
    skipErrorHandling?: boolean;
}

export async function fetchAPI<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Get User ID from localStorage or default to fallback
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || DEFAULT_USER_FALLBACK;
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);

    const defaultHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-User-ID': userId, // Mantendo por compatibilidade com logs antigos se necessário
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    // If body is FormData, let browser set Content-Type with boundary
    if (options.body instanceof FormData) {
        delete (config.headers as Record<string, string>)['Content-Type'];
    }

    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            
            // Auto-logout on 401 (Unauthorized) or 403 (Forbidden/Blocked)
            if (response.status === 401 || response.status === 403) {
                console.warn(`Access denied (${response.status}) - redirecting to login`);
                localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
                localStorage.removeItem(STORAGE_KEYS.USER_ID);
                localStorage.removeItem(STORAGE_KEYS.USER_ROLE);
                
                // Avoid infinite reload loops if already on login or public auth pages
                const publicPaths = ['/login', '/register', '/forgot-password', '/reset-password', '/verify', '/landing'];
                const isPublicPath = publicPaths.some(path => window.location.pathname.startsWith(path));

                if (!isPublicPath) {
                    window.location.href = '/login';
                }
                
                const msg = response.status === 403 ? "Acesso negado ou conta bloqueada." : "Sessão expirada. Faça login novamente.";
                throw new Error(msg);
            }

            // Try to parse error message from API
            let errorMessage = `API Error: ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.detail) errorMessage = errorData.detail;
                if (errorData.message) errorMessage = errorData.message;
            } catch (e) {
                // Ignore parsing error, keep default
            }

            throw new Error(errorMessage);
        }

        // Return empty if no content
        if (response.status === 204) return null;

        return await response.json();
    } catch (error: any) {
        console.error("API Request Failed:", error);

        if (!options.skipErrorHandling) {
            toast.error(error.message || "Ocorreu um erro na requisição.");
        }
        
        throw error;
    }
}
