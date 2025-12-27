import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

class UserBehaviorService:
    """
    Gerencia a persistência do comportamento do usuário (Telemetria & Hábitos).
    ARQUIVO: data/users/{username}/behavior.json
    
    Diferente do UserConfigService, este arquivo armazena dados
    que podem ser reconstruídos ou descartados sem perda crítica de acesso,
    mas que são essenciais para a inteligência adaptativa (Jarvis).
    """

    def __init__(self, username: str):
        if not username:
            raise ValueError("Username não pode ser nulo.")
        self.username = username
        self.user_dir = Path(config.DATA_DIR) / "users" / self.username
        self.behavior_file = self.user_dir / "behavior.json"
        self._ensure_dir_exists()

    def _ensure_dir_exists(self) -> None:
        self.user_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict[str, Any]:
        if not self.behavior_file.exists():
            return {}
        try:
            with open(self.behavior_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"AVISO: behavior.json corrompido para {self.username}. Reiniciando.")
            return {}

    def _save_data(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.behavior_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except OSError as e:
            print(f"ERRO ao salvar behavior.json: {e}")

    # --- Telemetria de Ações ---

    def log_action(self, action_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra uma ação realizada pelo usuário (ex: 'view_dashboard', 'add_transaction').
        """
        data = self._load_data()
        
        # 1. Atualizar contadores
        if "action_counts" not in data:
            data["action_counts"] = {}
        
        current_count = data["action_counts"].get(action_type, 0)
        data["action_counts"][action_type] = current_count + 1

        # 2. Atualizar última interação global
        data["last_interaction"] = datetime.now().isoformat()

        # 3. Registrar horário (para perfil de uso)
        # Ex: "hourly_activity": { "09": 5, "20": 42 }
        if "hourly_activity" not in data:
            data["hourly_activity"] = {}
        
        current_hour = str(datetime.now().hour)
        data["hourly_activity"][current_hour] = data["hourly_activity"].get(current_hour, 0) + 1

        self._save_data(data)

    # --- Feedback de Regras (O "Cérebro" de Silenciamento) ---

    def log_rule_feedback(self, rule_name: str, feedback_type: str) -> None:
        """
        Registra como o usuário reagiu a uma regra.
        feedback_type: 'ignored' | 'dismissed' | 'clicked' | 'positive'
        """
        data = self._load_data()
        
        if "rule_feedback" not in data:
            data["rule_feedback"] = {}
        
        if rule_name not in data["rule_feedback"]:
            data["rule_feedback"][rule_name] = {
                "ignored_count": 0,
                "dismissed_count": 0,
                "clicked_count": 0,
                "consecutive_ignores": 0
            }

        stats = data["rule_feedback"][rule_name]
        
        if feedback_type == 'ignored':
            stats["ignored_count"] += 1
            stats["consecutive_ignores"] += 1
        elif feedback_type == 'dismissed':
            stats["dismissed_count"] += 1
            # Dimissed é uma ação ativa, zera ignores consecutivos?
            # Depende: se ele dispensa sem ler, é ruim. Se ele dispensa pq já sabe, é ok.
            # Vamos manter conservative: não zera, mas conta separado.
        elif feedback_type in ['clicked', 'positive']:
            stats["clicked_count"] += 1
            stats["consecutive_ignores"] = 0 # Sucesso! Resetamos o contador de "chato"
        
        stats["last_trigger"] = datetime.now().isoformat()
        
        data["rule_feedback"][rule_name] = stats
        self._save_data(data)

    def should_silence_rule(self, rule_name: str, threshold: int = 3) -> bool:
        """
        Consulta se uma regra deve ser silenciada com base no histórico.
        """
        data = self._load_data()
        feedback = data.get("rule_feedback", {}).get(rule_name, {})
        
        consecutive_ignores = feedback.get("consecutive_ignores", 0)
        
        if consecutive_ignores >= threshold:
            print(f"SMART RULE: Silenciando '{rule_name}' (Ignorada {consecutive_ignores}x seguidas).")
            return True
            
        return False
