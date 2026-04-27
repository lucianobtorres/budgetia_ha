import { useContext } from 'react';
import { DrawerContext, type DrawerContextProps } from '../context/DrawerContext';

export function useDrawer(): DrawerContextProps {
    const context = useContext(DrawerContext);
    if (!context) {
        throw new Error("useDrawer must be used within a DrawerProvider");
    }
    return context;
}
