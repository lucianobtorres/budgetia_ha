import type { ReactNode } from "react";
import { Typography } from "./Typography";

interface PageHeaderProps {
    title: string;
    description?: string;
    action?: ReactNode;
    className?: string;
    icon?: React.ElementType;
}

export function PageHeader({ title, description, action, className, icon: Icon }: PageHeaderProps) {
    return (
        <div className={`flex-none pt-safe gap-4 z-10 ${className || ''}`}>
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                     {Icon && <div className="p-2 rounded-lg bg-primary/10 text-primary"><Icon className="w-6 h-6" /></div>}
                     <div>
                        <Typography variant="h2" className="mb-1 border-none">{title}</Typography>
                        {description && <Typography variant="muted" className="text-base">{description}</Typography>}
                     </div>
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
