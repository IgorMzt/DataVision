from __future__ import annotations
import pandas as pd


def compare_runs(current_df, previous_df, current_run, previous_run):
    def pct(now, before):
        if before in (None, 0):
            return None
        return round((now - before) / before * 100, 1)

    metrics = [
        {"label": "Registros", "current": len(current_df), "previous": len(previous_df), "change": pct(len(current_df), len(previous_df))},
        {"label": "Colunas", "current": len(current_df.columns), "previous": len(previous_df.columns), "change": pct(len(current_df.columns), len(previous_df.columns))},
        {"label": "Data Quality", "current": round(float(current_run.quality_score or 0), 1), "previous": round(float(previous_run.quality_score or 0), 1), "change": round(float(current_run.quality_score or 0) - float(previous_run.quality_score or 0), 1)},
    ]
    common_numeric = [c for c in current_df.columns if c in previous_df.columns and pd.api.types.is_numeric_dtype(current_df[c])]
    if common_numeric:
        col = common_numeric[0]
        now = pd.to_numeric(current_df[col], errors="coerce").sum()
        before = pd.to_numeric(previous_df[col], errors="coerce").sum()
        metrics.append({"label": f"Soma de {col}", "current": round(float(now), 2), "previous": round(float(before), 2), "change": pct(now, before)})
    return {"metrics": metrics, "previous_run_id": previous_run.id, "current_run_id": current_run.id}
