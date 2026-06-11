[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/HR2Xz9sU)
# [Group5] 房價趨勢與熱門成交物件特徵分析

本專案以雙北市（台北市＋新北市）2023Q1–2026Q1 的開價資料為主要來源，結合市場趨勢 EDA、熱銷物件特徵分析與機器學習估價建模，探討雙北房市的價格動能與物件特徵，並以互動網頁呈現分析結果。

**研究問題**
1. 雙北房市 2023–2026Q1 的季度單價趨勢與各區成交動能如何變化？
2. 哪些物件特徵讓一個物件「熱銷」（快速成交）？
3. 在控制區域因素之後，哪些特徵決定了單價的折溢價？能否據此找出市場上被低估的物件？

## Contributors

|組員|系級|學號|工作分配|
|-|-|-|-|
|江凱倫|資科碩一|114753144|資料清洗與探索分析：特徵工程、EDA 圖表製作、資料洞察撰寫|
|黃育程|資科碩一|114753219|價格預測建模：多模型訓練調參、模型評估比較、特徵重要性分析（SHAP）|
|辛柏慶|資科碩一|114753220|熱銷物件分析：開價資料處理、熱銷天數統計、熱門房型特徵歸納|
|林城誼|資科碩一|114753211|互動式網頁開發：Leaflet 地圖視覺化、圖表整合、Demo 展示部署|
|林秋瑢|資科碩一|114753213|專案統籌與視覺整合：GitHub 維護、Poster 設計輸出、投影片編排|

## Quick start

```bash
# 安裝相依套件
pip install -r requirements.txt

# Phase 1：資料清洗與 EDA（需先備妥開價原始 xlsx，詳見 data/ 說明）
python code/01_eda.py

# Phase 2：熱銷物件分析
python code/02_hot_property.py

# Phase 3：估價建模（LightGBM + SHAP）
jupyter notebook code/final_model.ipynb

# Phase 4：互動網頁（本地預覽）
cd web && python -m http.server 8080
```

> **注意**：原始開價資料（`2023/2024/2025/202603_開價.xlsx`，合計約 144.5 萬筆）體積過大，不放入 repo。請依 `data/README_data.md` 說明自行取得，或聯繫組員索取處理後的 CSV。

## Folder organization and its related description

idea by Noble WS (2009) [A Quick Guide to Organizing Computational Biology Projects.](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1000424) PLoS Comput Biol 5(7): e1000424.

```
finalproject_group5/
├── README.md
├── requirements.txt
├── docs/
│   ├── 1132_DS-FP_group5.pptx          # 期末報告投影片（06.10 前上傳）
│   ├── poster_group5.pdf                # Innofest A1 海報
│   └── meeting_records/                 # 會議記錄
├── data/
│   ├── README_data.md                   # 資料取得說明
│   └── output/                          # 清洗後可放入 repo 的中間檔
├── code/
│   ├── 01_eda.py                        # Phase 1：資料清洗與 EDA
│   ├── 02_hot_property.py               # Phase 2：熱銷物件分析
│   └── final_model.ipynb                # Phase 3：估價建模主程式
├── results/
│   ├── model_comparison.csv             # 9 組模型比較結果
│   ├── top30_undervalued_2026Q1.csv     # 2026Q1 Top 30 低估物件
│   ├── hot_type_by_district_year.csv    # 各區×年度最熱銷類型
│   └── figures/                         # SHAP 圖、預測 vs 實際、殘差分布等
└── web/                                 # 互動網頁 Demo
    ├── index.html
    ├── style.css
    ├── app.js
    └── data/                            # GeoJSON、圖表用 JSON
```

### docs
- `1132_DS-FP_group5.pptx`：期末報告投影片，含研究動機、資料來源與前處理、市場概況、建模方法、模型效能與特徵、低估物件與熱銷分析、線上 Demo、結論。截止日 **06.10**。
- `poster_group5.pdf`：A1 直式海報，2026 NCCU Innofest（6/01）展示版本。
- `meeting_records/`：兩次小組會議記錄（2026/04/30、2026/05/14）。

### data

**輸入資料（體積過大，不放入 repo）**

| 檔案 | 來源 | 筆數 | 用途 |
|---|---|---|---|
| `2023_開價.xlsx` | 比房網（網路爬蟲） | ~47.4 萬筆 | 熱銷分析、建模 |
| `2024_開價.xlsx` | 比房網（網路爬蟲） | ~41.5 萬筆 | 同上 |
| `2025_開價.xlsx` | 比房網（網路爬蟲） | ~42.9 萬筆 | 同上 |
| `202603_開價.xlsx` | 比房網（網路爬蟲） | ~12.8 萬筆 | 同上（至 2026/03） |
| 成交資料 | 內政部實價登錄 | 雙北約 11.5 萬筆 | 市場趨勢 EDA |

合計開價原始資料約 **144.5 萬筆**，清洗後約 131 萬筆。分析聚焦雙北住宅類物件（電梯大樓／住宅大樓／公寓／華廈），排除商業用途。

