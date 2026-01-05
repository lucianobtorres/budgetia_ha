import { useState, useEffect } from 'react';
import { useIntelligence } from '../../hooks/useIntelligence';
import { FormDrawer } from '../ui/FormDrawer';
import { Input } from '../ui/Input';
import { Plus, X } from 'lucide-react';
import { toast } from 'sonner';

interface SubscriptionSettingsDrawerProps {
    isOpen: boolean;
    onClose: () => void;
}

export function SubscriptionSettingsDrawer({ isOpen, onClose }: SubscriptionSettingsDrawerProps) {
    const { subscriptionKeywords, updateSubscriptionKeywords } = useIntelligence();
    const [keywords, setKeywords] = useState<string[]>([]);
    const [newKeyword, setNewKeyword] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    // Sync local state with loaded data
    // Sync local state with loaded data
    useEffect(() => {
        if (subscriptionKeywords) {
            // Only update if content is different to avoid infinite loops
            if (JSON.stringify(subscriptionKeywords) !== JSON.stringify(keywords)) {
                setKeywords(subscriptionKeywords);
            }
        }
    }, [subscriptionKeywords]); // Removed keywords from dependency to break loop logic if it existed, though logical check handles it.
    // Actually, keywords dependency would be bad if we setKeywords inside.
    // But `setKeywords` updates `keywords`, causing re-render.
    // If `subscriptionKeywords` reference is stable, this runs once. 
    // If unstable, it runs every render. The stringify check prevents setKeywords call.

    const handleAddKeyword = () => {
        if (!newKeyword.trim()) return;
        
        const term = newKeyword.trim().toLowerCase();
        if (keywords.includes(term)) {
            toast.warning(`'${term}' já está na lista.`);
            return;
        }

        setKeywords([...keywords, term]);
        setNewKeyword('');
    };

    const handleRemoveKeyword = (term: string) => {
        setKeywords(keywords.filter(k => k !== term));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);
        try {
            await updateSubscriptionKeywords(keywords);
            onClose();
        } catch (error) {
            console.error(error);
            // Error handling is centralized in api.ts/hook
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <FormDrawer
            isOpen={isOpen}
            onClose={onClose}
            title="Auditor de Assinaturas"
            isLoading={isSaving}
            onSubmit={handleSubmit}
            formId="subscription-audit-form"
            submitLabel="Salvar Lista"
        >
            <div className="space-y-4">
                <p className="text-sm text-text-secondary">
                    O BudgetIA busca estas palavras-chave nas descrições de suas transações para identificar possíveis assinaturas esquecidas.
                </p>

                <div className="flex gap-2">
                    <Input
                        value={newKeyword}
                        onChange={(e) => setNewKeyword(e.target.value)}
                        placeholder="Ex: Netflix, Spotify..."
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                handleAddKeyword();
                            }
                        }}
                    />
                    <button
                        type="button"
                        onClick={handleAddKeyword}
                        disabled={!newKeyword.trim()}
                        className="p-3 bg-surface-hover rounded-xl hover:bg-surface-active disabled:opacity-50 transition-colors"
                    >
                        <Plus className="w-5 h-5 text-text-primary" />
                    </button>
                </div>

                <div className="flex flex-wrap gap-2 pt-2">
                    {keywords.map(keyword => (
                        <div 
                            key={keyword}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-card border border-border rounded-lg group animate-in fade-in zoom-in duration-200"
                        >
                            <span className="text-sm font-medium text-text-primary capitalize">{keyword}</span>
                            <button
                                type="button"
                                onClick={() => handleRemoveKeyword(keyword)}
                                className="p-0.5 rounded-full hover:bg-red-500/20 hover:text-red-400 text-text-muted transition-colors"
                            >
                                <X className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    ))}
                    {keywords.length === 0 && (
                        <span className="text-sm text-text-muted italic">Nenhuma palavra-chave definida. O auditor usará a lista padrão.</span>
                    )}
                </div>
            </div>
        </FormDrawer>
    );
}
