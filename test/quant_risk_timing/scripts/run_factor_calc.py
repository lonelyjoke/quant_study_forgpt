"""Calculate factor tables for configured indices."""

from __future__ import annotations

from common import load_config, resolve_project_path
from data.data_loader import TushareIndexDataLoader
from factors.factor_pipeline import calculate_factor_table, save_factor_table


def main() -> None:
    """Load market data, calculate factors, and save CSV outputs."""

    config = load_config()
    data_cfg = config["data"]
    cache_dir = resolve_project_path(data_cfg["cache_dir"])
    loader = TushareIndexDataLoader(cache_dir=cache_dir)

    for ts_code, name in config["indices"].items():
        price_df = loader.get_index_daily(
            ts_code,
            start_date=data_cfg["start_date"],
            end_date=data_cfg.get("end_date"),
            refresh=bool(data_cfg.get("refresh", False)),
        )
        factor_df = calculate_factor_table(price_df)
        output_path = cache_dir / f"{ts_code.replace('.', '_')}_factors.csv"
        save_factor_table(factor_df, output_path)
        print(f"{ts_code} {name}: saved factors to {output_path}")


if __name__ == "__main__":
    main()
