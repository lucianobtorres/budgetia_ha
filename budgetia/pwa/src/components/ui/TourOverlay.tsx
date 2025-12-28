import { AnimatePresence, motion } from 'framer-motion';
import { createPortal } from 'react-dom';
import { useEffect, useState } from 'react';
import { X, ChevronRight, ChevronLeft } from 'lucide-react';
import { cn } from '../../utils/cn';

interface TourStep {
    targetId: string;
    title: string;
    content: string;
    position?: 'top' | 'bottom' | 'left' | 'right';
}

interface TourOverlayProps {
    isOpen: boolean;
    step: TourStep;
    currentStepIndex: number;
    totalSteps: number;
    onNext: () => void;
    onPrev: () => void;
    onClose: () => void;
}

export function TourOverlay({
    isOpen,
    step,
    currentStepIndex,
    totalSteps,
    onNext,
    onPrev,
    onClose
}: TourOverlayProps) {
    const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

    // Update rect on step change or resize
    useEffect(() => {
        if (!isOpen) return;

        const updateRect = () => {
            const el = document.getElementById(step.targetId);
            if (el) {
                // Scroll element into view smoothly if needed
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTargetRect(el.getBoundingClientRect());
            } else {
                // Fallback if target not found: Just center or warn
                console.warn(`Tour target #${step.targetId} not found`);
                setTargetRect(null); // Will render centralized modal fallback
            }
        };

        // Delay slightly to allow any layout shifts/animations to settle
        const timer = setTimeout(updateRect, 300);
        window.addEventListener('resize', updateRect);
        
        return () => {
            window.removeEventListener('resize', updateRect);
            clearTimeout(timer);
        };
    }, [step.targetId, isOpen]);

    if (!isOpen) return null;

    // Portal to render outside standard DOM hierarchy (on top of everything)
    return createPortal(
        <AnimatePresence>
            <div className="fixed inset-0 z-[9999] isolate pointer-events-none">
                {/* 1. Backdrop with Hole (SVG Mask) */}
                {targetRect && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/70 pointer-events-auto"
                        style={{
                            clipPath: `polygon(
                                0% 0%, 
                                0% 100%, 
                                0% ${targetRect.top}px, 
                                ${targetRect.left}px ${targetRect.top}px, 
                                ${targetRect.left}px ${targetRect.bottom}px, 
                                ${targetRect.right}px ${targetRect.bottom}px, 
                                ${targetRect.right}px ${targetRect.top}px, 
                                0% ${targetRect.top}px, 
                                100% 0%, 
                                100% 100%, 
                                0% 100%
                            )`
                            // Note: Polygon clip-path is tricky for holes. 
                            // A better approach often used is a massive border or 4 separate div overlays. 
                            // Or just a full SVG overlay with a mask.
                            // Let's use a simpler "Spotlight" composed of 4 divs to ensure click-through block works easily.
                        }}
                    >
                         {/* This simplistic clipPath approach has issues with "evenodd" rules in CSS.
                             Let's switch to the "SVG Mask" strategy for perfect holes. 
                         */}
                    </motion.div>
                )}

                {/* SVG Mask Impl - More Robust */}
                 <motion.svg 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 w-full h-full pointer-events-auto"
                >
                    <defs>
                        <mask id="tour-mask">
                            <rect x="0" y="0" width="100%" height="100%" fill="white" />
                            {targetRect && (
                                <rect 
                                    x={targetRect.left - 5} 
                                    y={targetRect.top - 5} 
                                    width={targetRect.width + 10} 
                                    height={targetRect.height + 10} 
                                    rx="8" 
                                    fill="black" 
                                />
                            )}
                        </mask>
                    </defs>
                    <rect 
                        width="100%" 
                        height="100%" 
                        fill="rgba(0,0,0,0.7)" 
                        mask="url(#tour-mask)" 
                    />
                </motion.svg>

                {/* 2. Highlight Border */}
                {targetRect && (
                    <motion.div
                        layoutId="tour-highlight"
                        className="absolute border-2 border-emerald-500 rounded-lg shadow-[0_0_20px_rgba(16,185,129,0.5)] pointer-events-none"
                        style={{
                            left: targetRect.left - 5,
                            top: targetRect.top - 5,
                            width: targetRect.width + 10,
                            height: targetRect.height + 10,
                        }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                )}

                {/* 3. Tooltip Card */}
                {targetRect ? (
                    <div 
                        className="absolute pointer-events-auto"
                        style={getTooltipStyle(targetRect)}
                    >
                        <Card 
                            step={step} 
                            current={currentStepIndex} 
                            total={totalSteps}
                            onNext={onNext}
                            onPrev={onPrev}
                            onClose={onClose}
                        />
                    </div>
                ) : (
                    // Center fallback if no target
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-auto">
                        <Card 
                             step={step} 
                             current={currentStepIndex} 
                             total={totalSteps}
                             onNext={onNext}
                             onPrev={onPrev}
                             onClose={onClose}
                        />
                    </div>
                )}
            </div>
        </AnimatePresence>,
        document.body
    );
}

