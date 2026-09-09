#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财日度导出 → 二级行业汇总

每天把「MACD红柱」「涨跌幅>0」两个 Excel 汇总到 二级行业_MACD.xlsx

用法（在 Windows PowerShell）:
  cd 本脚本所在目录
  pip install pandas openpyxl
  python daily_industry_stats.py
  python daily_industry_stats.py --date 2026-09-09
  python daily_industry_stats.py --dir "C:\\Users\\Administrator\\Desktop\\问财无限下载器v9"
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# ========= 默认目录（可按你的机器修改）=========
DEFAULT_DIR = Path(r"C:\Users\Administrator\Desktop\问财无限下载器v9")
OUTPUT_NAME = "二级行业_MACD.xlsx"

# 文件名模板（日期用 YYYY-MM-DD）
MACD_NAME_TMPL = "{date}日MACD红柱，显示二级行业.xlsx"
UP_NAME_TMPL = "{date}日涨跌幅大于0，显示二级行业.xlsx"

# 可能的「二级行业」列名（按优先级匹配）
INDUSTRY_CANDIDATES = [
    "二级行业",
    "所属同花顺二级行业",
    "同花顺二级行业",
    "二级行业名称",
    "行业",
    "所属行业",
]

# 可能的股票代码 / 名称列（用于计数去重，没有也能按行数统计）
CODE_CANDIDATES = ["股票代码", "代码", "证券代码", "code", "symbol"]
NAME_CANDIDATES = ["股票简称", "股票名称", "名称", "证券简称", "name"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="二级行业日度汇总")
    p.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_DIR,
        help="问财导出目录",
    )
    p.add_argument(
        "--date",
        type=str,
        default=None,
        help="交易日 YYYY-MM-DD；默认今天（或从目录里自动找最新日期）",
    )
    p.add_argument(
        "--auto-latest",
        action="store_true",
        help="若不指定 --date，从目录文件名中自动取最新日期",
    )
    return p.parse_args()


def find_latest_date(data_dir: Path) -> str | None:
    dates: list[str] = []
    for f in data_dir.glob("*.xlsx"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})日", f.name)
        if m:
            dates.append(m.group(1))
    if not dates:
        return None
    return max(dates)


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    cols = list(columns)
    # 精确匹配
    for c in candidates:
        if c in cols:
            return c
    # 模糊包含
    for c in candidates:
        for col in cols:
            if c in str(col):
                return str(col)
    return None


def load_sheet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {path}")
    # 问财有时第一行是标题说明，失败则尝试 header=1
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception:
        df = pd.read_excel(path)

    if df.empty or all(str(c).startswith("Unnamed") for c in df.columns):
        df = pd.read_excel(path, header=1, engine="openpyxl")

    # 去掉全空行
    df = df.dropna(how="all")
    return df


