
import json
import os
from pathlib import Path
from typing import List

from app.notifications.rules.base_rule import IFinancialRule
from app.notifications.rules.dynamic_rule import DynamicThresholdRule


class RuleRepository:
    """
    Gerencia a persistência de regras dinâmicas do usuário.
    Salva em: data/users/{username}/rules.json
    """

    def __init__(self, user_data_dir: str):
        self.rules_file = os.path.join(user_data_dir, "rules.json")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.rules_file):
            self._save_rules_data([])

    def _load_rules_data(self) -> List[dict]:
        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_rules_data(self, data: List[dict]):
        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_rule(self, rule: DynamicThresholdRule):
        data = self._load_rules_data()
        # Remove existente se mesmo ID (upsert)
        data = [r for r in data if r["id"] != rule.id]
        data.append(rule.to_dict())
        self._save_rules_data(data)

    def remove_rule(self, rule_id: str):
        data = self._load_rules_data()
        data = [r for r in data if r["id"] != rule_id]
        self._save_rules_data(data)

    def get_all_rules(self) -> List[IFinancialRule]:
        data = self._load_rules_data()
        rules = []
        for item in data:
            if item.get("type") == "threshold":
                rules.append(DynamicThresholdRule.from_dict(item))
            # Outros tipos viriam aqui
        return rules
