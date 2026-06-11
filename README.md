[Group5] 房價趨勢與熱門成交物件特徵分析

本專案以雙北市（台北市＋新北市）2023Q1–2026Q1 的開價資料為主要來源，結合市場趨勢 EDA、熱銷物件特徵分析與機器學習估價建模，探討雙北房市的價格動能與物件特徵，並以互動網頁呈現分析結果。

研究問題


雙北房市 2023–2026Q1 的季度單價趨勢與各區成交動能如何變化？
哪些物件特徵讓一個物件「熱銷」（快速成交）？
在控制區域因素之後，哪些特徵決定了單價的折溢價？能否據此找出市場上被低估的物件？


Contributors

組員系級學號工作分配江凱倫資科碩一114753144資料清洗與探索分析：特徵工程、EDA 圖表製作、資料洞察撰寫黃育程資科碩一114753219價格預測建模：多模型訓練調參、模型評估比較、特徵重要性分析（SHAP）辛柏慶資科碩一114753220熱銷物件分析：開價資料處理、熱銷天數統計、熱門房型特徵歸納林城誼資科碩一114753211互動式網頁開發：Leaflet 地圖視覺化、圖表整合、Demo 展示部署林秋瑢資科碩一114753213專案統籌與視覺整合：GitHub 維護、Poster 設計輸出、投影片編排

Quick start

bash# 安裝相依套件
pip install -r requirements.txt

# Phase 1：資料清洗與 EDA（需先備妥開價原始 xlsx，詳見 data/ 說明）
python code/01_eda.py

# Phase 2：熱銷物件分析
python code/02_hot_property.py

# Phase 3：估價建模（LightGBM + SHAP）
jupyter notebook code/final_model.ipynb

# Phase 4：互動網頁（本地預覽）
cd web && python -m http.server 8080


注意：原始開價資料（2023/2024/2025/202603_開價.xlsx，合計約 144.5 萬筆）體積過大，不放入 repo。請依 data/README_data.md 說明自行取得，或聯繫組員索取處理後的 CSV。



Folder organization and its related description

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

docs


1132_DS-FP_group5.pptx：期末報告投影片，含研究動機、資料來源與前處理、市場概況、建模方法、模型效能與特徵、低估物件與熱銷分析、線上 Demo、結論。截止日 06.10。
poster_group5.pdf：A1 直式海報，2026 NCCU Innofest（6/01）展示版本。
meeting_records/：兩次小組會議記錄（2026/04/30、2026/05/14）。


data

輸入資料（體積過大，不放入 repo）

檔案來源筆數用途2023_開價.xlsx比房網（網路爬蟲）~47.4 萬筆熱銷分析、建模2024_開價.xlsx比房網（網路爬蟲）~41.5 萬筆同上2025_開價.xlsx比房網（網路爬蟲）~42.9 萬筆同上202603_開價.xlsx比房網（網路爬蟲）~12.8 萬筆同上（至 2026/03）成交資料內政部實價登錄雙北約 11.5 萬筆市場趨勢 EDA

合計開價原始資料約 144.5 萬筆，清洗後約 131 萬筆。分析聚焦雙北住宅類物件（電梯大樓／住宅大樓／公寓／華廈），排除商業用途。

主要欄位：ym（年月）、city/dist（縣市/行政區）、road（路名）、type（建物類別）、age（屋齡）、size（建坪）、main（主建物坪數）、room（房數）、low/high/floor（樓層）、park（車位類別）、price（總價萬）、unit（單價萬/坪）、saledays（掛牌天數）、x/y（座標）


資料聲明：開價資料來自比房網爬蟲、成交資料來自內政部實價登錄，僅供課程學術研究使用，請勿作商業用途。



code

Phase 1 — 資料清洗與 EDA（01_eda.py）


篩選住宅類物件、排除商業用途
特徵工程：相對樓層 Relative_Floor = high / floor、得房率 Efficiency_Ratio = main / size、車位類別 one-hot（平面／機械／無）
屋齡缺值以同縣市×行政區中位數填補
產出：季度單價趨勢圖、各區交易量圖等


Phase 2 — 熱銷物件分析（02_hot_property.py）


熱銷定義：saledays < 各行政區中位數 × 0.5（相對門檻，因各區市場速度差異大）
分析各區×年度最熱銷房型與市場動能變化
使用套件：pandas、numpy、matplotlib


Phase 3 — 估價建模（final_model.ipynb）


目標變數：物件單價 ÷ 該行政區當季平均單價（區域中性化折溢價比例，label 欄位名稱 unit）
時序切分：train = 2023–2025、test = 2026Q1（避免 data leakage，非隨機切分）
模型：LightGBM（最佳）、Random Forest、XGBoost、Ridge、Null model（行政區季均價）；共比較 9 組「模型 × 特徵策略」設定
Null model：以各行政區當季平均單價作為預測值（折溢價 = 1.0），作為性能下限基準
評估指標：MSE、R²（2026Q1 測試集）
解釋性：SHAP summary plot + LightGBM feature importance
產出：results/model_comparison.csv、SHAP 圖、Top 30 低估物件清單


results

模型比較（2026Q1 測試集）

Model TypeFeature StrategyMSER²Random Forest+ size + Efficiency_Ratio0.05020.5505LightGBM+ size + Efficiency_Ratio0.05030.55LightGBM+ size0.05240.531LightGBM+ Efficiency_Ratio0.05430.514XGBoost+ size + Efficiency_Ratio0.05430.514LightGBM+ main0.05480.510LightGBMModel A（無坪數）0.06020.461Ridge (Linear)Basic Features0.10470.056Null ModelBasic Features0.1109−0.0002

Random Forest 與 LightGBM（+ size + Efficiency_Ratio）表現實質並列；最終以 LightGBM 作為部署模型，主要考量訓練效率與部署便利性。

改善幅度：最佳模型相較 Null baseline 的 MSE 降低約 55%，大幅優於線性的 Ridge（R² 0.056），顯示房價折溢價存在強烈的非線性與空間結構。

SHAP 特徵影響力（高→低）：屋齡 > 相對樓層 > 行政區 > 總坪數 > 經緯度 > 房數 > 得房率 > 車位。其中車位對單價呈負向貢獻（車位坪數稀釋每坪單價）。

市場觀察：2026Q1 全體掛牌天數中位數由 2023–2025 年的約 62–80 天暴增至 163 天（大安 84→201、士林 82→210、中山 99→194 天），熱銷率亦由約 42–46% 降至約 36%，顯示市場明顯轉冷。

References

使用套件


pandas、numpy — 資料處理
scikit-learn — Ridge、Random Forest、資料切分
LightGBM — 主力建模
XGBoost — 梯度提升對照
SHAP — 模型可解釋性
matplotlib、seaborn — 視覺化
Leaflet.js — 互動地圖（網頁端）


相關文獻


Chen T, Guestrin C (2016). XGBoost: A Scalable Tree Boosting System. KDD 2016.
Ke G et al. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. NeurIPS 2017.
Lundberg SM, Lee SI (2017). A Unified Approach to Interpreting Model Predictions. NeurIPS 2017.
