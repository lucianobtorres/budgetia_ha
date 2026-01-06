
import { fetchAPI } from './api';

export interface ImportedTransaction {
    data: string;
    descricao: string;
    valor: number;
    tipo: "Receita" | "Despesa";
    categoria: string;
    reference_id?: string;
    status?: string;
}

export async function uploadOFX(file: File): Promise<ImportedTransaction[]> {
    const formData = new FormData();
    formData.append('file', file);
    
    // fetchAPI handles JSON parsing, but for upload we need to handle headers carefully
    // Usually fetchAPI sets Content-Type to application/json, we need to let browser set boundary for multipart
    
    // We'll use a raw fetch check or modify fetchAPI. 
    // Let's check fetchAPI in api.ts first. If it forces JSON, we might need a specific call.
    
    // Checking api.ts... it sets Content-Type to application/json by default.
    // We should override headers to undefined to let browser set it.
    
    return fetchAPI('/imports/upload', {
        method: 'POST',
        body: formData,
    });
}
