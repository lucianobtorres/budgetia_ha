import type { CategoryCreate, CategorySchema } from '../../types/api';
import type { Category } from '../../domain/models/Category';
import { createCategoryFromSchema } from '../../domain/models/Category';
import { fetchAPI } from '../../services/api';

export class ApiCategoryRepository {
    async list(): Promise<Category[]> {
        const data = await fetchAPI<CategorySchema[]>('/categories/');
        return (data || []).map(createCategoryFromSchema);
    }

    async create(data: CategoryCreate): Promise<void> {
        await fetchAPI('/categories/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async update(oldName: string, data: CategoryCreate): Promise<void> {
        await fetchAPI(`/categories/${encodeURIComponent(oldName)}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(name: string): Promise<void> {
        await fetchAPI(`/categories/${encodeURIComponent(name)}`, {
            method: 'DELETE',
        });
    }
}
