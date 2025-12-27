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
        let baseStyle = "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/20";
        let onClick = () => onSelect(option);

        if (option.includes("Upload") || option.includes("📤")) {
            icon = <Upload className="w-4 h-4" />;
            baseStyle = "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/20";
            onClick = onUploadClick;
        } else if (option.includes("Google") || option.includes("☁️")) {
             icon = <Cloud className="w-4 h-4" />;
             baseStyle = "bg-orange-600 hover:bg-orange-500 text-white shadow-orange-900/20";
             onClick = onGoogleClick;
        } else if (option.includes("Zero") || option.includes("🚀")) {
             icon = <FileSpreadsheet className="w-4 h-4" />;
        } else if (option.includes("Certo") || option.includes("✅")) {
             icon = <CheckCircle className="w-4 h-4" />;
             baseStyle = "bg-green-600 hover:bg-green-500 text-white shadow-green-900/20";
        }

        return (
            <button
                key={option}
                onClick={onClick}
                disabled={disabled}
                className={cn(
                    "flex items-center gap-2 px-6 py-3 rounded-xl font-medium shadow-lg transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 disabled:cursor-not-allowed backdrop-blur-sm",
                    baseStyle
                )}
            >
                {icon}
                {option}
            </button>
        );
    };

    return (
        <div className="flex flex-wrap gap-3 justify-center mb-4 p-2">
            {options.map(renderButton)}
        </div>
    );
}
