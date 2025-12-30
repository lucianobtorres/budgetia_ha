import type { ReactNode } from "react";
import { Typography } from "./Typography";

interface PageHeaderProps {
    title: string;
    description?: string;
    action?: ReactNode;
    className?: string;
}

export function PageHeader({ title, description, action, className }: PageHeaderProps) {
    return (
        <div className={`flex-none pt-safe gap-4 z-10 ${className || ''}`}>
            <div className="flex items-start justify-between">
                <div>
                     <Typography variant="h2" className="mb-1 border-none">{title}</Typography>
                     {description && <Typography variant="muted" className="text-base">{description}</Typography>}
                </div>
                {action && (
                    <div className="flex-shrink-0">
                        {action}
                    </div>
                )}
            </div>
        </div>
    );
}
