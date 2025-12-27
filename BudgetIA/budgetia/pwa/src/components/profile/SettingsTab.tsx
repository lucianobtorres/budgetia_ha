import { useState } from 'react';
import { Settings, HelpCircle, FileSpreadsheet, CheckCircle, XCircle, ShieldAlert, HardDrive, ChevronDown, ChevronUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import { GlassCard } from '../ui/GlassCard';
import { GradientBanner } from '../ui/GradientBanner';
import { PushNotificationCard } from './PushNotificationCard';
import type { DriveStatus } from '../../hooks/useProfile';
import { useTour } from '../../context/TourContext';

interface Props {
    driveStatus: DriveStatus | undefined;
    onShareDrive: () => void;
    onRevokeDrive: () => void;
    onResetProfile: (fastTrack: boolean) => void;
}

export function SettingsTab({ driveStatus, onShareDrive, onRevokeDrive, onResetProfile }: Props) {
    const [isDangerZoneOpen, setIsDangerZoneOpen] = useState(false);
    const { resetTours } = useTour();
    const navigate = useNavigate();

    const handleDriveRevoke = () => {
        if(confirm("Tem certeza? O Agente não poderá mais atualizar a planilha em segundo plano.")) {
            onRevokeDrive();
        }
    };

    const handleReset = (fastTrack: boolean) => {
        const msg = fastTrack 
            ? "Reiniciar configuração (Fast Track)?" 
            : "ATENÇÃO: Isso apagará TODOS os dados e reiniciará o tutorial. Continuar?";
        
        if (confirm(msg)) {
            onResetProfile(fastTrack);
        }
    };

    return (
        <div className="space-y-6">
            <GradientBanner 
                icon={Settings}
                title="Configurações da Conta"
                description="Gerencie seu acesso e integrações."
                variant="blue"
            />
            
            <PushNotificationCard />

            {/* Tour / Help Section */}
            <GlassCard variant="emerald" className="p-6 flex items-center justify-between group cursor-pointer" 
                onClick={() => {
                    resetTours();
                    navigate('/', { state: { restartTour: true } });
                }}
            >
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400 group-hover:bg-emerald-500/20 transition-colors">
                        <HelpCircle size={24} />
                    </div>
                    <div>
                        <h3 className="text-white font-bold">Reiniciar Dicas de Uso</h3>
                        <p className="text-sm text-gray-400">Ver novamente o tour guiado pelo painel.</p>
                    </div>
                </div>
                <div className="text-emerald-500">
                    →
                </div>
            </GlassCard>

            {driveStatus && driveStatus.is_google_sheet && (
                <GlassCard className="p-6">
                    <div className="flex items-center space-x-3 mb-6">
                        <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500">
                            <FileSpreadsheet size={24} />
                        </div>
                        <div>
                                <h3 className="text-lg font-bold text-white">Google Drive</h3>
                                <p className="text-xs text-gray-500">Conexão Backend</p>
                        </div>
                    </div>
                    
                    <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800 mb-6 text-sm text-gray-300 leading-relaxed">
                        Para que o Agendador de Tarefas e o Bot do Telegram funcionem quando você não está com o app aberto, é necessário autorizar o acesso backend à planilha.
                    </div>

                    <div className="flex items-center justify-between bg-gray-900 p-4 rounded-xl border border-gray-800 mb-6">
                        <span className="text-sm font-medium text-white">Status</span>
                        {driveStatus.backend_consent ? (
                            <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
                                <CheckCircle size={16} />
                                <span className="text-xs uppercase font-bold">Ativo</span>
                            </div>
                        ) : (
                            <div className="flex items-center space-x-2 text-gray-500 bg-gray-800 px-3 py-1 rounded-lg border border-gray-700">
                                <XCircle size={16} />
                                <span className="text-xs uppercase font-bold">Inativo</span>
                            </div>
                        )}
                    </div>

                    {!driveStatus.has_credentials ? (
                            <div className="text-sm text-yellow-500 bg-yellow-900/20 p-4 rounded-xl border border-yellow-900/50 mb-4 flex gap-3 items-start">
                            <ShieldAlert className="shrink-0 mt-0.5" size={16} />
                            <span>Você precisa fazer login com Google para habilitar este recurso.</span>
                            </div>
                    ) : (
                        driveStatus.backend_consent ? (
                            <Button
                                onClick={handleDriveRevoke}
                                variant="outline"
                                className="w-full"
                            >
                                Revogar Acesso Backend
                            </Button>
                        ) : (
                            <Button
                                onClick={onShareDrive}
                                variant="primary"
                                className="w-full shadow-lg shadow-emerald-900/20"
                            >
                                Autorizar Acesso Backend
                            </Button>
                        )
                    )}
                </GlassCard>
            )}

            <div className="bg-red-950/10 border border-red-900/30 rounded-xl overflow-hidden transition-all">
                    <button 
                    onClick={() => setIsDangerZoneOpen(!isDangerZoneOpen)}
                    className="w-full p-6 flex items-center justify-between hover:bg-red-900/5 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                        <div className="p-2 bg-red-500/10 rounded-lg text-red-500">
                            <HardDrive size={20} />
                        </div>
                        <div className="text-left">
                            <h3 className="text-lg font-bold text-red-400">Zona de Perigo</h3>
                            <p className="text-xs text-red-300/50">Ações irreversíveis e resets.</p>
                        </div>
                        </div>
                        
                        {isDangerZoneOpen ? <ChevronUp className="text-red-400" /> : <ChevronDown className="text-red-400" />}
                    </button>
                    
                    {isDangerZoneOpen && (
                        <div className="px-6 pb-6 pt-0 animate-in slide-in-from-top-2 duration-200">
                            <div className="h-px bg-red-900/30 mb-6" /> {/* Divider */}
                            
                            <div className="grid grid-cols-1 gap-3">
                            <button 
                                onClick={() => handleReset(false)}
                                className="w-full text-red-400 hover:text-red-300 text-sm font-medium border border-red-900/50 p-3 rounded-xl hover:bg-red-900/20 transition-colors text-left flex items-center gap-3"
                            >
                                <span className="text-lg">💥</span>
                                <div className="flex-1">
                                    <div className="font-bold">Reset Completo</div>
                                    <div className="text-xs opacity-70">Apaga tudo e reinicia tutorial</div>
                                </div>
                            </button>

                            <button 
                                onClick={() => handleReset(true)}
                                className="w-full text-orange-400 hover:text-orange-300 text-sm font-medium border border-orange-900/50 p-3 rounded-xl hover:bg-orange-900/20 transition-colors text-left flex items-center gap-3"
                            >
                                <span className="text-lg">🚀</span>
                                <div className="flex-1">
                                    <div className="font-bold">Reset Rápido</div>
                                    <div className="text-xs opacity-70">Reinicia sem tutorial</div>
                                </div>
                            </button>
                            </div>
                        </div>
                    )}
            </div>
        </div>
    );
}
