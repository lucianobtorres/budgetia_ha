import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  action?: React.ReactNode;
}

export function Drawer({ isOpen, onClose, children, title, action }: DrawerProps) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Lock body scroll when drawer is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => { document.body.style.overflow = 'unset'; };
    }, [isOpen]);

    if (!mounted) return null;

    return createPortal(
        <AnimatePresence>
        {isOpen && (
            <>
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="fixed inset-0 z-[90] bg-black/60 backdrop-blur-sm"
            />
            
            {/* Drawer Panel */}
            <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed bottom-0 left-0 right-0 z-[100] mt-24 flex h-[85dvh] flex-col rounded-t-[20px] bg-gray-900 border-t border-gray-800 shadow-2xl"
            >
                {/* Handle/Header */}
                <div className="flex-none p-4 pb-2">
                    <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-gray-700/50" />
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">{title || "Detalhes"}</h2>
                        <div className="flex items-center gap-2">
                            {action}
                            <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-800 text-gray-400">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 pt-0">
                    {children}
                </div>
            </motion.div>
            </>
        )}
        </AnimatePresence>,
        document.body
    );
}
