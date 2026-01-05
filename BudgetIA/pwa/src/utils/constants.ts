export const STORAGE_KEYS = {
    USER_ID: 'budgetia_user_id',
    AUTH_TOKEN: 'budgetia_auth_token',
    USER_ROLE: 'budgetia_user_role',
    TRIAL_ENDS_AT: 'budgetia_trial_ends_at',
    DEPLOY_MODE: 'budgetia_deploy_mode',
    THEME: 'budgetia_theme',
    SIDEBAR_OPEN: 'budgetia_sidebar_open'
} as const;

export const TRANSACTION_CATEGORIES = [
    'Alimentação', 
    'Moradia', 
    'Transporte', 
    'Lazer', 
    'Saúde', 
    'Educação', 
    'Salário', 
    'Investimentos', 
    'Outros'
] as const;

export const DEFAULT_USER_FALLBACK = 'jsmith';

// Generated Public Key for Push Notifications
export const VAPID_PUBLIC_KEY = "BMOc5mPY-YMyvUAKNM7u9swgLRRbq-VdXYCIT1FHO4SrofeuA0sA7zOYkQSOKOuLeNC9tiHjtm6NGF1fAf8gvOA";
