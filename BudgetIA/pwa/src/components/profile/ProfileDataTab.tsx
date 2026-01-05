import { useState, useEffect } from 'react';
import { User, LogOut, Save } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { GlassCard } from '../ui/GlassCard';
import { GradientBanner } from '../ui/GradientBanner';
import type { ProfileItem } from '../../hooks/useProfile';

interface Props {
    data: ProfileItem[];
    onSave: (data: ProfileItem[]) => Promise<any>;
    isSaving: boolean;
}

export function ProfileDataTab({ data, onSave, isSaving }: Props) {
    const [formData, setFormData] = useState<ProfileItem[]>([]);

    useEffect(() => {
        if (data && data.length > 0) {
            setFormData(data);
        }
    }, [data]);

    const handleEdit = (index: number, value: string) => {
        const newData = [...formData];
        newData[index] = { ...newData[index], Valor: value };
        setFormData(newData);
    };

    return (
        <div className="space-y-6">
            <GradientBanner 
                icon={User}
                title="Dados Pessoais"
                description="Informações que a IA usa para personalizar o atendimento."
                variant="emerald"
            />

            <GlassCard variant="emerald" className="divide-y divide-border overflow-hidden" hoverEffect={false}>
                {formData.map((item, idx) => (
                    <div key={idx} className="p-4 hover:bg-surface-hover/80 transition-colors flex flex-col md:flex-row md:items-center gap-2">
                        <div className="md:w-1/3">
                            <span className="text-sm font-medium text-text-muted">{item.Campo}</span>
                        </div>
                        <div className="md:w-2/3">
                            <Input 
                                onChange={(e) => handleEdit(idx, e.target.value)}
                                className="w-full bg-surface-input/50" // Small adjustment to background if needed, but keeping standard is safer
                                placeholder="Valor..."
                            />
                        </div>
                    </div>
                ))}
                {formData.length === 0 && (
                        <div className="p-8 text-center text-text-muted">Nenhum dado de perfil encontrado.</div>
                )}
            </GlassCard>

            <div className="flex justify-between items-center pt-2 gap-4">
                <Button 
                    onClick={() => {
                        if(confirm("Deseja sair da conta?")) {
                            localStorage.clear();
                            window.location.reload();
                        }
                    }}
                    variant="danger-outline"
                    icon={LogOut}
                    className="w-full md:w-auto"
                >
                    Sair da Conta
                </Button>

                <Button 
                    onClick={() => onSave(formData)}
                    variant="primary"
                    icon={Save}
                    className="w-full md:w-auto md:px-8"
                    isLoading={isSaving}
                >
                    Salvar Dados
                </Button>
            </div>
        </div>
    );
}
