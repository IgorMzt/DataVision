import pandas as pd
from app.services.anomaly_engine import analyze_anomalies


def test_anomaly_engine_flags_velocity_and_value():
    df = pd.DataFrame({
        "cliente": ["A"] * 7 + ["B"],
        "valor": [10, 12, 11, 13, 12, 9000, 14, 15],
        "data": [f"01/10/2026 02:0{i}" for i in range(7)] + ["01/10/2026 14:00"],
        "status": ["Negada"] * 6 + ["Aprovada", "Aprovada"],
    })
    mapping = {"cliente":{"role":"cliente"},"valor":{"role":"valor"},"data":{"role":"data_hora"},"status":{"role":"status"}}
    result = analyze_anomalies(df, mapping, "financeiro")
    assert result["available"] is True
    assert result["summary"]["max_score"] > 0
    assert "velocity" in result["components"]
    assert result["rows"]


def test_anomaly_score_is_not_fraud_probability():
    df = pd.DataFrame({"valor": [1, 2, 3, 1000]})
    result = analyze_anomalies(df, {"valor":{"role":"valor"}}, "financeiro")
    assert "não representa probabilidade de fraude" in result["disclaimer"]
