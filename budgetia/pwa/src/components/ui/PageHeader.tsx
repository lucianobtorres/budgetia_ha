import type { ReactNode } from "react";

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
                     <h2 className="text-xl md:text-3xl font-bold tracking-tight text-white mb-1">{title}</h2>
                     {description && <p className="text-sm text-gray-400">{description}</p>}
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
