import type { ProfileItem, ProfileSchema } from '../../domain/models/Profile';
import { createProfileFromSchema } from '../../domain/models/Profile';
import { fetchAPI } from '../../services/api';

export class ApiProfileRepository {
    async getProfile(): Promise<ProfileItem[]> {
        const data = await fetchAPI<ProfileSchema[]>('/profile/');
        return (data || []).map(createProfileFromSchema);
    }

    async updateProfile(items: ProfileItem[]): Promise<void> {
        // Map back to API schema if necessary, or update backend to accept clean fields
        const schemaItems = items.map(item => ({
            Campo: item.field,
            Valor: item.value,
            Observações: item.observations
        }));
        await fetchAPI('/profile/bulk', {
            method: 'PUT',
            body: JSON.stringify(schemaItems),
        });
    }
}
