"""Data loading, preparation, and validation for FinSight."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

NSE_REQUIRED_COLUMNS = {
    "date",
    "symbol",
    "series",
    "open",
    "high",
    "low",
    "close",
    "volume",
}
PRICE_COLUMNS = ("open", "high", "low", "close")
INDIAN_STOCKS = {
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "ITC",
    "ONGC",
    "WIPRO",
    "TATAMOTORS",
}


def standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize column labels without changing their meaning."""
    result = frame.copy()
    result.columns = [str(column).strip().lower().replace(" ", "_") for column in result.columns]
    return result


def validate_ohlc(frame: pd.DataFrame, *, context: str = "data") -> None:
    """Raise with explicit counts rather than silently dropping invalid rows."""
    missing_columns = NSE_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"{context}: missing required columns: {sorted(missing_columns)}")

    missing_values = {
        column: int(count)
        for column, count in frame[list(NSE_REQUIRED_COLUMNS)].isna().sum().items()
        if count
    }
    if missing_values:
        raise ValueError(f"{context}: nulls in required fields: {missing_values}")

    nonpositive = {
        column: int((frame[column] <= 0).sum())
        for column in PRICE_COLUMNS
        if (frame[column] <= 0).any()
    }
    if nonpositive:
        raise ValueError(f"{context}: nonpositive OHLC values: {nonpositive}")

    invalid_ohlc = (
        (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
    )
    if invalid_ohlc.any():
        raise ValueError(f"{context}: {int(invalid_ohlc.sum())} invalid OHLC rows")

    negative_volume = int((frame["volume"] < 0).sum())
    if negative_volume:
        raise ValueError(f"{context}: {negative_volume} negative-volume rows")


def nse_files(raw_dir: Path | str) -> list[Path]:
    """Return annual NSE Parquet files in chronological filename order."""
    files = sorted(Path(raw_dir).glob("nse_*.parquet"))
    if not files:
        raise FileNotFoundError(f"No nse_YYYY.parquet files found in {raw_dir}")
    return files


def load_india_daily(
    raw_dir: Path | str,
    *,
    symbols: Iterable[str] | None = None,
    series: str = "EQ",
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load annual NSE data, retaining the requested series and optional symbols."""
    requested_columns = list(columns) if columns is not None else None
    if requested_columns is not None and not NSE_REQUIRED_COLUMNS.issubset(requested_columns):
        raise ValueError(
            "columns must include all validation fields: "
            f"{sorted(NSE_REQUIRED_COLUMNS)}"
        )
    frames: list[pd.DataFrame] = []
    wanted = set(symbols) if symbols is not None else None

    for path in nse_files(raw_dir):
        frame = standardize_columns(pd.read_parquet(path, columns=requested_columns))
        missing = NSE_REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            raise ValueError(f"{path.name}: missing required columns: {sorted(missing)}")
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        frame = frame.loc[frame["series"].eq(series)]
        if wanted is not None:
            frame = frame.loc[frame["symbol"].isin(wanted)]
        if not frame.empty:
            validate_ohlc(frame, context=path.name)
            frames.append(frame)

    if not frames:
        raise ValueError(f"No rows found for series={series!r} and requested symbols")

    result = pd.concat(frames, ignore_index=True)
    duplicate_count = int(result.duplicated(["date", "symbol", "series"]).sum())
    if duplicate_count:
        raise ValueError(f"Combined NSE data has {duplicate_count} duplicate natural keys")
    return result.sort_values(["symbol", "date"], ignore_index=True)


def build_processed_india(
    raw_dir: Path | str,
    output_path: Path | str,
    *,
    overwrite: bool = False,
) -> Path:
    """Write all validated EQ-series observations to one processed Parquet file."""
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"{output} already exists; pass overwrite=True to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)

    writer: pq.ParquetWriter | None = None
    total_rows = 0
    try:
        for path in nse_files(raw_dir):
            frame = standardize_columns(pd.read_parquet(path))
            missing = NSE_REQUIRED_COLUMNS.difference(frame.columns)
            if missing:
                raise ValueError(f"{path.name}: missing required columns: {sorted(missing)}")
            frame["date"] = pd.to_datetime(frame["date"], errors="raise")
            frame = frame.loc[frame["series"].eq("EQ")].copy()
            validate_ohlc(frame, context=path.name)
            if frame.duplicated(["date", "symbol", "series"]).any():
                raise ValueError(f"{path.name}: duplicate natural keys")

            table = pa.Table.from_pandas(frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(output, table.schema, compression="zstd")
            else:
                table = table.cast(writer.schema)
            writer.write_table(table)
            total_rows += len(frame)
    except Exception:
        if writer is not None:
            writer.close()
        if output.exists():
            output.unlink()
        raise
    else:
        if writer is not None:
            writer.close()

    if total_rows == 0:
        raise ValueError("No EQ-series rows were found")
    return output


def load_processed_india(
    processed_path: Path | str,
    *,
    symbols: Iterable[str] | None = None,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Read only requested instruments/columns from the combined Parquet file."""
    import pyarrow.dataset as ds

    dataset = ds.dataset(Path(processed_path), format="parquet")
    selected_columns = list(columns) if columns is not None else None
    if selected_columns is not None and not {"date", "symbol"}.issubset(selected_columns):
        raise ValueError("columns must include date and symbol for sorting")
    expression = None
    if symbols is not None:
        symbols = list(symbols)
        if not symbols:
            raise ValueError("symbols must contain at least one instrument")
        expression = ds.field("symbol").isin(symbols)
    table = dataset.to_table(columns=selected_columns, filter=expression)
    if table.num_rows == 0:
        raise ValueError(f"No rows matched the requested symbols in {processed_path}")
    return table.to_pandas().sort_values(["symbol", "date"], ignore_index=True)
