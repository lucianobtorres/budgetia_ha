import { fetchAPI } from './api';

export interface TelemetryAction {
    action_type: string;
    metadata?: Record<string, any>;
}

export interface RuleFeedback {
    rule_name: string;
    feedback_type: 'ignored' | 'dismissed' | 'clicked' | 'positive';
}

class TelemetryService {
    private static instance: TelemetryService;
    
    // Lista de ações para evitar spam de chamadas (debounce simples poderia ser adicionado aqui)
    // Por enquanto, faremos chamadas diretas ("fire and forget")

    private constructor() {}

    public static getInstance(): TelemetryService {
        if (!TelemetryService.instance) {
            TelemetryService.instance = new TelemetryService();
        }
        return TelemetryService.instance;
    }

    /**
     * Registra uma ação do usuário.
     * Use para tracking de navegação, cliques importantes, uso de features.
     */
    public async logAction(action_type: string, metadata?: Record<string, any>) {
        try {
            // "Fire and forget" - não aguardamos a Promise para não bloquear a UI
            fetchAPI('/telemetry/action', {
                method: 'POST',
                body: JSON.stringify({ action_type, metadata }),
            }).catch(err => console.error("Telemetry Error (Background):", err));
        } catch (error) {
            console.error("Telemetry Error:", error);
        }
    }

    /**
     * Registra feedback sobre uma notificação/regra.
     * Essencial para o aprendizado do sistema.
     */
    public async logFeedback(rule_name: string, feedback_type: RuleFeedback['feedback_type']) {
        try {
            fetchAPI('/telemetry/feedback', {
                method: 'POST',
                body: JSON.stringify({ rule_name, feedback_type }),
            }).catch(err => console.error("Telemetry Feedback Error:", err));
        } catch (error) {
            console.error("Telemetry Feedback Error:", error);
        }
    }
}

export const telemetry = TelemetryService.getInstance();
