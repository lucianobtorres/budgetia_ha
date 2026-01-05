import { fetchAPI } from './api';
import { STORAGE_KEYS } from '../utils/constants';

export interface UserSession {
    username: string;
    onboardingStatus: string;
}

export const AuthService = {
    async login(username: string, password: string): Promise<{ user: { username: string, role: string, trial_ends_at?: string, deploy_mode?: string } }> {
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
        localStorage.setItem(STORAGE_KEYS.USER_ROLE, data.user.role || 'user');
        localStorage.setItem(STORAGE_KEYS.DEPLOY_MODE, data.user.deploy_mode || 'SAAS');
        
        if (data.user.trial_ends_at) {
            localStorage.setItem(STORAGE_KEYS.TRIAL_ENDS_AT, data.user.trial_ends_at);
        } else {
            localStorage.removeItem(STORAGE_KEYS.TRIAL_ENDS_AT); // Clear if user becomes paid/lifetime
        }

        localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, data.access_token);
        return data;
    },

    async register(name: string, email: string, password: string): Promise<any> {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Falha no registro");
        }
        
        return await res.json();
    },

    async verifyEmail(token: string): Promise<any> {
        return fetchAPI('/auth/verify-email', {
            method: 'POST',
            body: JSON.stringify({ token })
        });
    },

    async resendVerification(email: string): Promise<any> {
        return fetchAPI('/auth/resend-verification', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    },

    async forgotPassword(email: string): Promise<any> {
        return fetchAPI('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    },

    async resetPassword(token: string, new_password: string): Promise<any> {
        return fetchAPI('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, new_password })
        });
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
        localStorage.removeItem(STORAGE_KEYS.USER_ROLE);
        localStorage.removeItem(STORAGE_KEYS.TRIAL_ENDS_AT);
        localStorage.removeItem(STORAGE_KEYS.DEPLOY_MODE);
        window.location.reload();
    },

    getSessionUser(): string | null {
        return localStorage.getItem(STORAGE_KEYS.USER_ID);
    },

    getUserRole(): string {
        return localStorage.getItem(STORAGE_KEYS.USER_ROLE) || 'user';
    },

    getTrialEndDate(): string | null {
        return localStorage.getItem(STORAGE_KEYS.TRIAL_ENDS_AT);
    },

    getDeployMode(): string {
        return localStorage.getItem(STORAGE_KEYS.DEPLOY_MODE) || 'SAAS';
    },

    setSession(token: string, user: any) {
        localStorage.setItem(STORAGE_KEYS.USER_ID, user.username);
        localStorage.setItem(STORAGE_KEYS.USER_ROLE, user.role || 'user');
        localStorage.setItem(STORAGE_KEYS.DEPLOY_MODE, user.deploy_mode || 'SAAS');
        
        if (user.trial_ends_at) {
            localStorage.setItem(STORAGE_KEYS.TRIAL_ENDS_AT, user.trial_ends_at);
        } else {
            localStorage.removeItem(STORAGE_KEYS.TRIAL_ENDS_AT);
        }

        localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
    }
};
