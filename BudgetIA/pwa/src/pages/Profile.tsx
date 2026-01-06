import { useState } from 'react';
import { User, Download, Settings, CreditCard, Tag } from 'lucide-react';
import { toast } from 'sonner';

import { PageHeader } from '../components/ui/PageHeader';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { Button } from '../components/ui/Button';
import { STORAGE_KEYS } from '../utils/constants';

import { useProfile } from '../hooks/useProfile';
import { ProfileDataTab } from '../components/profile/ProfileDataTab';
import { SettingsTab } from '../components/profile/SettingsTab';
import { SubscriptionTab } from '../components/profile/SubscriptionTab';
import { CategoriesTab } from '../components/profile/CategoriesTab';


export default function Profile() {
    const [activeTab, setActiveTab] = useState<'profile' | 'categories' | 'settings' | 'subscription'>('profile');
    
    // Hook handles all data fetching and mutations
    const { 
        profileData, 
        driveStatus, 
        isLoading, 
        saveProfile, 
        shareDrive, 
        revokeDrive,
        resetProfile,
        isSaving
    } = useProfile();

    const handleExport = async () => {
        try {
            const currentUserId = localStorage.getItem(STORAGE_KEYS.USER_ID) || '';
            const response = await fetch('/api/dashboard/export', { 
                headers: { 'X-User-ID': currentUserId }
            });
            if (!response.ok) throw new Error('Falha no download');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'budgetia_export.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            toast.error('Erro ao exportar arquivo.');
            console.error(error);
        }
    };

    const tabs = [
        { id: 'profile', label: 'Dados', icon: User, color: 'text-emerald-400' },
        { id: 'categories', label: 'Categorias', icon: Tag, color: 'text-orange-400' },
        { id: 'subscription', label: 'Assinatura', icon: CreditCard, color: 'text-purple-400' },
        { id: 'settings', label: 'Conta', icon: Settings, color: 'text-blue-400' }
    ] as const;

    return (
        <div className="h-full flex flex-col gap-6 overflow-hidden">
            {/* Fixed Header */}
             <div className="flex-none pt-safe space-y-4">
                <PageHeader 
                    title="Seu Perfil" 
                    description="Gerencie seus dados e a IA."
                    className="pt-0 !space-y-0"
                    action={
                        <div className="flex space-x-2">
                             <Button 
                                 onClick={handleExport}
                                 variant="neutral"
                                 title="Backup Excel"
                                 icon={Download}
                             >
                                 <span className="hidden md:inline">Backup</span>
                             </Button>
                        </div>
                    }
                />

                {/* Tabs */}
                <SegmentedControl 
                    options={tabs.map(t => ({ id: t.id, label: t.label, icon: t.icon, activeColor: t.color }))}
                    value={activeTab}
                    onChange={(val) => setActiveTab(val as any)}
                />
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto pb-20 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-gutter-stable">
                <div className="bg-gray-900/30 border border-gray-800/50 rounded-2xl p-6 min-h-[300px]">
                    {isLoading ? (
                        <div className="flex items-center justify-center h-40 text-gray-400 gap-2">
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                        </div>
                    ) : (
                        <div className="max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
                            {activeTab === 'profile' && (
                                <ProfileDataTab 
                                    data={profileData} 
                                    onSave={saveProfile} 
                                    isSaving={isSaving} 
                                />
                            )}

                            {activeTab === 'categories' && (
                                <CategoriesTab />
                            )}

                            {activeTab === 'subscription' && (
                                <SubscriptionTab />
                            )}

                            {activeTab === 'settings' && (
                                <SettingsTab 
                                    driveStatus={driveStatus} 
                                    onShareDrive={shareDrive}
                                    onRevokeDrive={revokeDrive}
                                    onResetProfile={resetProfile}
                                />
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
