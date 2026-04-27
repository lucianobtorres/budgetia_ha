import { useState, useEffect, useCallback, type ReactNode } from 'react';
import { TourOverlay } from '../components/ui/TourOverlay';
import { TOURS, type TourStep } from '../config/tours';
import { telemetry } from '../services/telemetry';
import { fetchAPI } from '../services/api';
import { TourContext, type TourId } from './TourContext';

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
                const data = await fetchAPI<{ seen_tours: string[] }>('/telemetry/tours');
                if (data && data.seen_tours) {
                    setCompletedTours(prev => {
                        const merged = Array.from(new Set([...prev, ...data.seen_tours]));
                        localStorage.setItem('budgetia_seen_tours', JSON.stringify(merged));
                        return merged;
                    });
                }
            } catch (error) {
                console.error("Failed to fetch seen tours:", error);
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

        if (isLoading) return;

        if (!force && completedTours.includes(tourId)) {
            return;
        }
        
        if (!force && activeTourId === tourId) {
             return;
        }

        const rawSteps = TOURS[tourId];
        const validSteps = rawSteps.filter(step => {
            const el = document.getElementById(step.targetId);
            return !!el;
        });

        if (validSteps.length === 0) {
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
        localStorage.setItem('budgetia_seen_tours', JSON.stringify(newCompleted));
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
            const newCompleted = [...completedTours, activeTourId];
            setCompletedTours(newCompleted);
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