// Helper to calculate position
function getTooltipStyle(rect: DOMRect): React.CSSProperties {
    const isMobile = window.innerWidth < 768;
    const CARD_HEIGHT_ESTIMATE = 220;
    const MARGIN = 20;
    const VIEWPORT_MARGIN = 16;

    // Default: Desktop standard
    const style: React.CSSProperties = {
        position: 'absolute',
        width: isMobile ? 'auto' : 300,
        left: isMobile ? VIEWPORT_MARGIN : Math.max(VIEWPORT_MARGIN, Math.min(rect.left, window.innerWidth - 320)),
        right: isMobile ? VIEWPORT_MARGIN : 'auto'
    };

    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    if (spaceBelow > CARD_HEIGHT_ESTIMATE) {
        // Place Below
        style.top = rect.bottom + MARGIN;
    } else if (spaceAbove > CARD_HEIGHT_ESTIMATE) {
        // Place Above
        style.bottom = window.innerHeight - rect.top + MARGIN;
    } else {
        // Overlap / Inside (Large Element Case)
        // Check if we should place at Top-Inside or Bottom-Inside ?
        // Usually Top-Inside is safer for lists
        style.top = Math.max(VIEWPORT_MARGIN, rect.top + MARGIN);
        
        // Ensure it doesn't go off screen bottom if element is weirdly placed
        // But since we are "inside", we assume we are visible.
        // Also add background/backdrop contrast if needed? The card has shadow/border.
        
        // Force visual separation if inside? 
        // Maybe ensure we are not too far right if overlapping content?
        // Keep left logic.
    }

    return style;
}

function Card({ step, current, total, onNext, onPrev, onClose }: any) {
    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-5 text-white flex flex-col gap-3 relative z-50"
        >
            <div className="flex justify-between items-start">
                <h3 className="font-bold text-lg text-emerald-400">{step.title}</h3>
                <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                    <X size={18} />
                </button>
            </div>
            <p className="text-gray-300 text-sm leading-relaxed">
                {step.content}
            </p>
            
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-800">
                <span className="text-xs text-gray-500">
                    Passo {current + 1} de {total}
                </span>
                <div className="flex gap-2">
                    {current > 0 && (
                        <button 
                            onClick={onPrev}
                            className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            <ChevronLeft size={20} />
                        </button>
                    )}
                    <button 
                        onClick={onNext}
                        className={cn(
                            "px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1",
                            current === total - 1 
                                ? "bg-emerald-500 hover:bg-emerald-600 text-white" 
                                : "bg-white/10 hover:bg-white/20 text-white"
                        )}
                    >
                        {current === total - 1 ? "Concluir" : "Próximo"}
                        {current !== total - 1 && <ChevronRight size={16} />}
                    </button>
                </div>
            </div>
        </motion.div>
    );
}
