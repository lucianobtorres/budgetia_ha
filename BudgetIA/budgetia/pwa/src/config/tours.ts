export interface TourStep {
    targetId: string;
    title: string;
    content: string;
}

export const TOURS = {
    // Cenário 1: Novo Usuário (Sem Dados)
    dashboard_empty: [
        { 
            targetId: 'welcome-header', 
            title: 'Bem-vindo ao BudgetIA', 
            content: 'Seu assistente financeiro pessoal começa aqui. Esta é sua tela principal.' 
        },
        { 
            targetId: 'notification-bell', 
            title: 'Central de Notificações', 
            content: 'Fique de olho aqui. O Jarvis te avisará sobre insights importantes ou se faltar alguma informação.' 
        },
        { 
            targetId: 'chat-widget', 
            title: 'Seu Jarvis Financeiro', 
            content: 'Esta é a parte principal. Converse com a IA aqui para adicionar transações ("Gastei 50 no almoço") ou tirar dúvidas.' 
        }
    ],

    // Cenário 2: Usuário Ativo (Com Dados) - Inclui Onboarding + Análise
    dashboard_full: [
        { 
            targetId: 'welcome-header', 
            title: 'Seu Painel', 
            content: 'Bem-vindo de volta! Aqui você tem a visão geral da sua saúde financeira.' 
        },
        { 
            targetId: 'notification-bell', 
            title: 'Central de Notificações', 
            content: 'Fique de olho aqui. O Jarvis te avisará sobre insights importantes ou se faltar alguma informação.' 
        },
        { 
            targetId: 'kpi-grid', 
            title: 'Indicadores Principais', 
            content: 'Aqui você vê o resumo do mês: Saldo, Receitas e Despesas. Mantenha o saldo no verde!' 
        },
        { 
            targetId: 'budget-widget', 
            title: 'Orçamentos', 
            content: 'Acompanhe o progresso das suas metas de gasto mensais.' 
        },
        { 
            targetId: 'category-chart', 
            title: 'Análise de Categorias', 
            content: 'Veja onde seu dinheiro está indo. Toque para ver detalhes.' 
        },
        { 
            targetId: 'chat-widget', 
            title: 'Jarvis', 
            content: 'Continue usando o chat para registrar gastos rápidos ou pedir insights profundos.' 
        }
    ],

    // Cenário 3: Página de Transações
    transactions_walkthrough: [
        {
            targetId: 'tx-header',
            title: 'Gerente de Transações',
            content: 'Aqui você visualiza e edita cada gasto ou ganho detalhadamente.'
        },
        {
            targetId: 'tx-add-btn',
            title: 'Nova Transação',
            content: 'Toque aqui para adicionar um gasto manualmente sem usar o chat.'
        },
        {
            targetId: 'tx-filters',
            title: 'Filtros Poderosos',
            content: 'Navegue entre meses ou busque por nome de lojas e categorias.'
        },
        {
            targetId: 'tx-list',
            title: 'Histórico',
            content: 'Aqui aparecerá seu histórico de movimentações. Quando houver itens, toque neles para editar.'
        }
    ]
};
