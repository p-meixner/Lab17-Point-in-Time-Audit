"""Run live benchmark and app checks; save reproducible evidence."""
from datetime import date
from pathlib import Path
import json

import pandas as pd
from streamlit.testing.v1 import AppTest
from asof_app import download_today, download_asof, summarize


def main():
    today = date.today()
    evidence = {"download_date": str(today), "known_answer": {}, "DGS10": {}}
    expected = {"BAA": ("2026-09-01", 6.47), "FEDFUNDS": ("2026-09-01", 3.75),
                "DGS10": ("2026-10-02", 5.28), "MORTGAGE30US": ("2026-10-01", 7.28)}
    for series_id, (last_date, value) in expected.items():
        current = download_today(series_id, today)
        vintage = download_asof(series_id, date(2026, 10, 5), today)
        result = summarize(current, vintage)
        evidence["known_answer"][series_id] = result
        assert result["Last measured as known"] == last_date, result
        assert abs(result["Value as known"] - value) < 1e-9, result
    current = download_today("PAYEMS", today)
    vintage = download_asof("PAYEMS", date(2025, 1, 15), today)
    probe = pd.Timestamp("2024-12-01")
    result = summarize(current, vintage)
    result["December 2024 then"] = float(vintage.loc[probe, "Value"])
    result["December 2024 today"] = float(current.loc[probe, "Value"])
    assert result["Last measured as known"] == "2024-12-01"
    assert result["December 2024 then"] == 159536
    assert result["December 2024 today"] < 159536
    assert result["Revised shared dates"] > 0
    evidence["PAYEMS_probe"] = result
    current = download_today("DGS10", today)
    for cutoff in (date(2026, 9, 30), today):
        evidence["DGS10"][str(cutoff)] = summarize(current, download_asof("DGS10", cutoff, today))
    evidence["DGS10"]["latest_three"] = {str(day.date()): float(value) for day, value in current["Value"].dropna().tail(3).items()}
    # Exercise real Streamlit widgets and error isolation.
    app = AppTest.from_file("asof_app.py", default_timeout=120).run()
    assert not app.exception and not app.error
    assert len(app.dataframe[0].value) == 4
    app.sidebar.date_input[1].set_value(date(2026, 10, 5)).run()
    assert not app.exception and not app.error
    app.sidebar.text_input[0].set_value("PAYEMS")
    app.sidebar.date_input[1].set_value(date(2025, 1, 15)).run()
    assert not app.exception and not app.error
    assert len(app.dataframe[0].value) == 5
    app.sidebar.text_input[0].set_value("NOT_A_REAL_SERIES_LAB17").run()
    assert not app.exception and len(app.error) == 1
    assert sum(app.dataframe[0].value["Status"] == "OK") == 4
    evidence["app_checks"] = "PASS: default four series, historical date, PAYEMS addition, unknown-ID isolation"
    Path("Lab17-validation.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
