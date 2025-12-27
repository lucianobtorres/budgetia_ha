import type { LucideIcon } from "lucide-react";
import { Button } from "./Button";
import { cn } from "../../utils/cn";

interface EmptyStateProps {
    title: string;
    description: string;
    icon?: LucideIcon;
    actionLabel?: string;
    onAction?: () => void;
    className?: string;
}

export function EmptyState({ 
    title, 
    description, 
    icon: Icon, 
    actionLabel, 
    onAction, 
    className 
}: EmptyStateProps) {
    return (
        <div className={cn("flex flex-col items-center justify-center p-8 text-center h-full min-h-[300px]", className)}>
            {Icon && (
                <div className="p-4 bg-gray-800/50 rounded-full mb-4">
                    <Icon className="w-8 h-8 text-gray-400" />
                </div>
            )}
            <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
            <p className="text-gray-400 max-w-sm mb-6 text-sm leading-relaxed">
                {description}
            </p>
            {actionLabel && onAction && (
                <Button 
                    onClick={onAction}
                    variant="primary"
                    className="rounded-full px-6"
                >
                    {actionLabel}
                </Button>
            )}
        </div>
    );
}
