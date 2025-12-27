const API_BASE_URL = '/api'; // Proxied by Vite
import { STORAGE_KEYS, DEFAULT_USER_FALLBACK } from '../utils/constants';

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
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

    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        // Return empty if no content
        if (response.status === 204) return null;

        return await response.json();
    } catch (error) {
        console.error("API Request Failed:", error);
        throw error;
    }
}
