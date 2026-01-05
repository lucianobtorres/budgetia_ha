import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '../services/api';
import { toast } from 'sonner';

// Interfaces
export interface ProfileItem {
    Campo: string;
    Valor: string;
    Observações?: string;
    [key: string]: any;
}

export interface DriveStatus {
    has_credentials: boolean;
    backend_consent: boolean;
    is_google_sheet: boolean;
    planilha_path: string;
}

export function useProfile() {
    const queryClient = useQueryClient();

    // Queries
    const profileQuery = useQuery({
        queryKey: ['profile'],
        queryFn: () => fetchAPI('/profile/') as Promise<ProfileItem[]>,
        staleTime: 1000 * 60 * 5 // 5 minutes
    });

    const driveQuery = useQuery({
        queryKey: ['driveSettings'],
        queryFn: () => fetchAPI('/profile/settings/google-drive') as Promise<DriveStatus>,
        staleTime: 1000 * 60 * 5
    });

    // Mutations
    const saveProfileMutation = useMutation({
        mutationFn: (data: ProfileItem[]) => fetchAPI('/profile/bulk', {
            method: 'PUT',
            body: JSON.stringify(data)
        }),
        onSuccess: () => {
            toast.success('Perfil atualizado com sucesso!');
            queryClient.invalidateQueries({ queryKey: ['profile'] });
        },
        onError: () => toast.error('Erro ao salvar perfil.')
    });

     const shareDriveMutation = useMutation({
        mutationFn: () => fetchAPI('/profile/settings/google-drive/share', { method: 'POST' }),
        onSuccess: (res) => {
             toast.success(res.message);
             queryClient.invalidateQueries({ queryKey: ['driveSettings'] });
        },
        onError: () => toast.error('Erro ao habilitar Google Drive.')
    });

    const revokeDriveMutation = useMutation({
         mutationFn: () => fetchAPI('/profile/settings/google-drive/revoke', { method: 'POST' }),
         onSuccess: (res) => {
              toast.success(res.message);
              queryClient.invalidateQueries({ queryKey: ['driveSettings'] });
         },
         onError: () => toast.error('Erro ao desabilitar Google Drive.')
    });
    
    const resetProfileMutation = useMutation({
        mutationFn: (fastTrack: boolean) => fetchAPI('/profile/reset', { 
            method: 'POST',
            body: JSON.stringify({ fast_track: fastTrack })
        }),
        onSuccess: () => {
             // Limpa apenas chaves de estado de UI, mantendo sessão/token
             localStorage.removeItem('budgetia_tour_completed');
             window.location.reload();
        },
        onError: () => toast.error('Erro ao resetar.')
    });

    return {
        // Data
        profileData: profileQuery.data || [],
        driveStatus: driveQuery.data,
        isLoading: profileQuery.isLoading || driveQuery.isLoading,
        
        // Status keys to handle UI loading states explicitly if needed
        isProfileLoading: profileQuery.isLoading,
        
        // Mutations
        saveProfile: saveProfileMutation.mutateAsync,
        shareDrive: shareDriveMutation.mutateAsync,
        revokeDrive: revokeDriveMutation.mutateAsync,
        resetProfile: resetProfileMutation.mutateAsync,
        
        // Loading states for actions
        isSaving: saveProfileMutation.isPending
    };
}
