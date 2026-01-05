
export interface PlanFeature {
    name: string;
    included: boolean;
}

export interface Plan {
    id: string;
    name: string;
    price: string;
    period?: string; // e.g. "/mês"
    description: string;
    features: PlanFeature[];
    variant?: 'default' | 'highlight';
    buttonText?: string;
    isPopular?: boolean;
}

export const PLANS: Plan[] = [
    {
        id: 'free',
        name: 'Gratuito',
        price: 'R$ 0',
        period: '/mês',
        description: 'Ideal para começar.',
        buttonText: 'Começar Grátis',
        features: [
            { name: 'Planilha Mestra (.xlsx)', included: true },
            { name: 'Dashboard Básico', included: true },
            { name: '50 Transações/mês', included: true },
            { name: 'Controle Financeiro', included: true },
            { name: 'IA Básica', included: true },
            { name: 'Sem Consultoria Ativa', included: false },
            { name: 'Sem WhatsApp', included: false },
        ]
    },
    {
        id: 'pro',
        name: 'BudgetIA Pro',
        price: 'R$ 10',
        period: '/mês',
        description: 'Poder total da Inteligência Artificial.',
        variant: 'highlight',
        isPopular: true,
        buttonText: 'Testar 14 dias Grátis',
        features: [
            { name: 'IA Avançada (GPT-4o)', included: true },
            { name: 'Faxineiro Autônomo', included: true },
            { name: 'Integração WhatsApp Ilimitada', included: true },
            { name: 'Observadores Proativos', included: true },
            { name: 'Planilha Mestra + Backup', included: true },
            { name: 'Consultoria Ativa', included: true },
            { name: 'Controle Financeiro', included: true },
        ]
    }
];
