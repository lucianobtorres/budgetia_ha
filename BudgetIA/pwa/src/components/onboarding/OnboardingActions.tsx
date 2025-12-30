import { Upload, Cloud, FileSpreadsheet, CheckCircle, ArrowRight } from 'lucide-react';
import { cn } from '../../utils/cn';

interface OnboardingActionsProps {
    options: string[];
    onSelect: (option: string) => void;
    onUploadClick: () => void;
    onGoogleClick: () => void;
    disabled?: boolean;
}

export function OnboardingActions({ options, onSelect, onUploadClick, onGoogleClick, disabled }: OnboardingActionsProps) {
    if (!options || options.length === 0) return null;

    const renderButton = (option: string) => {
        let icon = <ArrowRight className="w-4 h-4" />;
        // Default style: Chip style (Outlined, subtle bg, hover effect)
        let baseStyle = "bg-surface-card/50 border border-border text-text-secondary hover:border-primary/50 hover:bg-surface-hover hover:text-primary";
        let onClick = () => onSelect(option);

        if (option.includes("Upload") || option.includes("📤")) {
            icon = <Upload className="w-4 h-4" />;
            baseStyle = "bg-blue-950/30 border border-blue-900/50 text-blue-200 hover:border-blue-500/50 hover:bg-blue-900/50 hover:text-blue-100";
            onClick = onUploadClick;
        } else if (option.includes("Google") || option.includes("☁️")) {
             icon = <Cloud className="w-4 h-4" />;
             baseStyle = "bg-orange-950/30 border border-orange-900/50 text-orange-200 hover:border-orange-500/50 hover:bg-orange-900/50 hover:text-orange-100";
             onClick = onGoogleClick;
        } else if (option.includes("Zero") || option.includes("🚀")) {
             icon = <FileSpreadsheet className="w-4 h-4" />;
        } else if (option.includes("Certo") || option.includes("✅")) {
             icon = <CheckCircle className="w-4 h-4" />;
             baseStyle = "bg-primary/20 border border-primary/50 text-primary-light hover:border-primary hover:bg-primary/30 hover:text-white";
        }

        return (
            <button
                key={option}
                onClick={onClick}
                disabled={disabled}
                className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all transform active:scale-95 disabled:opacity-50 disabled:scale-100 disabled:cursor-not-allowed backdrop-blur-sm cursor-pointer shadow-sm hover:shadow-md",
                    baseStyle
                )}
            >
                {icon}
                {option}
            </button>
        );
    };

    return (
        <div className="flex flex-wrap gap-2 justify-start md:justify-center mb-4 p-2 animate-fade-in">
            {options.map(renderButton)}
        </div>
    );
}
