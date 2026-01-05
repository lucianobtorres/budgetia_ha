import { useEffect, useState } from 'react';
import { AlertTriangle, Info, X, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchAPI } from '../../services/api';

interface SystemBannerData {
    id: string;
    is_active: boolean;
    message: string;
    level: 'info' | 'warning' | 'error';
    expires_at?: string;
}

export function GlobalBanner() {
    const [banner, setBanner] = useState<SystemBannerData | null>(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const checkBanner = async () => {
            try {
                const data = await fetchAPI('/system/banner');
                if (data && data.is_active) {
                    const dismissedId = localStorage.getItem('dismissed_banner_id');
                    if (dismissedId !== data.id) {
                        setBanner(data);
                        setIsVisible(true);
                    } else {
                        // Banner exists but was dismissed
                        setBanner(null);
                        setIsVisible(false);
                    }
                } else {
                    setBanner(null);
                    setIsVisible(false);
                }
            } catch (error) {
                console.debug("No system banner found");
            }
        };

        checkBanner();
        // Check every 30 seconds
        const interval = setInterval(checkBanner, 30 * 1000);
        return () => clearInterval(interval);
    }, []);

    const handleDismiss = () => {
        if (banner) {
            localStorage.setItem('dismissed_banner_id', banner.id);
            setIsVisible(false);
        }
    };

    if (!banner || !isVisible) return null;

    const getStyles = () => {
        switch (banner.level) {
            case 'error': return "bg-red-600 text-white";
            case 'warning': return "bg-orange-500 text-white";
            default: return "bg-blue-600 text-white";
        }
    };

    const getIcon = () => {
        switch (banner.level) {
            case 'error': return <AlertTriangle className="w-4 h-4" />;
            case 'warning': return <AlertTriangle className="w-4 h-4" />;
            default: return <Info className="w-4 h-4" />;
        }
    };

    return (
        <AnimatePresence>
            <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className={`${getStyles()} relative z-50 shadow-md`}
            >
                <div className="max-w-7xl mx-auto px-4 py-2 relative flex items-center justify-center text-xs md:text-sm font-medium">
                    <div className="flex items-center gap-2">
                        {getIcon()}
                        <span>{banner.message}</span>
                        {banner.expires_at && (
                            <span className="text-white/70 text-xs ml-2 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                até {new Date(banner.expires_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                        )}
                    </div>
                    
                    <button 
                        onClick={handleDismiss}
                        className="absolute right-4 p-1 hover:bg-white/20 rounded-full transition-colors"
                        title="Fechar aviso permanentemente"
                    >
                        <X className="w-3 h-3 md:w-4 md:h-4" />
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
