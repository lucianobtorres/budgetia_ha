import type { TransactionCreate, TransactionUpdate } from '../../types/api';
import type { Transaction } from '../models/Transaction';

export interface ITransactionRepository {
    list(filters?: { month?: number; year?: number; limit?: number }): Promise<Transaction[]>;
    create(data: TransactionCreate): Promise<void>;
    createBatch(data: TransactionCreate[]): Promise<{ message: string }>;
    update(id: number, data: TransactionUpdate): Promise<void>;
    delete(id: number): Promise<void>;
}
