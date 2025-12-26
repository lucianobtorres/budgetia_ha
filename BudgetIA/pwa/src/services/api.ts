const API_BASE_URL = '/api'; // Proxied by Vite
import { STORAGE_KEYS, DEFAULT_USER_FALLBACK } from '../utils/constants';

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Get User ID from localStorage or default to fallback
    // In a real app, this would come from an Auth Context or Login flow
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || DEFAULT_USER_FALLBACK;

    const defaultHeaders = {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
    };

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
