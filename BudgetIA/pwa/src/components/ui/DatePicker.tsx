import { useState, useRef } from 'react';
import { cn } from '../../utils/cn';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { useOutsideClick } from '../../hooks/useOutsideClick';
import { 
    format, 
    addMonths, 
    subMonths, 
    startOfMonth, 
    endOfMonth, 
    eachDayOfInterval, 
    isSameMonth, 
    isSameDay, 
    isToday, 
    getDay 
} from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface DatePickerProps {
    value?: string; // Expects ISO string YYYY-MM-DD
    onChange?: (e: { target: { value: string } }) => void;
    placeholder?: string;
    variant?: 'default' | 'glass';
    containerClassName?: string;
    className?: string;
    disabled?: boolean;
    required?: boolean; // For visual indication or validation hook
}

export function DatePicker({
    value,
    onChange,
    placeholder = "Selecione uma data",
    variant = 'default',
    containerClassName,
    className,
    disabled = false
}: DatePickerProps) {
    const [isOpen, setIsOpen] = useState(false);
    // Use current date if value is invalid, but only for the view month
    const [viewDate, setViewDate] = useState(() => value ? new Date(value + 'T00:00:00') : new Date());
    
    const containerRef = useRef<HTMLDivElement>(null);

    useOutsideClick(containerRef as any, () => setIsOpen(false));

    const selectedDate = value ? new Date(value + 'T00:00:00') : null;

    const handleSelect = (date: Date) => {
        if (disabled) return;
        setViewDate(date);
        if (onChange) {
            onChange({ target: { value: format(date, 'yyyy-MM-dd') } });
        }
        setIsOpen(false);
    };

    const nextMonth = () => setViewDate(addMonths(viewDate, 1));
    const prevMonth = () => setViewDate(subMonths(viewDate, 1));

    // Calendar Generation
    const monthStart = startOfMonth(viewDate);
    const monthEnd = endOfMonth(viewDate);
    const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd });

    // Padding days for grid alignment
    // getDay returns 0 for Sunday. If we want Monday start, we adjust. 
    // Let's stick to Sunday start (Standard)
    const startDay = getDay(monthStart); 
    const paddingDays = Array.from({ length: startDay });

    const weekDays = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];

    const variants = {
        default: "bg-surface-input border-border hover:border-primary/50",
        glass: "bg-gray-900/50 border-gray-700 text-white hover:border-emerald-500/50"
    };

    const activeRing = isOpen ? "ring-1 ring-primary border-primary" : "";

    return (
        <div ref={containerRef} className={cn("relative flex-1", containerClassName)}>
            {/* Trigger */}
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
                <div className="mr-2 text-gray-400">
                    <CalendarIcon size={16} />
                </div>
                
                <span className={cn("flex-1 truncate", !selectedDate && "text-gray-500")}>
                    {selectedDate ? format(selectedDate, "dd 'de' MMMM, yyyy", { locale: ptBR }) : placeholder}
                </span>

                {/* If needed, we can show a small chevron here too, or just leave it clean */}
            </div>

            {/* Calendar Popover */}
            {isOpen && (
                <div className="absolute z-50 mt-1 w-[280px] p-3 rounded-xl border border-gray-700 bg-gray-900 shadow-xl shadow-black/50 select-none left-0 sm:left-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4">
                        <button type="button" onClick={(e) => { e.preventDefault(); prevMonth() }} className="p-1 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
                            <ChevronLeft size={18} />
                        </button>
                        <span className="font-semibold text-sm capitalize">
                            {format(viewDate, 'MMMM yyyy', { locale: ptBR })}
                        </span>
                        <button type="button" onClick={(e) => { e.preventDefault(); nextMonth() }} className="p-1 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
                            <ChevronRight size={18} />
                        </button>
                    </div>

                    {/* Week Days */}
                    <div className="grid grid-cols-7 mb-2 text-center">
                        {weekDays.map((day, i) => (
                            <span key={i} className="text-xs font-medium text-gray-500">{day}</span>
                        ))}
                    </div>

                    {/* Days Grid */}
                    <div className="grid grid-cols-7 gap-1">
                        {paddingDays.map((_, i) => <div key={`pad-${i}`} />)}
                        
                        {daysInMonth.map((date) => {
                            const isSelected = selectedDate ? isSameDay(date, selectedDate) : false;
                            const isTodayDate = isToday(date);
                            
                            return (
                                <button
                                    key={date.toString()}
                                    type="button"
                                    onClick={(e) => { e.preventDefault(); handleSelect(date); }}
                                    className={cn(
                                        "h-8 w-8 rounded-lg flex items-center justify-center text-sm transition-colors relative group",
                                        isSelected 
                                            ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30" 
                                            : "text-gray-300 hover:bg-gray-800",
                                        isTodayDate && !isSelected && "text-emerald-400 font-bold"
                                    )}
                                >
                                    {format(date, 'd')}
                                    {isTodayDate && !isSelected && (
                                        <div className="absolute bottom-1 w-1 h-1 bg-emerald-500 rounded-full" />
                                    )}
                                </button>
                            );
                        })}
                    </div>
                    
                    {/* Footer - Today Shortcut */}
                    <div className="mt-3 pt-3 border-t border-gray-800">
                         <button 
                            type="button"
                            onClick={(e) => { e.preventDefault(); handleSelect(new Date()) }}
                            className="w-full text-xs text-center text-emerald-400 hover:text-emerald-300 font-medium py-1"
                         >
                            Hoje
                         </button>
                    </div>
                </div>
            )}
        </div>
    );
}