**主要欄位**：`ym`（年月）、`city`/`dist`（縣市/行政區）、`road`（路名）、`type`（建物類別）、`age`（屋齡）、`size`（建坪）、`main`（主建物坪數）、`room`（房數）、`low`/`high`/`floor`（樓層）、`park`（車位類別）、`price`（總價萬）、`unit`（單價萬/坪）、`saledays`（掛牌天數）、`x`/`y`（座標）

> 資料聲明：開價資料來自比房網爬蟲、成交資料來自內政部實價登錄，僅供課程學術研究使用，請勿作商業用途。

### code

**Phase 1 — 資料清洗與 EDA（`01_eda.py`）**
- 篩選住宅類物件、排除商業用途
- 特徵工程：相對樓層 `Relative_Floor = high / floor`、得房率 `Efficiency_Ratio = main / size`、車位類別 one-hot（平面／機械／無）
- 屋齡缺值以同縣市×行政區中位數填補
- 產出：季度單價趨勢圖、各區交易量圖等

**Phase 2 — 熱銷物件分析（`02_hot_property.py`）**
- 熱銷定義：`saledays < 各行政區中位數 × 0.5`（相對門檻，因各區市場速度差異大）
- 分析各區×年度最熱銷房型與市場動能變化
- 使用套件：pandas、numpy、matplotlib

**Phase 3 — 估價建模（`final_model.ipynb`）**
- **目標變數**：`物件單價 ÷ 該行政區當季平均單價`（區域中性化折溢價比例，label 欄位名稱 `unit`）
- **時序切分**：train = 2023–2025、test = 2026Q1（避免 data leakage，非隨機切分）
- **模型**：LightGBM（最佳）、Random Forest、XGBoost、Ridge、Null model（行政區季均價）；共比較 9 組「模型 × 特徵策略」設定
- **Null model**：以各行政區當季平均單價作為預測值（折溢價 = 1.0），作為性能下限基準
- **評估指標**：MSE、R²（2026Q1 測試集）
- **解釋性**：SHAP summary plot + LightGBM feature importance
- 產出：`results/model_comparison.csv`、SHAP 圖、Top 30 低估物件清單

### results

**模型比較（2026Q1 測試集）**

| Model Type | Feature Strategy | MSE | R² |
|---|---|---|---|
| Random Forest | + size + Efficiency_Ratio | 0.0502 | 0.5505 |
| **LightGBM** | **+ size + Efficiency_Ratio** | **0.0503** | **0.55** |
| LightGBM | + size | 0.0524 | 0.531 |
| LightGBM | + Efficiency_Ratio | 0.0543 | 0.514 |
| XGBoost | + size + Efficiency_Ratio | 0.0543 | 0.514 |
| LightGBM | + main | 0.0548 | 0.510 |
| LightGBM | Model A（無坪數） | 0.0602 | 0.461 |
| Ridge (Linear) | Basic Features | 0.1047 | 0.056 |
| Null Model | Basic Features | 0.1109 | −0.0002 |

Random Forest 與 LightGBM（+ size + Efficiency_Ratio）表現實質並列；最終以 **LightGBM** 作為部署模型，主要考量訓練效率與部署便利性。

**改善幅度**：最佳模型相較 Null baseline 的 MSE 降低約 **55%**，大幅優於線性的 Ridge（R² 0.056），顯示房價折溢價存在強烈的非線性與空間結構。

**SHAP 特徵影響力（高→低）**：屋齡 > 相對樓層 > 行政區 > 總坪數 > 經緯度 > 房數 > 得房率 > 車位。其中車位對單價呈**負向**貢獻（車位坪數稀釋每坪單價）。

**市場觀察**：2026Q1 全體掛牌天數中位數由 2023–2025 年的約 62–80 天暴增至 163 天（大安 84→201、士林 82→210、中山 99→194 天），熱銷率亦由約 42–46% 降至約 36%，顯示市場明顯轉冷。

## References

**使用套件**
- [pandas](https://pandas.pydata.org/)、[numpy](https://numpy.org/) — 資料處理
- [scikit-learn](https://scikit-learn.org/) — Ridge、Random Forest、資料切分
- [LightGBM](https://lightgbm.readthedocs.io/) — 主力建模
- [XGBoost](https://xgboost.readthedocs.io/) — 梯度提升對照
- [SHAP](https://shap.readthedocs.io/) — 模型可解釋性
- [matplotlib](https://matplotlib.org/)、[seaborn](https://seaborn.pydata.org/) — 視覺化
- [Leaflet.js](https://leafletjs.com/) — 互動地圖（網頁端）

**相關文獻**
- Noble WS (2009). A Quick Guide to Organizing Computational Biology Projects. *PLoS Comput Biol* 5(7): e1000424.
- Chen T, Guestrin C (2016). XGBoost: A Scalable Tree Boosting System. *KDD 2016*.
- Ke G et al. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS 2017*.
- Lundberg SM, Lee SI (2017). A Unified Approach to Interpreting Model Predictions. *NeurIPS 2017*.
