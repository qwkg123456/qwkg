# 二级行业日度统计（问财导出）

把每天导出的两个 Excel：

- `YYYY-MM-DD日MACD红柱，显示二级行业.xlsx`
- `YYYY-MM-DD日涨跌幅大于0，显示二级行业.xlsx`

汇总到同目录：

- `二级行业_MACD.xlsx`

## 安装

```powershell
pip install pandas openpyxl
```

## 每天怎么跑

问财下载完两个文件后：

```powershell
cd C:\Users\Administrator\Desktop\问财无限下载器v9
# 把本脚本拷到该目录，或写全路径运行

python daily_industry_stats.py --dir "C:\Users\Administrator\Desktop\问财无限下载器v9"
```

指定某一天：

```powershell
python daily_industry_stats.py --date 2026-09-09 --dir "C:\Users\Administrator\Desktop\问财无限下载器v9"
```

不传 `--date` 时，会从目录里文件名自动取**最新日期**。

## 输出说明

| Sheet | 内容 |
|-------|------|
| 汇总_最新 | 当天各二级行业：MACD红柱家数、上涨家数、占比、是否双上榜 |
| 历史_长表 | 每天追加，可做趋势；同一天重跑会覆盖该日 |
| 当日双上榜 | MACD红柱与上涨同时出现的行业 |
| 运行信息 | 源文件、合计家数等 |

## 列名对不上时

打开源 Excel 看表头，把真实的「二级行业」列名加到脚本里的 `INDUSTRY_CANDIDATES`。

## 说明

- 前半 SHA 类字段与本脚本无关；本脚本只做行业家数统计。
- ETF-MACD / ETF-涨跌若也是「成分股清单 + 二级行业」列，可同样改文件名模板复用逻辑。
