import type { LucideIcon } from "lucide-react";
import { cn } from "../../utils/cn";

export type BannerVariant = 'emerald' | 'violet' | 'orange' | 'blue' | 'yellow' | 'green' | 'red';

interface GradientBannerProps {
    icon: LucideIcon;
    title: string;
    description: string;
    variant?: BannerVariant;
    className?: string;
}

const VARIANTS = {
    emerald: {
        container: "from-primary/10 border-primary/20",
        iconBg: "bg-primary/20 text-primary-light",
        desc: "text-primary-light/60"
    },
    violet: {
        container: "from-violet-500/10 border-violet-500/20",
        iconBg: "bg-violet-500/20 text-violet-400",
        desc: "text-violet-200/60"
    },
    orange: {
        container: "from-orange-500/10 border-orange-500/20",
        iconBg: "bg-orange-500/20 text-orange-400",
        desc: "text-orange-200/60"
    },
    blue: {
        container: "from-blue-500/10 border-blue-500/20",
        iconBg: "bg-blue-500/20 text-blue-400",
        desc: "text-blue-200/60"
    },
    yellow: {
        container: "from-yellow-500/10 border-yellow-500/20",
        iconBg: "bg-yellow-500/20 text-yellow-400",
        desc: "text-yellow-200/60"
    },
    green: {
        container: "from-green-500/10 border-green-500/20",
        iconBg: "bg-green-500/20 text-green-400",
        desc: "text-green-200/60"
    },
    red: {
         container: "from-red-500/10 border-red-500/20",
         iconBg: "bg-red-500/20 text-red-400",
         desc: "text-red-200/60"
    }
};

export function GradientBanner({ icon: Icon, title, description, variant = 'emerald', className }: GradientBannerProps) {
    const styles = VARIANTS[variant] || VARIANTS.emerald;

    return (
        <div className={cn(
            "bg-gradient-to-br to-transparent p-6 rounded-xl border mb-6", 
            styles.container,
            className
        )}>
            <div className="flex items-center gap-4">
                <div className={cn("p-3 rounded-full", styles.iconBg)}>
                    <Icon size={32} />
                </div>
                <div>
                    <h3 className="text-xl font-bold text-white">{title}</h3>
                    <p className={cn("text-sm", styles.desc)}>{description}</p>
                </div>
            </div>
        </div>
    );
}
