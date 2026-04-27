import math
from typing import Any

import pandas as pd


def sanitize_data(data: Any) -> Any:
    """
    Sanitiza dados (dict, list, DataFrame, Series) removendo valores NaN e Inf,
    convertendo-os para None, o que é compatível com JSON/Pydantic.
    """
    if isinstance(data, pd.DataFrame):
        return [sanitize_data(r) for r in data.to_dict(orient="records")]

    if isinstance(data, pd.Series):
        return sanitize_data(data.to_dict())

    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}

    if isinstance(data, list):
        return [sanitize_data(i) for i in data]

    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None

    return data
