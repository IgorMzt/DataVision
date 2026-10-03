from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _role(mapping: dict, role: str):
    """
    Procura qual coluna do dataset foi associada a uma função
    semântica pelo Smart Column Mapper.
    """
    for column, info in (mapping or {}).items():
        if isinstance(info, dict) and info.get("role") == role:
            return column

    return None


def _money(value) -> str:
    """
    Formata valores monetários no padrão brasileiro.
    """
    if value is None or pd.isna(value):
        value = 0

    return (
        f"R$ {float(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def _json_number(value):
    """
    Converte valores NumPy/Pandas para números seguros para JSON.
    """
    if value is None or pd.isna(value):
        return 0

    value = float(value)

    if not math.isfinite(value):
        return 0

    return round(value, 2)


def _date_series(series: pd.Series) -> pd.Series:
    """
    Converte uma Series para datetime.

    format='mixed' evita o warning do Pandas ao trabalhar
    com datas em diferentes formatos.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(
            series,
            errors="coerce",
        )

    return pd.to_datetime(
        series,
        errors="coerce",
        dayfirst=True,
        format="mixed",
    )


def _status_approval(series: pd.Series):
    """
    Calcula uma taxa de aprovação quando os valores da coluna
    de status possuem estados reconhecidos como positivos.
    """
    normalized = (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    positive = {
        "aprovada",
        "aprovado",
        "approved",
        "ok",
        "sucesso",
        "success",
        "concluida",
        "concluído",
        "concluido",
    }

    known = normalized.ne("")

    if not known.any():
        return None

    approved = normalized.isin(positive).sum()

    return round(
        approved / known.sum() * 100,
        1,
    )


def _top_category_chart(
    df: pd.DataFrame,
    category,
    value=None,
    title=None,
):
    """
    Gera dados para gráfico de categorias.

    Se existir uma coluna de valor, agrega pela soma.
    Caso contrário, utiliza contagem de registros.
    """
    if not category or category not in df.columns:
        return None

    if value and value in df.columns:
        temp = df[[category, value]].copy()

        temp[value] = pd.to_numeric(
            temp[value],
            errors="coerce",
        )

        grouped = (
            temp
            .groupby(category, dropna=False)[value]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        return {
            "type": "bar",
            "title": title or f"Valor por {category}",
            "labels": [
                str(x)
                for x in grouped.index
            ],
            "values": [
                _json_number(x)
                for x in grouped.values
            ],
        }

    counts = (
        df[category]
        .fillna("Sem categoria")
        .astype(str)
        .value_counts()
        .head(10)
    )

    return {
        "type": "bar",
        "title": title or f"Registros por {category}",
        "labels": counts.index.tolist(),
        "values": [
            int(x)
            for x in counts.values
        ],
    }


def _common_context(
    df: pd.DataFrame,
    mapping: dict,
):
    """
    Recupera as principais funções semânticas utilizadas
    pelo Analytics Engine.
    """
    roles = (
        "cliente",
        "valor",
        "data_hora",
        "status",
        "produto",
        "quantidade",
        "departamento",
        "funcionario",
    )

    return {
        role: _role(mapping, role)
        for role in roles
    }


def build_analytics(
    df: pd.DataFrame,
    mapping: dict,
    segment: str,
    quality_score: float | None = None,
) -> dict:
    """
    Constrói KPIs, gráficos e insights determinísticos
    para o dashboard DataVision.

    Esta versão não utiliza IA generativa.
    """

    ctx = _common_context(
        df,
        mapping,
    )

    value = ctx["valor"]
    status = ctx["status"]
    date = ctx["data_hora"]

    # =========================================================
    # KPIs
    # =========================================================

    kpis = [
        {
            "label": "Registros",
            "value": f"{len(df):,}".replace(",", "."),
            "hint": "linhas analisadas",
        }
    ]

    charts = []
    insights = []

    # =========================================================
    # VALORES
    # =========================================================

    if value and value in df.columns:
        values = pd.to_numeric(
            df[value],
            errors="coerce",
        )

        kpis.extend(
            [
                {
                    "label": "Valor total",
                    "value": _money(
                        values.sum()
                    ),
                    "hint": value,
                },
                {
                    "label": "Valor médio",
                    "value": _money(
                        values.mean()
                    ),
                    "hint": "média por registro",
                },
            ]
        )

        if values.notna().any():
            insights.append(
                {
                    "kind": "Estatístico",
                    "title": "Centro da distribuição",
                    "text": (
                        f"A mediana de {value} é "
                        f"{_money(values.median())}. "
                        "A mediana reduz a influência "
                        "de valores extremos."
                    ),
                }
            )

    # =========================================================
    # KPIs ESPECÍFICOS POR SEGMENTO
    # =========================================================

    if (
        segment == "financeiro"
        and status
        and status in df.columns
    ):
        approval = _status_approval(
            df[status]
        )

        if approval is not None:
            kpis.append(
                {
                    "label": "Taxa de aprovação",
                    "value": (
                        f"{approval:.1f}%"
                        .replace(".", ",")
                    ),
                    "hint": (
                        "status positivos reconhecidos"
                    ),
                }
            )

    elif (
        segment == "comercio"
        and ctx["quantidade"]
        and ctx["quantidade"] in df.columns
    ):
        qty = pd.to_numeric(
            df[ctx["quantidade"]],
            errors="coerce",
        ).sum()

        kpis.append(
            {
                "label": "Quantidade",
                "value": (
                    f"{int(qty):,}"
                    .replace(",", ".")
                ),
                "hint": "itens registrados",
            }
        )

    elif (
        segment == "empresa"
        and ctx["funcionario"]
        and ctx["funcionario"] in df.columns
    ):
        kpis.append(
            {
                "label": "Funcionários",
                "value": str(
                    df[
                        ctx["funcionario"]
                    ].nunique(
                        dropna=True
                    )
                ),
                "hint": "identificadores únicos",
            }
        )

    elif quality_score is not None:
        kpis.append(
            {
                "label": "Data Quality",
                "value": (
                    f"{quality_score:.1f}%"
                    .replace(".", ",")
                ),
                "hint": "qualidade do dataset",
            }
        )

    # =========================================================
    # CLIENTES
    # =========================================================

    if (
        ctx["cliente"]
        and ctx["cliente"] in df.columns
        and len(kpis) < 5
    ):
        kpis.append(
            {
                "label": "Clientes únicos",
                "value": str(
                    df[
                        ctx["cliente"]
                    ].nunique(
                        dropna=True
                    )
                ),
                "hint": ctx["cliente"],
            }
        )

    # =========================================================
    # STATUS
    # =========================================================

    if status and status in df.columns:
        counts = (
            df[status]
            .fillna("Sem status")
            .astype(str)
            .value_counts()
            .head(8)
        )

        charts.append(
            {
                "type": "doughnut",
                "title": (
                    "Distribuição por status"
                ),
                "labels": (
                    counts.index.tolist()
                ),
                "values": [
                    int(x)
                    for x in counts.values
                ],
            }
        )

        if len(counts):
            share = (
                counts.iloc[0]
                / max(
                    counts.sum(),
                    1,
                )
                * 100
            )

            insights.append(
                {
                    "kind": "Comportamental",
                    "title": (
                        "Status predominante"
                    ),
                    "text": (
                        f"{counts.index[0]} "
                        f"concentra {share:.1f}% "
                        "dos registros com status "
                        "considerados no gráfico."
                    ),
                }
            )

    # =========================================================
    # CATEGORIAS
    # =========================================================

    if segment in {
        "financeiro",
        "comercio",
    }:
        category = ctx["produto"]

    elif segment == "empresa":
        category = ctx["departamento"]

    else:
        category = None

    chart = _top_category_chart(
        df,
        category,
        value,
    )

    if chart:
        charts.append(
            chart
        )

        if chart["values"]:
            insights.append(
                {
                    "kind": "Concentração",
                    "title": (
                        "Maior categoria observada"
                    ),
                    "text": (
                        f"{chart['labels'][0]} "
                        "aparece no topo de "
                        f"“{chart['title']}”, "
                        "com valor calculado de "
                        f"{chart['values'][0]}."
                    ),
                }
            )

    # =========================================================
    # ANÁLISE TEMPORAL
    # =========================================================

    if date and date in df.columns:
        dates = (
            _date_series(
                df[date]
            )
            .dropna()
        )

        if len(dates):
            daily = (
                pd.Series(
                    1,
                    index=dates,
                )
                .resample("D")
                .sum()
            )

            charts.append(
                {
                    "type": "line",
                    "title": (
                        "Volume de registros no tempo"
                    ),
                    "labels": [
                        x.strftime(
                            "%d/%m"
                        )
                        for x in daily.index
                    ],
                    "values": [
                        int(x)
                        for x in daily.values
                    ],
                }
            )

            peak = daily.idxmax()

            insights.append(
                {
                    "kind": "Temporal",
                    "title": (
                        "Pico de atividade"
                    ),
                    "text": (
                        "O maior volume diário "
                        f"ocorreu em "
                        f"{peak.strftime('%d/%m/%Y')}, "
                        f"com {int(daily.max())} "
                        "registros."
                    ),
                }
            )

    # =========================================================
    # GRÁFICO EXTRA AUTOMÁTICO
    # =========================================================

    if len(charts) < 4:
        excluded = {
            value,
            date,
            status,
            category,
        }

        candidates = [
            column
            for column in df.columns
            if (
                column not in excluded
                and df[column].nunique(
                    dropna=True
                ) <= 20
            )
        ]

        if candidates:
            extra = _top_category_chart(
                df,
                candidates[0],
                None,
                (
                    "Distribuição de "
                    f"{candidates[0]}"
                ),
            )

            if extra:
                charts.append(
                    extra
                )

    # =========================================================
    # CORRELAÇÃO
    # =========================================================

    numeric = df.select_dtypes(
        include=np.number
    )

    if len(numeric.columns) >= 2:
        corr = (
            numeric
            .corr()
            .abs()
        )

        # Pandas/NumPy recentes podem retornar
        # corr.values como somente leitura.
        #
        # Criamos uma cópia independente e gravável
        # antes de alterar a diagonal.
        arr = corr.to_numpy(
            copy=True
        )

        # Uma coluna sempre possui correlação 1.0
        # consigo mesma.
        #
        # Colocamos NaN na diagonal para que ela
        # não seja considerada na busca pela maior
        # correlação entre colunas diferentes.
        np.fill_diagonal(
            arr,
            np.nan,
        )

        if np.isfinite(arr).any():
            i, j = np.unravel_index(
                np.nanargmax(arr),
                arr.shape,
            )

            strongest = arr[i, j]

            if strongest >= 0.65:
                insights.append(
                    {
                        "kind": "Relação",
                        "title": (
                            "Associação estatística"
                        ),
                        "text": (
                            f"{corr.index[i]} e "
                            f"{corr.columns[j]} "
                            "têm correlação absoluta "
                            f"de {strongest:.2f}. "
                            "Isso indica associação "
                            "nos dados, não causalidade."
                        ),
                    }
                )

    # =========================================================
    # RESULTADO
    # =========================================================

    labels = {
        "financeiro": "Financeiro",
        "comercio": "Comércio",
        "empresa": "Empresarial",
        "geral": "Análise Geral",
    }

    return {
        "segment": segment,
        "segment_label": labels.get(
            segment,
            segment.title(),
        ),
        "kpis": kpis[:5],
        "charts": charts[:4],
        "insights": insights[:5],
    }