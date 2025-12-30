import { cn } from '../../utils/cn';

interface SegmentedControlOption {
    id: string;
    label: string;
    icon?: React.ElementType;
    activeColor?: string; // Optional tailwind color class e.g. 'text-blue-400'
}

interface SegmentedControlProps {
    options: readonly SegmentedControlOption[];
    value: string;
    onChange: (value: string) => void;
    className?: string;
}

export function SegmentedControl({ options, value, onChange, className }: SegmentedControlProps) {
    return (
        <div className={cn("bg-surface-card/50 p-1 rounded-xl border border-border flex overflow-x-auto scrollbar-none", className)}>
            {options.map((option) => {
                const isActive = value === option.id;
                const Icon = option.icon;
                
                return (
                    <button
                        key={option.id}
                        onClick={() => onChange(option.id)}
                        className={cn(
                            "flex-1 flex items-center justify-center p-3 rounded-lg text-sm font-medium transition-all md:min-w-[100px]",
                            isActive
                                ? "bg-surface-hover text-text-primary shadow-sm ring-1 ring-border-hover"
                                : "text-text-secondary hover:text-text-primary hover:bg-surface-hover/50"
                        )}
                        title={option.label}
                    >
                        {Icon && (
                            <Icon 
                                size={20} 
                                className={cn(isActive && option.activeColor, "md:mr-2")} 
                            />
                        )}
                        <span className="hidden md:inline">{option.label}</span>
                    </button>
                );
            })}
        </div>
    );
}
