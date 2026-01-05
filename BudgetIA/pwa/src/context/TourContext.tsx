import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { TourOverlay } from '../components/ui/TourOverlay';
import { TOURS, type TourStep } from '../config/tours';
import { telemetry } from '../services/telemetry';
import { fetchAPI } from '../services/api';

export type TourId = keyof typeof TOURS;

interface TourContextType {
    startTour: (tourId: TourId, force?: boolean) => void;
    dismissTour: () => void;
    isTourCompleted: (tourId: TourId) => boolean;
    resetTours: () => void;
    isTourLoading: boolean;
}

const TourContext = createContext<TourContextType | undefined>(undefined);

export function TourProvider({ children }: { children: ReactNode }) {
    const [activeTourId, setActiveTourId] = useState<TourId | null>(null);
    const [activeStepsState, setActiveStepsState] = useState<TourStep[]>([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [completedTours, setCompletedTours] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Initial fetch from Server & LocalStorage Sync
    useEffect(() => {
        const loadSeenTours = async () => {
            // 1. Load from LocalStorage first for instant feedback (no flicker)
            try {
                const stored = localStorage.getItem('budgetia_seen_tours');
                if (stored) {
                    setCompletedTours(JSON.parse(stored));
                }
            } catch (e) {
                console.error("Error reading localStorage tour state", e);
            }

            // 2. Fetch from Server to sync
            try {
                // fetchAPI returns the parsed JSON directly
                const data = await fetchAPI('/telemetry/tours');
                if (data && data.seen_tours) {
                    // Merge server data with local data (redundancy)
                    setCompletedTours(prev => {
                        const merged = Array.from(new Set([...prev, ...data.seen_tours]));
                        localStorage.setItem('budgetia_seen_tours', JSON.stringify(merged));
                        return merged;
                    });
                }
            } catch (error) {
                console.error("Failed to fetch seen tours:", error);
                // On error, we rely on what we loaded from localStorage
            } finally {
                setIsLoading(false);
            }
        };
        loadSeenTours();
    }, []);

    const startTour = useCallback((tourId: TourId, force = false) => {
        if (!TOURS[tourId]) {
            console.warn(`Tour '${tourId}' not found.`);
            return;
        }

        if (isLoading) return; // Wait for server sync

        // Check server state
        if (!force && completedTours.includes(tourId)) {
            return; // Já visto
        }
        
        // Prevent restarting the same tour if it's already active (unless forced)
        if (!force && activeTourId === tourId) {
             return;
        }

        // DYNAMIC FILTERING: Only include steps for elements that exist in the DOM
        const rawSteps = TOURS[tourId];
        const validSteps = rawSteps.filter(step => {
            const el = document.getElementById(step.targetId);
            if (!el) {
                console.warn(`[Tour] Skipping step '${step.title}' because target '#${step.targetId}' is missing.`);
                return false;
            }
            return true;
        });

        if (validSteps.length === 0) {
            console.warn(`[Tour] No valid steps found for '${tourId}'.`);
            return; 
        }

        setActiveTourId(tourId);
        setActiveStepsState(validSteps);
        setCurrentStepIndex(0);
        
        telemetry.logAction('tour_started', { tour_id: tourId });
    }, [isLoading, completedTours, activeTourId]);

    const markAsSeenOnServer = useCallback(async (tourId: string) => {
        try {
            await fetchAPI(`/telemetry/tours/${tourId}`, { method: 'POST' });
        } catch (error) {
            console.error("Failed to sync tour state:", error);
        }
    }, []);

    const completeTour = useCallback(() => {
        if (!activeTourId) return;

        const newCompleted = [...completedTours, activeTourId];
        
        setCompletedTours(newCompleted);
        
        // Persist locally immediately
        localStorage.setItem('budgetia_seen_tours', JSON.stringify(newCompleted));
        
        // Sync with server
        markAsSeenOnServer(activeTourId);
        
        telemetry.logAction('tour_completed', { tour_id: activeTourId });
        
        setActiveTourId(null);
        setActiveStepsState([]);
    }, [activeTourId, completedTours, markAsSeenOnServer]);

    const nextStep = useCallback(() => {
        if (!activeTourId) return;
        
        if (currentStepIndex < activeStepsState.length - 1) {
            setCurrentStepIndex(prev => prev + 1);
        } else {
            completeTour();
        }
    }, [activeTourId, currentStepIndex, activeStepsState.length, completeTour]);

    const prevStep = useCallback(() => {
        if (currentStepIndex > 0) {
            setCurrentStepIndex(prev => prev - 1);
        }
    }, [currentStepIndex]);

    const dismissTour = useCallback(() => {
        if (activeTourId) {
            telemetry.logAction('tour_dismissed', { tour_id: activeTourId, step: currentStepIndex });
            
            // UX Decision: If user dismisses (clicks X), we consider it "Done" to avoid nagging.
            const newCompleted = [...completedTours, activeTourId];
            setCompletedTours(newCompleted);
            
            // Persist locally immediately
            localStorage.setItem('budgetia_seen_tours', JSON.stringify(newCompleted));
            
            markAsSeenOnServer(activeTourId);

            setActiveTourId(null);
            setActiveStepsState([]);
        }
    }, [activeTourId, currentStepIndex, completedTours, markAsSeenOnServer]);

    const isTourCompleted = useCallback((tourId: TourId) => completedTours.includes(tourId), [completedTours]);

    const resetTours = useCallback(async () => {
        setCompletedTours([]);
        localStorage.removeItem('budgetia_seen_tours');
        
        try {
            await fetchAPI('/telemetry/tours', { method: 'DELETE' });
        } catch (e) {
            console.error('[TourContext] Failed to clear server history', e);
        }

        telemetry.logAction('tour_reset', {});
    }, []);

    const activeSteps: TourStep[] = activeStepsState;
    const currentStep = activeSteps[currentStepIndex];

    return (
        <TourContext.Provider value={{ startTour, dismissTour, isTourCompleted, resetTours, isTourLoading: isLoading }}>
            {children}
            
            {activeTourId && currentStep && (
                <TourOverlay 
                    isOpen={true}
                    step={currentStep}
                    currentStepIndex={currentStepIndex}
                    totalSteps={activeSteps.length}
                    onNext={nextStep}
                    onPrev={prevStep}
                    onClose={dismissTour}
                />
            )}
        </TourContext.Provider>
    );
}

export const useTour = () => {
    const context = useContext(TourContext);
    if (!context) throw new Error("useTour must be used within TourProvider");
    return context;
};
