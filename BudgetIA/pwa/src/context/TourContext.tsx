import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { TourOverlay } from '../components/ui/TourOverlay';
import { TOURS, type TourStep } from '../config/tours';
import { telemetry } from '../services/telemetry';

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
    const [currentStepIndex, setCurrentStepIndex] = useState(0); // Renaming for clarity if needed, but keeping simple
    const [completedTours, setCompletedTours] = useState<string[]>([]);

    useEffect(() => {
        const saved = localStorage.getItem('budgetia_completed_tours');
        if (saved) {
            setCompletedTours(JSON.parse(saved));
        }
    }, []);

    const startTour = (tourId: TourId, force = false) => {
        if (!TOURS[tourId]) {
            console.warn(`Tour '${tourId}' not found.`);
            return;
        }

        // Check localStorage directly to avoid closure staleness issues with useEffect/state
        const storedCompleted = JSON.parse(localStorage.getItem('budgetia_completed_tours') || '[]');
        if (!force && (completedTours.includes(tourId) || storedCompleted.includes(tourId))) {
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
        
        // Use filtered steps state
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

    const completeTour = () => {
        if (!activeTourId) return;

        const newCompleted = [...completedTours, activeTourId];
        setCompletedTours(newCompleted);
        localStorage.setItem('budgetia_completed_tours', JSON.stringify(newCompleted));
        
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
            localStorage.setItem('budgetia_completed_tours', JSON.stringify(newCompleted));

            setActiveTourId(null);
            setActiveStepsState([]);
        }
    };

    const isTourCompleted = (tourId: TourId) => completedTours.includes(tourId);

    const resetTours = () => {
        setCompletedTours([]);
        localStorage.removeItem('budgetia_completed_tours');
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
