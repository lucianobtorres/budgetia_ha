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
        <div className={cn("bg-gray-900/50 p-1 rounded-xl border border-gray-800 flex overflow-x-auto scrollbar-none", className)}>
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
                                ? "bg-gray-800 text-white shadow-sm ring-1 ring-gray-700"
                                : "text-gray-400 hover:text-white hover:bg-gray-800/50"
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