def aggregate_by_industry(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    """按二级行业统计家数，返回 DataFrame: 二级行业, {tag}_家数, {tag}_占比%"""
    industry_col = pick_column(list(df.columns), INDUSTRY_CANDIDATES)
    if not industry_col:
        raise ValueError(
            f"[{tag}] 未找到二级行业列。当前列名: {list(df.columns)}\n"
            f"请把实际列名告诉我，或改脚本里 INDUSTRY_CANDIDATES。"
        )

    code_col = pick_column(list(df.columns), CODE_CANDIDATES)
    work = df.copy()
    work[industry_col] = work[industry_col].astype(str).str.strip()
    work = work[work[industry_col].notna() & (work[industry_col] != "") & (work[industry_col] != "nan")]

    if code_col:
        work[code_col] = work[code_col].astype(str).str.strip()
        # 去掉代码后缀如 .SZ
        grp = work.drop_duplicates(subset=[industry_col, code_col])
        counts = grp.groupby(industry_col, dropna=False)[code_col].nunique()
    else:
        counts = work.groupby(industry_col, dropna=False).size()

    total = int(counts.sum())
    out = counts.rename(f"{tag}_家数").reset_index()
    out.columns = ["二级行业", f"{tag}_家数"]
    out[f"{tag}_占比%"] = (out[f"{tag}_家数"] / total * 100).round(2) if total else 0.0
    out = out.sort_values(f"{tag}_家数", ascending=False).reset_index(drop=True)
    return out, total, industry_col, code_col


def merge_stats(macd_df: pd.DataFrame, up_df: pd.DataFrame, trade_date: str) -> pd.DataFrame:
    merged = pd.merge(macd_df, up_df, on="二级行业", how="outer").fillna(0)
    for c in ["MACD红柱_家数", "涨跌幅>0_家数"]:
        if c in merged.columns:
            merged[c] = merged[c].astype(int)
    # 综合分：两边都上榜更强（可按需要改权重）
    if "MACD红柱_家数" in merged.columns and "涨跌幅>0_家数" in merged.columns:
        merged["综合家数"] = merged["MACD红柱_家数"] + merged["涨跌幅>0_家数"]
        merged["双上榜"] = (
            (merged["MACD红柱_家数"] > 0) & (merged["涨跌幅>0_家数"] > 0)
        ).map({True: "是", False: "否"})
        merged = merged.sort_values(
            ["双上榜", "综合家数", "MACD红柱_家数"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

    merged.insert(0, "日期", trade_date)
    return merged


def write_output(
    out_path: Path,
    day_df: pd.DataFrame,
    trade_date: str,
    meta: dict,
) -> None:
    """
    写入/追加：
    - 明细_按日：每天一个 sheet，或统一「按日明细」追加
    - 汇总_最新：覆盖为当日完整表
    - 历史_长表：不断 append 每日各行业一行
    """
    history_rows = day_df.copy()

    if out_path.exists():
        try:
            old_hist = pd.read_excel(out_path, sheet_name="历史_长表", engine="openpyxl")
            # 删掉同一天旧数据再追加（支持重跑）
            if "日期" in old_hist.columns:
                old_hist = old_hist[old_hist["日期"].astype(str) != trade_date]
            history = pd.concat([old_hist, history_rows], ignore_index=True)
        except Exception:
            history = history_rows
    else:
        history = history_rows

    # 行业宽表：每个行业一行，最近若干列可后续扩展；这里保留「最新一日」+「历史」
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        day_df.to_excel(writer, sheet_name="汇总_最新", index=False)
        history.to_excel(writer, sheet_name="历史_长表", index=False)

        # 元信息
        meta_df = pd.DataFrame([meta])
        meta_df.to_excel(writer, sheet_name="运行信息", index=False)

        # 当日双上榜行业速览
        if "双上榜" in day_df.columns:
            both = day_df[day_df["双上榜"] == "是"].copy()
            both.to_excel(writer, sheet_name="当日双上榜", index=False)


def main() -> None:
    args = parse_args()
    data_dir: Path = args.dir

    if not data_dir.exists():
        raise SystemExit(f"目录不存在: {data_dir}")

    trade_date = args.date
    if not trade_date:
        if args.auto_latest or True:
            trade_date = find_latest_date(data_dir) or date.today().isoformat()
        else:
            trade_date = date.today().isoformat()

    macd_path = data_dir / MACD_NAME_TMPL.format(date=trade_date)
    up_path = data_dir / UP_NAME_TMPL.format(date=trade_date)
    out_path = data_dir / OUTPUT_NAME

    print(f"交易日: {trade_date}")
    print(f"MACD文件: {macd_path.name} 存在={macd_path.exists()}")
    print(f"涨跌文件: {up_path.name} 存在={up_path.exists()}")

    macd_raw = load_sheet(macd_path)
    up_raw = load_sheet(up_path)

    macd_stats, macd_total, macd_ind, macd_code = aggregate_by_industry(macd_raw, "MACD红柱")
    up_stats, up_total, up_ind, up_code = aggregate_by_industry(up_raw, "涨跌幅>0")

    print(f"MACD红柱: 行业列=[{macd_ind}] 代码列=[{macd_code}] 股票合计={macd_total}")
    print(f"涨跌幅>0: 行业列=[{up_ind}] 代码列=[{up_code}] 股票合计={up_total}")

    day_df = merge_stats(macd_stats, up_stats, trade_date)

    meta = {
        "运行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "交易日": trade_date,
        "MACD源文件": macd_path.name,
        "涨跌源文件": up_path.name,
        "MACD股票数": macd_total,
        "上涨股票数": up_total,
        "行业数": int(day_df.shape[0]),
        "双上榜行业数": int((day_df["双上榜"] == "是").sum()) if "双上榜" in day_df.columns else 0,
    }

    write_output(out_path, day_df, trade_date, meta)

    print(f"\n已写入: {out_path}")
    print("Sheet: 汇总_最新 | 历史_长表 | 当日双上榜 | 运行信息")
    print("\n【汇总_最新】预览 Top10:")
    cols = [c for c in ["二级行业", "MACD红柱_家数", "涨跌幅>0_家数", "综合家数", "双上榜"] if c in day_df.columns]
    print(day_df[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
