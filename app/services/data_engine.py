from __future__ import annotations
import math
import re
from pathlib import Path
import numpy as np
import pandas as pd

ALIASES = {
    "id": ["id", "codigo", "code", "identificador"],
    "cliente": ["cliente", "customer", "client", "usuario", "user", "cpf", "customer_id", "cliente_id"],
    "valor": ["valor", "amount", "price", "preco", "total", "vlr", "reais", "salario", "salary", "receita", "revenue"],
    "data_hora": ["data", "date", "datetime", "timestamp", "hora", "time", "dt", "created_at"],
    "status": ["status", "situacao", "resultado", "state", "aprovado", "approved"],
    "produto": ["produto", "product", "item", "sku"],
    "quantidade": ["quantidade", "quantity", "qtd", "qty"],
    "departamento": ["departamento", "department", "setor", "area"],
    "funcionario": ["funcionario", "employee", "colaborador", "employee_id"],
}

def load_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            return pd.read_csv(path, sep=None, engine="python")
        except UnicodeDecodeError:
            return pd.read_csv(path, sep=None, engine="python", encoding="latin-1")
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path, engine="openpyxl")
    raise ValueError("Formato não suportado. Use CSV ou XLSX.")

def _safe(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return float(v)
    if isinstance(v, (pd.Timestamp,)): return v.isoformat()
    return v

def semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series): return "booleano"
    if pd.api.types.is_datetime64_any_dtype(series): return "data/hora"
    if pd.api.types.is_numeric_dtype(series): return "numérico"
    sample = series.dropna().astype(str).head(100)
    if len(sample):
        parsed = pd.to_datetime(sample, errors="coerce", dayfirst=True, format="mixed")
        if parsed.notna().mean() >= .85: return "data/hora"
    unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
    if unique_ratio > .9: return "identificador/texto"
    return "categórico"

def profile_dataframe(df: pd.DataFrame) -> dict:
    rows, cols = df.shape
    missing = int(df.isna().sum().sum())
    cells = max(rows * cols, 1)
    duplicates = int(df.duplicated().sum())
    column_profiles = []
    invalid_types = 0
    outliers_total = 0
    for name in df.columns:
        s = df[name]
        stype = semantic_type(s)
        item = {
            "name": str(name), "dtype": str(s.dtype), "semantic_type": stype,
            "missing": int(s.isna().sum()), "missing_pct": round(float(s.isna().mean()*100), 2),
            "unique": int(s.nunique(dropna=True)), "sample": [_safe(x) for x in s.dropna().head(3).tolist()]
        }
        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna().astype(float)
            if len(clean):
                q1, q3 = clean.quantile([.25, .75]); iqr = q3-q1
                outliers = int(((clean < q1-1.5*iqr) | (clean > q3+1.5*iqr)).sum()) if iqr > 0 else 0
                outliers_total += outliers
                item["stats"] = {"mean": _safe(clean.mean()), "median": _safe(clean.median()), "min": _safe(clean.min()), "max": _safe(clean.max()), "outliers": outliers}
        column_profiles.append(item)
    completeness = max(0, 100 - missing/cells*100)
    uniqueness = max(0, 100 - duplicates/max(rows,1)*100)
    validity = max(0, 100 - invalid_types/max(cols,1)*100)
    consistency = max(0, 100 - min(outliers_total/max(rows,1)*15, 25))
    quality = round(.40*completeness + .25*uniqueness + .20*validity + .15*consistency, 1)
    return {
        "rows": rows, "columns": cols, "missing": missing, "duplicates": duplicates, "outliers": outliers_total,
        "quality": quality,
        "quality_parts": {"completude": round(completeness,1), "duplicidade": round(uniqueness,1), "validade": round(validity,1), "consistencia": round(consistency,1)},
        "column_profiles": column_profiles,
    }

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")

def smart_mapping(df: pd.DataFrame, segment: str, previous: dict | None = None) -> dict:
    previous = previous or {}
    result = {}
    for col in df.columns:
        name = _norm(col); stype = semantic_type(df[col]); best_role = "outro"; best = 0
        if str(col) in previous:
            result[str(col)] = {"role": previous[str(col)], "confidence": "alta", "reason": "mapeamento anterior"}; continue
        for role, aliases in ALIASES.items():
            score = 0
            for alias in aliases:
                a = _norm(alias)
                if name == a: score = max(score, 5)
                elif a in name or name in a: score = max(score, 3)
            if role == "valor" and stype == "numérico": score += 1
            if role == "data_hora" and stype == "data/hora": score += 2
            if role in {"cliente","produto","departamento","funcionario","status"} and stype in {"categórico","identificador/texto"}: score += .5
            if score > best: best, best_role = score, role
        confidence = "alta" if best >= 5 else "média" if best >= 3 else "baixa"
        result[str(col)] = {"role": best_role, "confidence": confidence, "reason": f"nome + tipo {stype}" if best else f"tipo {stype}"}
    return result

def cleaning_recommendations(df: pd.DataFrame) -> list[dict]:
    recs = []
    dup = int(df.duplicated().sum())
    if dup: recs.append({"key":"drop_duplicates","kind":"duplicados","title":f"{dup} linhas duplicadas", "description":"Remover apenas duplicidades exatas.", "count":dup})
    for col in df.columns:
        miss = int(df[col].isna().sum())
        if not miss: continue
        if pd.api.types.is_numeric_dtype(df[col]):
            recs.append({"key":f"median::{col}","kind":"ausentes","title":f"{miss} ausentes em {col}","description":"Preencher com a mediana (recomendado para reduzir impacto de extremos).","count":miss})
        else:
            recs.append({"key":f"mode::{col}","kind":"ausentes","title":f"{miss} ausentes em {col}","description":"Preencher com o valor mais frequente da coluna.","count":miss})
    return recs

def apply_cleaning(df: pd.DataFrame, actions: list[str]) -> tuple[pd.DataFrame, list[dict]]:
    out = df.copy(); history=[]
    for action in actions:
        if action == "drop_duplicates":
            before=len(out); out=out.drop_duplicates(); history.append({"action":"drop_duplicates","affected":before-len(out),"label":"Duplicidades exatas removidas"})
        elif "::" in action:
            op,col=action.split("::",1)
            if col not in out.columns: continue
            before=int(out[col].isna().sum())
            if op == "median" and pd.api.types.is_numeric_dtype(out[col]): out[col]=out[col].fillna(out[col].median())
            elif op == "mean" and pd.api.types.is_numeric_dtype(out[col]): out[col]=out[col].fillna(out[col].mean())
            elif op == "mode":
                mode=out[col].mode(dropna=True)
                if len(mode): out[col]=out[col].fillna(mode.iloc[0])
            elif op == "drop_missing": out=out.dropna(subset=[col])
            history.append({"action":action,"affected":before,"label":f"Tratamento aplicado em {col}"})
    return out, history
