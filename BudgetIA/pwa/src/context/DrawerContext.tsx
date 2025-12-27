import React, { createContext, useContext, useState, ReactNode } from 'react';

// Define the types of drawers available
export type DrawerType = 'CATEGORY_EXPENSES' | 'BUDGETS';

interface DrawerState {
    isOpen: boolean;
    type: DrawerType | null;
    highlightCategory?: string; // Optional: Category to scroll to
    highlightId?: number; // Optional: ID to scroll to
}

interface DrawerContextProps {
    drawerState: DrawerState;
    openDrawer: (type: DrawerType, params?: { highlightCategory?: string; highlightId?: number }) => void;
    closeDrawer: () => void;
}

const DrawerContext = createContext<DrawerContextProps | undefined>(undefined);

export function DrawerProvider({ children }: { children: ReactNode }) {
    const [drawerState, setDrawerState] = useState<DrawerState>({
        isOpen: false,
        type: null
    });

    const openDrawer = (type: DrawerType, params?: { highlightCategory?: string; highlightId?: number }) => {
        setDrawerState({
            isOpen: true,
            type,
            highlightCategory: params?.highlightCategory,
            highlightId: params?.highlightId
        });
    };

    const closeDrawer = () => {
        setDrawerState(prev => ({ ...prev, isOpen: false }));
    };

    return (
        <DrawerContext.Provider value={{ drawerState, openDrawer, closeDrawer }}>
            {children}
        </DrawerContext.Provider>
    );
}

export function useDrawer() {
    const context = useContext(DrawerContext);
    if (!context) {
        throw new Error("useDrawer must be used within a DrawerProvider");
    }
    return context;
}
