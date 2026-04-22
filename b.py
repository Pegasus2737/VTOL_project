import math
import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1, lon1, lat2, lon2):
    """
    計算兩組經緯度點之間的大圓距離（公尺）。
    支援 scalar 與 numpy array。
    """
    lat1 = np.asarray(lat1, dtype=float)
    lon1 = np.asarray(lon1, dtype=float)
    lat2 = np.asarray(lat2, dtype=float)
    lon2 = np.asarray(lon2, dtype=float)

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return EARTH_RADIUS_M * c


def latlon_to_local_xy_m(lat, lon, lat_ref, lon_ref):
    """
    將經緯度轉為以參考點為中心的局部平面座標（公尺）。
    equirectangular approximation，適合小範圍漂移分析。
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    lat_ref_rad = math.radians(float(lat_ref))

    x = np.radians(lon - float(lon_ref)) * EARTH_RADIUS_M * math.cos(lat_ref_rad)
    y = np.radians(lat - float(lat_ref)) * EARTH_RADIUS_M
    return x, y


def cep_radius(errors_m, percentile):
    """
    回傳誤差半徑的百分位數（例如 CEP50、CEP95）。
    """
    err = np.asarray(errors_m, dtype=float)
    err = err[np.isfinite(err)]
    if err.size == 0:
        return float("nan")
    return float(np.percentile(err, percentile))


def _require_columns(df, columns):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _fmt_num(value):
    if value is None or not np.isfinite(value):
        return "N/A"
    return f"{value:.3f}"


def normalize_telemetry_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    將常見欄位命名統一成分析函式預期格式。
    支援 a.py 產生的 CSV 標頭與小寫版本。
    """
    out = df.copy()
    col_map = {
        "Timestamp": "pc_timestamp",
        "timestamp": "pc_timestamp",
        "MCU_Tick_ms": "mcu_tick_ms",
        "mcu_tick_ms": "mcu_tick_ms",
        "Time_UTC": "time_utc",
        "GPS_Valid": "gps_valid",
        "Fix_Quality": "fix_quality",
        "Satellites": "satellites",
        "satellites": "satellites",
        "HDOP": "hdop",
        "hdop": "hdop",
        "Latitude": "latitude_deg",
        "latitude": "latitude_deg",
        "latitude_deg": "latitude_deg",
        "Longitude": "longitude_deg",
        "longitude": "longitude_deg",
        "longitude_deg": "longitude_deg",
        "Altitude_m": "altitude_m",
        "altitude_m": "altitude_m",
        "Speed_kmh": "speed_kmh",
        "speed_kmh": "speed_kmh",
        "Course_deg": "course_deg",
    }
    rename_map = {c: col_map[c] for c in out.columns if c in col_map}
    out = out.rename(columns=rename_map)

    # 強制轉為數值，避免字串造成計算失敗
    numeric_cols = [
        "mcu_tick_ms",
        "latitude_deg",
        "longitude_deg",
        "speed_kmh",
        "satellites",
        "hdop",
        "altitude_m",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    return out

def process_telemetry_data(out):
    """
    處理遙測數據，計算距離與時間戳記 [cite: 3, 4]
    """
    out = normalize_telemetry_columns(out)
    _require_columns(out, ["latitude_deg", "longitude_deg", "mcu_tick_ms"])

    # 移除關鍵欄位無法計算的列
    out = out.dropna(subset=["latitude_deg", "longitude_deg", "mcu_tick_ms"]).reset_index(drop=True)

    if len(out) == 0:
        out["segment_distance_m"] = pd.Series(dtype=float)
        out["cumulative_distance_m"] = pd.Series(dtype=float)
        out["elapsed_s"] = pd.Series(dtype=float)
        return out

    # 計算航段距離 (Segment Distance)
    if len(out) > 1:
        seg = haversine_m(
            out["latitude_deg"].values[:-1], 
            out["longitude_deg"].values[:-1],
            out["latitude_deg"].values[1:], 
            out["longitude_deg"].values[1:]
        )
        out["segment_distance_m"] = np.insert(seg, 0, 0.0)
    else:
        out["segment_distance_m"] = np.array([0.0], dtype=float)

    # 計算累積距離 [cite: 4]
    out["cumulative_distance_m"] = out["segment_distance_m"].cumsum()

    # 計算經過時間 (秒) [cite: 4]
    if "pc_timestamp" in out.columns and out["pc_timestamp"].notna().any():
        ts = pd.to_datetime(out["pc_timestamp"], errors="coerce")
        valid_ts = ts.dropna()
        if len(valid_ts):
            t0 = valid_ts.iloc[0]
            out["elapsed_s"] = (ts - t0).dt.total_seconds().fillna(0.0)
        else:
            out["elapsed_s"] = (out["mcu_tick_ms"] - out["mcu_tick_ms"].iloc[0]) / 1000.0
    else:
        # 若無 PC 時間戳，則使用 MCU 的 Tick 進行計算 [cite: 4]
        out["elapsed_s"] = (out["mcu_tick_ms"] - out["mcu_tick_ms"].iloc[0]) / 1000.0
    
    return out

def compute_summary(df: pd.DataFrame, gt_lat: Optional[float], gt_lon: Optional[float]) -> dict:
    """
    計算統計摘要與誤差分析 [cite: 4, 5, 6, 7, 8, 9]
    """
    _require_columns(
        df,
        [
            "elapsed_s",
            "segment_distance_m",
            "speed_kmh",
            "satellites",
            "hdop",
            "altitude_m",
            "latitude_deg",
            "longitude_deg",
        ],
    )

    summary = {}
    summary["samples"] = int(len(df))
    summary["duration_s"] = float(df["elapsed_s"].iloc[-1] - df["elapsed_s"].iloc[0]) if len(df) >= 2 else 0.0
    summary["total_distance_m"] = float(df["segment_distance_m"].sum())
    
    # 速度與衛星資訊統計 [cite: 5, 6]
    summary["mean_speed_kmh"] = float(df["speed_kmh"].mean()) if len(df) else float("nan")
    summary["max_speed_kmh"] = float(df["speed_kmh"].max()) if len(df) else float("nan")
    summary["mean_satellites"] = float(df["satellites"].mean()) if len(df) else float("nan")
    summary["min_satellites"] = float(df["satellites"].min()) if len(df) else float("nan")
    summary["mean_hdop"] = float(df["hdop"].mean()) if len(df) else float("nan")
    summary["max_hdop"] = float(df["hdop"].max()) if len(df) else float("nan")
    
    # 高度統計 [cite: 7]
    summary["mean_altitude_m"] = float(df["altitude_m"].mean()) if len(df) else float("nan")
    summary["altitude_std_m"] = float(df["altitude_m"].std(ddof=0)) if len(df) else float("nan")

    # 靜態漂移分析 [cite: 7, 8]
    if len(df):
        lat_mean = float(df["latitude_deg"].mean())
        lon_mean = float(df["longitude_deg"].mean())
        x, y = latlon_to_local_xy_m(df["latitude_deg"].values, df["longitude_deg"].values, lat_mean, lon_mean)
        radial = np.sqrt(x**2 + y**2)
        summary["static_drift_mean_center_m"] = float(radial.mean())
        summary["static_drift_max_center_m"] = float(radial.max())
    else:
        summary["static_drift_mean_center_m"] = float("nan")
        summary["static_drift_max_center_m"] = float("nan")

    # 地面真值誤差分析 (Ground Truth Error) [cite: 8, 9]
    if gt_lat is not None and gt_lon is not None and len(df):
        gt_lat_arr = np.full(len(df), gt_lat)
        gt_lon_arr = np.full(len(df), gt_lon)
        err = haversine_m(df["latitude_deg"].values, df["longitude_deg"].values, gt_lat_arr, gt_lon_arr)
        summary["error_mean_m"] = float(np.mean(err))
        summary["error_max_m"] = float(np.max(err))
        summary["error_rmse_m"] = float(np.sqrt(np.mean(err**2)))
        summary["cep50_m"] = cep_radius(err, 50)
        summary["cep95_m"] = cep_radius(err, 95)
    else:
        summary["error_mean_m"] = float("nan")
        summary["error_max_m"] = float("nan")
        summary["error_rmse_m"] = float("nan")
        summary["cep50_m"] = float("nan")
        summary["cep95_m"] = float("nan")

    return summary

def save_summary_txt(summary: dict, outpath: Path, gt_lat: Optional[float], gt_lon: Optional[float]) -> None:
    """
    將分析結果存成文字檔 [cite: 10, 11, 12]
    """
    lines = []
    lines.append("A16 Offline Analysis Summary")
    lines.append("=" * 50)
    lines.append(f"Samples               : {summary['samples']}")
    lines.append(f"Duration (s)          : {_fmt_num(summary.get('duration_s'))}")
    lines.append(f"Total Distance (m)    : {_fmt_num(summary.get('total_distance_m'))}")
    lines.append(f"Mean Speed (km/h)     : {_fmt_num(summary.get('mean_speed_kmh'))}")
    lines.append(f"Max Speed (km/h)      : {_fmt_num(summary.get('max_speed_kmh'))}")
    lines.append(f"Mean Satellites       : {_fmt_num(summary.get('mean_satellites'))}")
    lines.append(f"Min Satellites        : {_fmt_num(summary.get('min_satellites'))}")
    lines.append(f"Mean HDOP             : {_fmt_num(summary.get('mean_hdop'))}")
    lines.append(f"Max HDOP              : {_fmt_num(summary.get('max_hdop'))}")
    lines.append(f"Mean Altitude (m)     : {_fmt_num(summary.get('mean_altitude_m'))}")
    lines.append(f"Altitude Std (m)      : {_fmt_num(summary.get('altitude_std_m'))}")
    lines.append(f"Static Drift Mean (m) : {_fmt_num(summary.get('static_drift_mean_center_m'))}")
    lines.append(f"Static Drift Max (m)  : {_fmt_num(summary.get('static_drift_max_center_m'))}")
    lines.append("")
    lines.append(f"Ground Truth Latitude : {gt_lat if gt_lat is not None else 'N/A'}")
    lines.append(f"Ground Truth Longitude: {gt_lon if gt_lon is not None else 'N/A'}")
    lines.append(f"Error Mean (m)        : {_fmt_num(summary.get('error_mean_m'))}")
    lines.append(f"Error Max (m)         : {_fmt_num(summary.get('error_max_m'))}")
    lines.append(f"Error RMSE (m)        : {_fmt_num(summary.get('error_rmse_m'))}")
    lines.append(f"CEP50 (m)             : {_fmt_num(summary.get('cep50_m'))}")
    lines.append(f"CEP95 (m)             : {_fmt_num(summary.get('cep95_m'))}")
    
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_offline_analysis(
    input_csv: Path,
    output_txt: Optional[Path] = None,
    gt_lat: Optional[float] = None,
    gt_lon: Optional[float] = None,
) -> dict:
    """
    從 CSV 載入資料，執行處理與摘要輸出。
    """
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df_raw = pd.read_csv(input_csv)
    df_proc = process_telemetry_data(df_raw)
    summary = compute_summary(df_proc, gt_lat, gt_lon)

    if output_txt is None:
        output_txt = input_csv.with_name(f"{input_csv.stem}_Summary.txt")

    save_summary_txt(summary, output_txt, gt_lat, gt_lon)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Offline telemetry analysis for CSV logs.")
    parser.add_argument("input_csv", nargs="?", help="Path to telemetry CSV file")
    parser.add_argument("--out", dest="out_txt", help="Path to output summary txt")
    parser.add_argument("--gt-lat", type=float, default=None, help="Ground truth latitude")
    parser.add_argument("--gt-lon", type=float, default=None, help="Ground truth longitude")

    args = parser.parse_args()

    if not args.input_csv:
        print("No input CSV provided.")
        print("Usage:")
        print("  python b.py <input_csv> [--out output.txt] [--gt-lat 25.0 --gt-lon 121.5]")
        return 0

    input_csv = Path(args.input_csv)
    out_txt = Path(args.out_txt) if args.out_txt else None

    try:
        summary = run_offline_analysis(input_csv, out_txt, args.gt_lat, args.gt_lon)
        output_path = out_txt if out_txt is not None else input_csv.with_name(f"{input_csv.stem}_Summary.txt")
        print(f"Analysis completed: {output_path}")
        print(f"Samples: {summary['samples']}")
        print(f"Duration (s): {_fmt_num(summary.get('duration_s'))}")
        print(f"Total Distance (m): {_fmt_num(summary.get('total_distance_m'))}")
        return 0
    except Exception as exc:
        print(f"Analysis failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())