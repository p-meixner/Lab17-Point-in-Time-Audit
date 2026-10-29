"""Lab 17: compare public FRED data with an ALFRED point-in-time vintage."""
from datetime import date
from io import BytesIO
import re
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import streamlit as st

SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "Federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}


def read_csv(url):
    with urlopen(url, timeout=30) as response:
        frame = pd.read_csv(BytesIO(response.read()), na_values=["."])
    if len(frame.columns) != 2 or frame.columns[0].lower() not in ("date", "observation_date"):
        raise ValueError("The server did not return a two-column observation CSV.")
    frame.columns = ["Date", "Value"]  # ALFRED adds a vintage suffix to its value header.
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    frame["Value"] = pd.to_numeric(frame["Value"], errors="raise")
    if frame["Date"].duplicated().any():
        raise ValueError("Duplicate observation dates in download.")
    return frame.set_index("Date").sort_index()


@st.cache_data(ttl=3600, show_spinner=False)
def download_today(series_id, download_day):
    """One current-data request; download_day also prevents cross-day cache reuse."""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?" + urlencode({"id": series_id})
    return read_csv(url)


@st.cache_data(ttl=3600, show_spinner=False)
def download_asof(series_id, vintage_date, download_day):
    """One vintage request, cached separately for each ID and decision date."""
    parameters = {"id": series_id, "vintage_date": vintage_date.isoformat()}
    url = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?" + urlencode(parameters)
    return read_csv(url)


def summarize(current, vintage):
    now = current["Value"].dropna()
    then = vintage["Value"].dropna()
    shared = pd.concat([then.rename("Then"), now.rename("Now")], axis=1).dropna()
    revised = int(((shared["Now"] - shared["Then"]).abs() > 1e-9).sum())
    last_then = then.index.max() if not then.empty else None
    return {
        "Last measured as known": last_then.strftime("%Y-%m-%d") if last_then is not None else None,
        "Value as known": float(then.iloc[-1]) if not then.empty else None,
        "Last measured today": now.index[-1].strftime("%Y-%m-%d") if not now.empty else None,
        "Value today": float(now.iloc[-1]) if not now.empty else None,
        "Later values": int((now.index > last_then).sum()) if last_then is not None else None,
        "Revised shared dates": revised,
    }


def main():
    st.set_page_config(page_title="Point-in-Time Rates Audit", layout="wide")
    today = date.today()
    st.title("Point-in-Time Rates Audit")
    st.caption(f"Data from FRED and ALFRED, Federal Reserve Bank of St. Louis, downloaded today ({today}); "
               "built with AI help, a learning demonstration, not investment advice.")
    selected = st.sidebar.multiselect("Series", list(SERIES), default=list(SERIES),
                                     format_func=lambda item: f"{item} — {SERIES[item]}")
    extra = st.sidebar.text_input("Add a FRED series ID", placeholder="PAYEMS").strip().upper()
    start = st.sidebar.date_input("Chart start date", date(2020, 1, 1),
                                  min_value=date(1776, 1, 1), max_value=today)
    vintage_date = st.sidebar.date_input("As known on", today,
                                        min_value=date(1776, 1, 1), max_value=today)
    if extra:
        if not re.fullmatch(r"[A-Z0-9_]+", extra):
            st.sidebar.error("Use a FRED series ID containing letters, numbers, or underscores.")
        elif extra not in selected:
            selected.append(extra)
    st.sidebar.caption("Downloads are cached for one hour. Each series uses one FRED request and one ALFRED request per uncached date combination.")
    st.caption("Charts show today's history. The table uses full downloaded histories; the chart start date does not change its counts. Dates are measurement dates, not publication dates.")
    rows = []
    for series_id in selected:
        st.subheader(f"{series_id} — {SERIES.get(series_id, 'Additional series')}")
        link = f"https://fred.stlouisfed.org/series/{series_id}"
        st.markdown(f"[Source and units on FRED]({link})")
        try:
            current = download_today(series_id, today)
            vintage = download_asof(series_id, vintage_date, today)
            summary = summarize(current, vintage)
            chart = current.loc[pd.Timestamp(start):]
            if chart["Value"].notna().any():
                st.line_chart(chart, y="Value")
            else:
                st.info("No current observations in this chart range.")
            st.caption(f"Last measured date known on {vintage_date}: "
                       f"{summary['Last measured as known'] or 'No nonmissing observations'}")
            rows.append({"Series": link, **summary, "Status": "OK"})
            if series_id == "PAYEMS":
                probe = pd.Timestamp("2024-12-01")
                old = vintage["Value"].get(probe, float("nan"))
                new = current["Value"].get(probe, float("nan"))
                st.write(f"December 2024 payrolls: {old:,.0f} as known on {vintage_date}; {new:,.0f} today (thousands of persons).")
        except Exception as error:
            st.error(f"{series_id}: {error}")
            rows.append({"Series": link, "Status": str(error)})
    st.subheader("Publication and revision audit")
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                     column_config={"Series": st.column_config.LinkColumn("Series", display_text=r"https://fred\.stlouisfed\.org/series/(.*)")})
    else:
        st.info("Select a series to begin.")
    st.caption("Later values counts nonmissing current observations after the last knowable measured date. Revised shared dates counts changed nonmissing values on matching dates. Missing days are never filled. If a vintage is empty, later values is undefined. These counts do not identify exact first-publication dates or all intervening revisions.")


if __name__ == "__main__":
    main()
