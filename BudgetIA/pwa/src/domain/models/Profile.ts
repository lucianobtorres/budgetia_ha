export interface ProfileItem {
    field: string;
    value: string;
    observations?: string;
}

export interface ProfileSchema {
    Campo: string;
    Valor: string;
    Observações?: string;
}

export function createProfileFromSchema(schema: ProfileSchema): ProfileItem {
    return {
        field: schema.Campo || '',
        value: schema.Valor || '',
        observations: schema.Observações || '',
    };
}
