import type { CategorySchema } from '../../types/api';

export interface Category {
    name: string;
    type: string;
    icon?: string;
    tags?: string;
}

export function createCategoryFromSchema(schema: CategorySchema): Category {
    return {
        name: schema.name || '',
        type: schema.type || '',
        icon: schema.icon || '',
        tags: schema.tags || '',
    };
}
