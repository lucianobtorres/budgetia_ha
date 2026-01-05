import { fetchAPI } from './api';

export interface UserSubscription {
    plan_tier: 'free' | 'pro' | 'enterprise' | 'lifetime';
    status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'expired';
    trial_end: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
}

export const SubscriptionService = {
    async getStatus(): Promise<UserSubscription> {
        try {
            return await fetchAPI('/subscription/status');
        } catch (error) {
            // Fallback for dev/demo if API missing
            console.warn("Mocking subscription status due to API error");
            return {
                plan_tier: 'free',
                status: 'active',
                trial_end: null,
                current_period_end: null,
                cancel_at_period_end: false
            };
        }
    },

    async getCheckoutUrl(planId: string): Promise<string> {
        const res = await fetchAPI('/subscription/checkout', {
            method: 'POST',
            body: JSON.stringify({ plan_id: planId })
        });
        return res.url;
    },

    async getPortalUrl(): Promise<string> {
        const res = await fetchAPI('/subscription/portal', {
            method: 'POST'
        });
        return res.url;
    }
};
