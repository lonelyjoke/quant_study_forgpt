"""Update local index daily data cache."""

from __future__ import annotations

from common import load_config, resolve_project_path
from data.data_loader import TushareIndexDataLoader


def main() -> None:
    """Fetch configured indices and refresh local cache if requested."""

    config = load_config()
    data_cfg = config["data"]
    loader = TushareIndexDataLoader(cache_dir=resolve_project_path(data_cfg["cache_dir"]))

    for ts_code, name in config["indices"].items():
        df = loader.get_index_daily(
            ts_code,
            start_date=data_cfg["start_date"],
            end_date=data_cfg.get("end_date"),
            refresh=bool(data_cfg.get("refresh", False)),
        )
        print(f"{ts_code} {name}: {len(df)} rows, {df['trade_date'].min().date()} -> {df['trade_date'].max().date()}")


if __name__ == "__main__":
    main()
