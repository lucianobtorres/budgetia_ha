import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { TourOverlay } from '../components/ui/TourOverlay';
import { TOURS, type TourStep } from '../config/tours';
import { telemetry } from '../services/telemetry';
import { fetchAPI } from '../services/api';

type TourId = keyof typeof TOURS;

interface TourContextType {
    startTour: (tourId: TourId, force?: boolean) => void;
    dismissTour: () => void;
    isTourCompleted: (tourId: TourId) => boolean;
    resetTours: () => void;
}

const TourContext = createContext<TourContextType | undefined>(undefined);

export function TourProvider({ children }: { children: ReactNode }) {
    const [activeTourId, setActiveTourId] = useState<TourId | null>(null);
    const [activeStepsState, setActiveStepsState] = useState<TourStep[]>([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [completedTours, setCompletedTours] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Initial fetch from Server
    useEffect(() => {
        const fetchSeenTours = async () => {
            try {
                // fetchAPI returns the parsed JSON directly
                const data = await fetchAPI('/telemetry/tours');
                if (data) {
                    setCompletedTours(data.seen_tours || []);
                }
            } catch (error) {
                console.error("Failed to fetch seen tours:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchSeenTours();
    }, []);

    const startTour = (tourId: TourId, force = false) => {
        if (!TOURS[tourId]) {
            console.warn(`Tour '${tourId}' not found.`);
            return;
        }

        if (isLoading) return; // Wait for server sync

        // Check server state
        if (!force && completedTours.includes(tourId)) {
            return; // Já visto
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
    };

    const nextStep = () => {
        if (!activeTourId) return;
        
        if (currentStepIndex < activeStepsState.length - 1) {
            setCurrentStepIndex(prev => prev + 1);
        } else {
            completeTour();
        }
    };

    const prevStep = () => {
        if (currentStepIndex > 0) {
            setCurrentStepIndex(prev => prev - 1);
        }
    };

    const markAsSeenOnServer = async (tourId: string) => {
        try {
            await fetchAPI(`/telemetry/tours/${tourId}`, { method: 'POST' });
        } catch (error) {
            console.error("Failed to sync tour state:", error);
        }
    };

    const completeTour = () => {
        if (!activeTourId) return;

        const newCompleted = [...completedTours, activeTourId];
        setCompletedTours(newCompleted);
        markAsSeenOnServer(activeTourId);
        
        telemetry.logAction('tour_completed', { tour_id: activeTourId });
        
        setActiveTourId(null);
        setActiveStepsState([]);
    };

    const dismissTour = () => {
        if (activeTourId) {
            telemetry.logAction('tour_dismissed', { tour_id: activeTourId, step: currentStepIndex });
            
            // UX Decision: If user dismisses (clicks X), we consider it "Done" to avoid nagging.
            const newCompleted = [...completedTours, activeTourId];
            setCompletedTours(newCompleted);
            markAsSeenOnServer(activeTourId);

            setActiveTourId(null);
            setActiveStepsState([]);
        }
    };

    const isTourCompleted = (tourId: TourId) => completedTours.includes(tourId);

    const resetTours = () => {
        setCompletedTours([]);
        // Note: Currently we don't have a specific endpoint to clear history on server, 
        // as this is mostly a debug feature.
        telemetry.logAction('tour_reset', {});
    };

    const activeSteps: TourStep[] = activeStepsState;
    const currentStep = activeSteps[currentStepIndex];

    return (
        <TourContext.Provider value={{ startTour, dismissTour, isTourCompleted, resetTours }}>
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
