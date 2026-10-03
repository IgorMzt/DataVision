from __future__ import annotations

import math
import numpy as np
import pandas as pd


def _role(mapping: dict, role: str):
    for column, info in (mapping or {}).items():
        if isinstance(info, dict) and info.get("role") == role:
            return column
    return None


def _money(value) -> str:
    if value is None or pd.isna(value):
        value = 0
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _json_number(value):
    if value is None or pd.isna(value) or not math.isfinite(float(value)):
        return 0
    return round(float(value), 2)


def _date_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    return pd.to_datetime(series, errors="coerce", dayfirst=True, format="mixed")


def _status_approval(series: pd.Series):
    normalized = series.fillna("").astype(str).str.strip().str.lower()
    positive = {"aprovada", "aprovado", "approved", "ok", "sucesso", "success", "concluida", "concluído", "concluido"}
    known = normalized.ne("")
    if not known.any():
        return None
    approved = normalized.isin(positive).sum()
    return round(approved / known.sum() * 100, 1)


def _top_category_chart(df, category, value=None, title=None):
    if not category or category not in df.columns:
        return None
    if value and value in df.columns:
        temp = df[[category, value]].copy()
        temp[value] = pd.to_numeric(temp[value], errors="coerce")
        grouped = temp.groupby(category, dropna=False)[value].sum().sort_values(ascending=False).head(10)
        return {"type": "bar", "title": title or f"Valor por {category}", "labels": [str(x) for x in grouped.index], "values": [_json_number(x) for x in grouped.values]}
    counts = df[category].fillna("Sem categoria").astype(str).value_counts().head(10)
    return {"type": "bar", "title": title or f"Registros por {category}", "labels": counts.index.tolist(), "values": [int(x) for x in counts.values]}


def _common_context(df, mapping):
    return {role: _role(mapping, role) for role in ("cliente", "valor", "data_hora", "status", "produto", "quantidade", "departamento", "funcionario")}


def build_analytics(df: pd.DataFrame, mapping: dict, segment: str, quality_score: float | None = None) -> dict:
    ctx = _common_context(df, mapping)
    value, status, date = ctx["valor"], ctx["status"], ctx["data_hora"]
    kpis = [{"label": "Registros", "value": f"{len(df):,}".replace(",", "."), "hint": "linhas analisadas"}]
    charts, insights = [], []

    if value and value in df.columns:
        values = pd.to_numeric(df[value], errors="coerce")
        kpis.extend([
            {"label": "Valor total", "value": _money(values.sum()), "hint": value},
            {"label": "Valor médio", "value": _money(values.mean()), "hint": "média por registro"},
        ])
        if values.notna().any():
            insights.append({"kind": "Estatístico", "title": "Centro da distribuição", "text": f"A mediana de {value} é {_money(values.median())}. A mediana reduz a influência de valores extremos."})

    if segment == "financeiro" and status and status in df.columns:
        approval = _status_approval(df[status])
        if approval is not None:
            kpis.append({"label": "Taxa de aprovação", "value": f"{approval:.1f}%".replace(".", ","), "hint": "status positivos reconhecidos"})
    elif segment == "comercio" and ctx["quantidade"] and ctx["quantidade"] in df.columns:
        qty = pd.to_numeric(df[ctx["quantidade"]], errors="coerce").sum()
        kpis.append({"label": "Quantidade", "value": f"{int(qty):,}".replace(",", "."), "hint": "itens registrados"})
    elif segment == "empresa" and ctx["funcionario"] and ctx["funcionario"] in df.columns:
        kpis.append({"label": "Funcionários", "value": str(df[ctx["funcionario"]].nunique(dropna=True)), "hint": "identificadores únicos"})
    elif quality_score is not None:
        kpis.append({"label": "Data Quality", "value": f"{quality_score:.1f}%".replace(".", ","), "hint": "qualidade do dataset"})

    if ctx["cliente"] and ctx["cliente"] in df.columns and len(kpis) < 5:
        kpis.append({"label": "Clientes únicos", "value": str(df[ctx["cliente"]].nunique(dropna=True)), "hint": ctx["cliente"]})

    if status and status in df.columns:
        counts = df[status].fillna("Sem status").astype(str).value_counts().head(8)
        charts.append({"type": "doughnut", "title": "Distribuição por status", "labels": counts.index.tolist(), "values": [int(x) for x in counts.values]})
        if len(counts):
            share = counts.iloc[0] / max(counts.sum(), 1) * 100
            insights.append({"kind": "Comportamental", "title": "Status predominante", "text": f"{counts.index[0]} concentra {share:.1f}% dos registros com status considerados no gráfico."})

    category = ctx["produto"] if segment in {"financeiro", "comercio"} else ctx["departamento"] if segment == "empresa" else None
    chart = _top_category_chart(df, category, value)
    if chart:
        charts.append(chart)
        if chart["values"]:
            insights.append({"kind": "Concentração", "title": "Maior categoria observada", "text": f"{chart['labels'][0]} aparece no topo de “{chart['title']}”, com valor calculado de {chart['values'][0]}."})

    if date and date in df.columns:
        dates = _date_series(df[date]).dropna()
        if len(dates):
            daily = pd.Series(1, index=dates).resample("D").sum()
            charts.append({"type": "line", "title": "Volume de registros no tempo", "labels": [x.strftime("%d/%m") for x in daily.index], "values": [int(x) for x in daily.values]})
            peak = daily.idxmax()
            insights.append({"kind": "Temporal", "title": "Pico de atividade", "text": f"O maior volume diário ocorreu em {peak.strftime('%d/%m/%Y')}, com {int(daily.max())} registros."})

    if len(charts) < 4:
        candidates = [c for c in df.columns if c not in {value, date, status, category} and df[c].nunique(dropna=True) <= 20]
        if candidates:
            extra = _top_category_chart(df, candidates[0], None, f"Distribuição de {candidates[0]}")
            if extra:
                charts.append(extra)

    numeric = df.select_dtypes(include=np.number)
    if len(numeric.columns) >= 2:
        corr = numeric.corr().abs()
        arr = corr.to_numpy(copy=True)
        np.fill_diagonal(arr, np.nan)
        if np.isfinite(arr).any():
            i, j = np.unravel_index(np.nanargmax(arr), arr.shape)
            strongest = arr[i, j]
            if strongest >= .65:
                insights.append({"kind": "Relação", "title": "Associação estatística", "text": f"{corr.index[i]} e {corr.columns[j]} têm correlação absoluta de {strongest:.2f}. Isso indica associação nos dados, não causalidade."})

    labels = {"financeiro": "Financeiro", "comercio": "Comércio", "empresa": "Empresarial", "geral": "Análise Geral"}
    return {"segment": segment, "segment_label": labels.get(segment, segment.title()), "kpis": kpis[:5], "charts": charts[:4], "insights": insights[:5]}
