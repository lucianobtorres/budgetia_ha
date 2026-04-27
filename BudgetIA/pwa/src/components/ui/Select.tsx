import React, { useRef, useState } from 'react';
import { cn } from '../../utils/cn';
import { ChevronDown, Check } from 'lucide-react';
import { useOutsideClick } from '../../hooks/useOutsideClick';

export interface SelectOption {
    label: string;
    value: string;
}

export interface SelectChangeEvent {
    target: { value: string; name?: string };
}

export interface SelectProps {
    value?: string;
    onChange?: (e: SelectChangeEvent) => void;
    options?: SelectOption[];
    placeholder?: string;
    icon?: React.ElementType;
    variant?: 'default' | 'glass';
    containerClassName?: string;
    className?: string;
    disabled?: boolean;
    children?: React.ReactNode;
}

export function Select({ 
    value, 
    onChange, 
    options = [], 
    placeholder = "Selecione...", 
    icon: Icon, 
    variant = 'default', 
    containerClassName, 
    className,
    disabled = false,
    children
}: SelectProps) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    
    const derivedOptions = React.useMemo(() => {
        if (options.length > 0) return options;
        if (!children) return [];

        const opts: SelectOption[] = [];
        React.Children.forEach(children, (child) => {
            if (React.isValidElement(child) && child.type === 'option') {
                 const props = child.props as { children: string; value: string };
                 opts.push({ 
                     label: props.children, 
                     value: props.value 
                 });
            }
        });
        return opts;
    }, [children, options]);

    useOutsideClick(containerRef, () => setIsOpen(false));

    const selectedOption = derivedOptions.find(opt => opt.value === value);

    const handleSelect = (val: string) => {
        if (disabled) return;
        setIsOpen(false);
        if (onChange) {
            // Mocking native event for compatibility with existing form handlers
            onChange({ target: { value: val } });
        }
    };

    const variants = {
        default: "bg-surface-input border-border hover:border-primary/50",
        glass: "bg-gray-900/50 border-gray-700 text-white hover:border-emerald-500/50"
    };

    const activeRing = isOpen ? "ring-1 ring-primary border-primary" : "";

    return (
        <div 
            ref={containerRef} 
            className={cn("relative flex-1", containerClassName)}
        >
            {/* Trigger Button */}
            <div 
                onClick={() => !disabled && setIsOpen(!isOpen)}
                className={cn(
                    "relative flex w-full items-center rounded-xl border px-3 py-2 text-sm transition-all cursor-pointer h-11",
                    variants[variant],
                    activeRing,
                    disabled && "cursor-not-allowed opacity-50",
                    className
                )}
            >
                {Icon && (
                    <div className="mr-2 text-gray-400">
                        <Icon size={16} />
                    </div>
                )}
                
                <span className={cn("flex-1 truncate", !selectedOption && "text-gray-500")}>
                    {selectedOption ? selectedOption.label : placeholder}
                </span>

                <div className="ml-2 text-gray-400">
                    <ChevronDown size={16} className={cn("transition-transform duration-200", isOpen && "rotate-180")} />
                </div>
            </div>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute z-50 mt-1 w-full max-h-60 overflow-auto rounded-xl border border-gray-700 bg-gray-900 shadow-xl shadow-black/50 py-1">
                    {derivedOptions.length > 0 ? (
                        derivedOptions.map((opt) => (
                            <div
                                key={opt.value}
                                onClick={() => handleSelect(opt.value)}
                                className={cn(
                                    "flex items-center justify-between px-3 py-2 text-sm cursor-pointer transition-colors",
                                    "hover:bg-emerald-500/10 hover:text-emerald-400",
                                    value === opt.value ? "text-emerald-400 bg-emerald-500/5" : "text-gray-300"
                                )}
                            >
                                <span className="truncate">{opt.label}</span>
                                {value === opt.value && <Check size={14} />}
                            </div>
                        ))
                    ) : (
                        <div className="px-3 py-2 text-sm text-gray-500 text-center">
                            Sem opções
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
