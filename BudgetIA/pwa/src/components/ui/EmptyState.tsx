import type { LucideIcon } from "lucide-react";
import { Button } from "./Button";
import { cn } from "../../utils/cn";
import { Typography } from "./Typography";

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
                <div className="p-4 bg-surface-hover rounded-full mb-4">
                    <Icon className="w-8 h-8 text-text-muted" />
                </div>
            )}
            <Typography variant="large" className="text-text-primary mb-2">{title}</Typography>
            <Typography variant="muted" className="max-w-sm mb-6 leading-relaxed">
                {description}
            </Typography>
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
