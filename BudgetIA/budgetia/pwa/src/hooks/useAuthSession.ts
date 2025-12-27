import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthService } from '../services/auth';

export function useAuthSession() {
    const [user, setUser] = useState<string | null>(AuthService.getSessionUser());
    const [onboardingStatus, setOnboardingStatus] = useState<string>("UNKNOWN");
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogin = (username: string) => {
        // AuthService already sets localStorage, but we need to update state
        // In a real app we might want to decode token or just trust the username passed
        setUser(username);
    };

    useEffect(() => {
        if (user) {
            const checkOnboarding = async () => {
                const status = await AuthService.checkOnboardingState(user);
                setOnboardingStatus(status);
                
                if (status !== "COMPLETE" && status !== "ERROR") {
                     if (location.pathname !== "/onboarding" && location.pathname !== "/google-callback") {
                          navigate("/onboarding");
                     }
                }
            };
            checkOnboarding();
        }
    }, [user, navigate, location.pathname]);

    return { user, onboardingStatus, handleLogin };
}
