import { useMemo } from 'react';
import { useExpenses } from './useDashboard';
import { getCategoryColor as getHashColor } from '../utils/colors';
import { TRANSACTION_CATEGORIES } from '../utils/constants';

export function useCategoryColorMap() {
    // Determine ranks based on actual spending (Top 50 is enough for color distribution)
    const { data: expenses } = useExpenses(50);
    // Note: We don't fetch budgets here anymore to strictly align colors with the "Expenses view"

    const colorMap = useMemo(() => {
        const map = new Map<string, string>();
        
        // 1. Compile Unique List of Categories
        // Start with actual expenses (these are the most important ones)
        const activeExpenses = expenses || [];
        const activeNames = new Set(activeExpenses.map(e => e.name));
        
        // Add standard categories that might not have expenses yet (Ranked lower)
        // We create a unified list of { name, value } objects
        const allCategories = [...activeExpenses];
        
        TRANSACTION_CATEGORIES.forEach(cat => {
            if (!activeNames.has(cat)) {
                allCategories.push({
                    name: cat,
                    value: 0
                });
            }
        });

        // 2. Sort Logic
        // Primary: Value (Descending)
        // Secondary: Name (Alphabetical)
        const sorted = allCategories.sort((a, b) => {
            if (b.value !== a.value) return b.value - a.value;
            return a.name.localeCompare(b.name);
        });

        // 3. Golden Angle Distribution
        // Guaranteed distinctiveness by jumping 137.5 degrees for each rank.
        sorted.forEach((item, index) => {
             // Golden Angle 137.508
            const hue = (index * 137.508) % 360;
            const color = `hsl(${hue.toFixed(1)}, 75%, 55%)`;
            
            map.set(item.name, color);
        });

        return map;
    }, [expenses]);

    const getCategoryColor = (category: string) => {
        // Return mapped rank color, or fallback to hash for unknown custom categories
        return colorMap.get(category) || getHashColor(category);
    };

    return { getCategoryColor };
}
