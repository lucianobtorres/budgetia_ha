// utils/colors.ts


function getHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash;
    }
    return Math.abs(hash);
}

/**
 * Generates a color based on Rank (Index) using the Golden Angle.
 * This guarantees that the top items (Rank 0, 1, 2...) have maximally distinct colors,
 * regardless of their semantic meaning.
 * 
 * If a category grows in value and moves up the rank, its color will change 
 * to reflect its new position in the distribution.
 */
export function getRankedColor(index: number): string {
    // Golden Angle = 137.508 degrees
    const goldenAngle = 137.508;
    
    // Start Hue: 0 (Red) is common for "Hot/High" items, or we can use 
    // a different start. Let's stick to the Golden Angle distribution.
    // Index 0 = Base Hue.
    
    // We can use a base hue offset if we want to avoid pure red as #1 if preferred,
    // but usually for "Top Expense", distinctiveness is key.
    const startHue = 0; 
    
    const hue = (startHue + (index * goldenAngle)) % 360;
    
    // High saturation, good visibility lightness
    return `hsl(${hue.toFixed(1)}, 75%, 55%)`;
}

// Deprecated alias to maintain compatibility if needed, or we can refactor all callers.
// Let's redirect getSeverityColor to this new logic since the user essentially wants 
// "Severity" (Rank) -> Color.
export const getSeverityColor = getRankedColor;

/**
 * Fallback for when rank is unknown.
 */
export function getCategoryColor(category: string): string {
    // Hash-based fallback
    const i = getHash(category);
    return getRankedColor(i + 100); // Offset to avoid clashing with top ranks visually
}


export function getCategoryTextColor(): string {
    return "text-white"; 
}
