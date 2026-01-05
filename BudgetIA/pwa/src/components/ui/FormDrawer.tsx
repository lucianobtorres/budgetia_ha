import { Drawer } from "./Drawer";
import { Button } from "./Button";

interface FormDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    isLoading?: boolean;
    isEditing?: boolean;
    onSubmit: (e: React.FormEvent) => void;
    formId: string;
    children: React.ReactNode;
    submitLabel?: string;
    loadingLabel?: string;
}

export function FormDrawer({
    isOpen,
    onClose,
    title,
    isLoading,
    isEditing,
    onSubmit,
    formId,
    children,
    submitLabel = "Salvar",
    loadingLabel = "Salvando..."
}: FormDrawerProps) {
    return (
        <Drawer
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            action={
                <Button
                    type="submit"
                    form={formId}
                    disabled={isLoading}
                    variant="primary"
                    className="font-semibold px-6"
                >
                    {isLoading ? '...' : submitLabel}
                </Button>
            }
        >
            <form id={formId} onSubmit={onSubmit} className="space-y-5 pb-safe pt-2 relative">
                {isLoading && (
                    <div className="absolute inset-0 z-50 bg-surface-card/60 backdrop-blur-[2px] flex items-center justify-center rounded-xl transition-all duration-300">
                        <div className="flex flex-col items-center gap-3">
                            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-xs font-medium text-primary-light animate-pulse">{loadingLabel}</span>
                        </div>
                    </div>
                )}
                {children}
            </form>
        </Drawer>
    );
}
