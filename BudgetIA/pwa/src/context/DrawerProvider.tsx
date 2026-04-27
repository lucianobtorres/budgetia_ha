import { useState, type ReactNode } from 'react';
import { DrawerContext, type DrawerState, type DrawerType } from './DrawerContext';

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
