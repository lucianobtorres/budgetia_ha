import { type HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

interface StackProps extends HTMLAttributes<HTMLDivElement> {
    /**
     * Spacing between items (Tailwind spacing scale).
     * e.g. 1 = 0.25rem, 4 = 1rem.
     * Maps to gap-{value}
     * Default: 2
     */
    gap?: number;
    
    /**
     * Vertical alignment of items.
     * Maps to items-{value}
     */
    align?: 'start' | 'end' | 'center' | 'baseline' | 'stretch';
    
    /**
     * Horizontal alignment of items (Justify content).
     * Maps to justify-{value}
     */
    justify?: 'start' | 'end' | 'center' | 'between' | 'around' | 'evenly';

    /**
     * If true, the stack will take up the full width of its parent.
     */
    fullWidth?: boolean;
}

/**
 * Vertical Stack (Column)
 * Flex container with flex-col direction.
 */
export const VStack = forwardRef<HTMLDivElement, StackProps>(({ 
    children, 
    className, 
    gap = 2, 
    align = 'stretch', 
    justify = 'start', 
    fullWidth = false,
    ...props 
}, ref) => {
    return (
        <div 
            ref={ref}
            className={cn(
                "flex flex-col",
                `gap-${gap}`,
                align && `items-${align}`,
                justify && `justify-${justify}`,
                fullWidth && "w-full",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
});

VStack.displayName = "VStack";


/**
 * Horizontal Stack (Row)
 * Flex container with flex-row direction.
 */
export const HStack = forwardRef<HTMLDivElement, StackProps>(({ 
    children, 
    className, 
    gap = 2, 
    align = 'center', 
    justify = 'start',
    fullWidth = false,
    ...props 
}, ref) => {
    return (
        <div 
            ref={ref}
            className={cn(
                "flex flex-row",
                `gap-${gap}`,
                align && `items-${align}`,
                justify && `justify-${justify}`,
                fullWidth && "w-full",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
});

HStack.displayName = "HStack";
