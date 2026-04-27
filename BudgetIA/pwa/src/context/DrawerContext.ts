import { createContext } from 'react';

// Define the types of drawers available
export type DrawerType = 'CATEGORY_EXPENSES' | 'BUDGETS';

export interface DrawerState {
    isOpen: boolean;
    type: DrawerType | null;
    highlightCategory?: string;
    highlightId?: number;
}

export interface DrawerContextProps {
    drawerState: DrawerState;
    openDrawer: (type: DrawerType, params?: { highlightCategory?: string; highlightId?: number }) => void;
    closeDrawer: () => void;
}

export const DrawerContext = createContext<DrawerContextProps | undefined>(undefined);
