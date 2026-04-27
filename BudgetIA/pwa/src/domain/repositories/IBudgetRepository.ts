import type { BudgetCreate } from '../../types/api';
import type { Budget } from '../models/Budget';

export interface IBudgetRepository {
    list(): Promise<Budget[]>;
    create(data: BudgetCreate): Promise<void>;
    update(id: number, data: BudgetCreate): Promise<void>;
    delete(id: number): Promise<void>;
}
