import { createContext } from 'react';
import { TOURS } from '../config/tours';

export type TourId = keyof typeof TOURS;

export interface TourContextType {
    startTour: (tourId: TourId, force?: boolean) => void;
    dismissTour: () => void;
    isTourCompleted: (tourId: TourId) => boolean;
    resetTours: () => void;
    isTourLoading: boolean;
}

export const TourContext = createContext<TourContextType | undefined>(undefined);
