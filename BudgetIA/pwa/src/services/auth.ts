import { fetchAPI } from './api';
import { STORAGE_KEYS } from '../utils/constants';

export interface UserSession {
    username: string;
    onboardingStatus: string;
}

export const AuthService = {
    async login(username: string, password: string): Promise<{ user: { username: string } }> {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Falha no login");
        }
        
        const data = await res.json();
        // Set local storage immediately upon success
        localStorage.setItem(STORAGE_KEYS.USER_ID, data.user.username);
        localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, data.access_token);
        return data;
    },

    async register(name: string, email: string, username: string, password: string): Promise<void> {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, username, password })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Falha no registro");
        }
    },

    async checkOnboardingState(username: string): Promise<string> {
        try {
            // Using fetchAPI automatically handles headers and base URL
            const data = await fetchAPI('/onboarding/state', {
                headers: { 'X-User-ID': username }
            });
            
            return data.state;
        } catch (error) {
            console.error("Onboarding Check Failed:", error);
            // Return ERROR to prevent false onboarding redirect
            return "ERROR";
        }
    },

    logout() {
        localStorage.removeItem(STORAGE_KEYS.USER_ID);
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
        window.location.reload();
    },

    getSessionUser(): string | null {
        return localStorage.getItem(STORAGE_KEYS.USER_ID);
    }
};
