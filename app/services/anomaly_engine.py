from __future__ import annotations

import math
import numpy as np
import pandas as pd


def _role(mapping: dict, role: str):
    for column, info in (mapping or {}).items():
        if isinstance(info, dict) and info.get("role") == role and column:
            return column
    return None


def _safe_float(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _normalize(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").fillna(0).clip(lower=0)
    maximum = series.max()
    return series / maximum if maximum and math.isfinite(float(maximum)) else pd.Series(0.0, index=series.index)


def _robust_deviation(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    median = values.median()
    mad = (values - median).abs().median()
    if pd.isna(median):
        return pd.Series(0.0, index=series.index)
    if pd.isna(mad) or mad == 0:
        std = values.std()
        if pd.isna(std) or std == 0:
            return pd.Series(0.0, index=series.index)
        z = (values - values.mean()).abs() / std
    else:
        z = 0.6745 * (values - median).abs() / mad
    return (z / 6.0).clip(0, 1).fillna(0)


def analyze_anomalies(df: pd.DataFrame, mapping: dict, segment: str) -> dict:
    """Deterministic anomaly scoring. Score means deviation, never fraud probability."""
    if df.empty:
        return {"available": False, "summary": {}, "rows": [], "components": []}

    value_col = _role(mapping, "valor")
    date_col = _role(mapping, "data_hora")
    status_col = _role(mapping, "status")
    customer_col = _role(mapping, "cliente")

    work = df.copy().reset_index(drop=False).rename(columns={"index": "_source_index"})
    score_parts = {}
    explanations = [[] for _ in range(len(work))]

    if value_col and value_col in work.columns:
        value_dev = _robust_deviation(work[value_col])
        score_parts["value_deviation"] = value_dev
        for idx, val in value_dev.items():
            if val >= .55:
                explanations[idx].append("valor distante do padrão central")

    parsed_dates = None
    if date_col and date_col in work.columns:
        parsed_dates = pd.to_datetime(work[date_col], errors="coerce", dayfirst=True, format="mixed")
        hours = parsed_dates.dt.hour
        time_behavior = pd.Series(0.0, index=work.index)
        time_behavior.loc[hours.isin([0, 1, 2, 3, 4, 5])] = .75
        score_parts["time_behavior"] = time_behavior
        for idx, val in time_behavior.items():
            if val >= .55:
                explanations[idx].append("horário pouco usual")

    velocity = pd.Series(0.0, index=work.index)
    if customer_col and customer_col in work.columns and parsed_dates is not None:
        temp = pd.DataFrame({"customer": work[customer_col], "date": parsed_dates}, index=work.index).dropna()
        for _, group in temp.groupby("customer"):
            ordered = group.sort_values("date")
            dates = ordered["date"]
            for pos, (idx, moment) in enumerate(dates.items()):
                count = int(((dates <= moment) & (dates >= moment - pd.Timedelta(minutes=10))).sum())
                velocity.loc[idx] = min(max(count - 1, 0) / 5.0, 1.0)
        score_parts["velocity"] = velocity
        for idx, val in velocity.items():
            if val >= .55:
                explanations[idx].append("múltiplas operações em até 10 minutos")

    denial = pd.Series(0.0, index=work.index)
    if status_col and status_col in work.columns:
        normalized = work[status_col].fillna("").astype(str).str.strip().str.lower()
        negative = normalized.str.contains(r"negad|recus|denied|declin|falh", regex=True)
        denial.loc[negative] = .65
        score_parts["denial"] = denial
        for idx, val in denial.items():
            if val >= .55:
                explanations[idx].append("status de negação/recusa")

    if not score_parts:
        return {"available": False, "summary": {}, "rows": [], "components": []}

    weights = {"velocity": .35, "value_deviation": .30, "denial": .20, "time_behavior": .15}
    active_weight = sum(weights[name] for name in score_parts)
    total = pd.Series(0.0, index=work.index)
    for name, series in score_parts.items():
        total += series * (weights[name] / active_weight)
    scores = (total * 100).clip(0, 100).round(1)

    ranked = scores.sort_values(ascending=False).head(15)
    rows = []
    for idx, score in ranked.items():
        if score < 20:
            continue
        row = work.loc[idx]
        item = {
            "row": int(row["_source_index"]) + 2,
            "score": _safe_float(score),
            "level": "alto" if score >= 70 else "moderado" if score >= 45 else "baixo",
            "reasons": explanations[idx] or ["combinação de desvios observados"],
            "customer": str(row[customer_col]) if customer_col and pd.notna(row.get(customer_col)) else "—",
            "value": _safe_float(row[value_col]) if value_col else None,
            "date": str(row[date_col]) if date_col and pd.notna(row.get(date_col)) else "—",
            "status": str(row[status_col]) if status_col and pd.notna(row.get(status_col)) else "—",
        }
        rows.append(item)

    high = int((scores >= 70).sum())
    moderate = int(((scores >= 45) & (scores < 70)).sum())
    return {
        "available": True,
        "summary": {"high": high, "moderate": moderate, "max_score": _safe_float(scores.max()), "analyzed": len(work)},
        "rows": rows,
        "components": [name for name in ("velocity", "value_deviation", "denial", "time_behavior") if name in score_parts],
        "disclaimer": "Anomaly Score mede desvio do padrão observado; não representa probabilidade de fraude.",
    }
