import { useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTour, type TourId } from '../context/TourContext';

export function usePageTour(tourId: TourId | null, startCondition: boolean = true) {
    const { startTour, isTourLoading, isTourCompleted } = useTour();
    const location = useLocation();
    const navigate = useNavigate();
    const processedRef = useRef<string | null>(null);

    useEffect(() => {
        // If tourId is not determined yet, or global tour loading is in progress, or condition not met
        if (!tourId || isTourLoading || !startCondition) {
            return;
        }

        // Check for restart signal from navigation (e.g. Profile -> Dashboard)
        const shouldForce = location.state?.restartTour;

        // Verify if we already processed this tour to avoid double-firing in StrictMode
        // or rapid re-renders.
        if (processedRef.current === tourId && !shouldForce) return;

        if (shouldForce) {
            // Start immediately (with small delay for render safety)
            const timer = setTimeout(() => {
                startTour(tourId, true);
                
                // Clear the state properly using React Router
                // This updates the location object for the next render
                navigate(location.pathname, { replace: true, state: {} });
            }, 500);
            
            processedRef.current = tourId;
            return () => clearTimeout(timer);
        } else {
            if (!isTourCompleted(tourId)) {
                // Auto-start for new users
                const timer = setTimeout(() => {
                    startTour(tourId, false);
                }, 1000); // 1s delay for "wow" effect / settling
                
                processedRef.current = tourId;
                return () => clearTimeout(timer);
            }
        }

    }, [tourId, isTourLoading, startCondition, startTour, isTourCompleted, location.state, location.pathname, navigate]);
}
