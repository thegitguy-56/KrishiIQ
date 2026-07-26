# KrishiIQ — Machine Learning Components: Full Documentation

This document explains what existed before, what was changed, and why, for all three ML
components in KrishiIQ: the disease detector, the yield predictor, and the field-level
pest/disease spread risk model. Written for inclusion in the final year project report.

---

## Summary

| Component | Before | After |
|---|---|---|
| Disease Detector | Fake — color-brightness heuristic disguised as EfficientNet-B4 | Real EfficientNet-B4, trained on 20,566 images, 11 of 16 classes |
| Yield Predictor | Fake — hardcoded formula, silently ignored 2 of its own inputs | Real hybrid model — trained Gradient Boosting regressor + honest fallback, wired to a new API endpoint that didn't exist before |
| Field Risk Model | Mislabeled — called a "Graph Neural Network," was actually a rule-based formula with no ML at all | Honestly relabeled as a geospatial heuristic, plus a real bug fixed (crop-matching logic was comparing null values) |

---

## 1. Disease Detector

### What it was
`app/ml/disease_detector.py` had legitimate, correctly-wired EfficientNet-B4 inference code (via
`timm`), but no trained weight file existed anywhere in the repo. With no `.pt` file present, the
code silently fell back to a **demo detector** that guessed a disease class from the average RGB
brightness of the image — not real disease detection, despite looking fully functional from the API
surface.

### What was built
A complete training pipeline (Colab notebook: `KrishiIQ_Disease_Detector_Training.ipynb`) that:

1. Automatically downloads two datasets via `kagglehub` (no manual file handling):
   - **Rice Leaf Disease Image** (nirmalsankalana) — 5,932 images: Bacterial_Blight, Leaf_Blast, Brown_Spot, Tungro
   - **PlantVillage full 38-class, non-augmented, color-only** (abdallahalidev) — Rust, Early/Late Blight, Powdery_Mildew, Leaf_Curl, Mosaic_Virus, Healthy
2. Maps dataset folders to the app's 16 originally-scoped disease classes, with a printed coverage
   report showing exactly which classes have real training data
3. Fine-tunes an ImageNet-pretrained EfficientNet-B4 with data augmentation and class-weighted loss
   (to offset ~19x imbalance between the smallest and largest class)
4. Evaluates on a held-out test split and on genuinely unseen real-world photos (not from either
   training dataset) — this second check is what caught the data leakage issue described below
5. Exports `efficientnet_disease.pt` in the exact format the existing loader code expects

### Final trained classes (11 of 16)
`Bacterial_Blight, Brown_Spot, Early_Blight, Healthy, Late_Blight, Leaf_Blast, Leaf_Curl,
Mosaic_Virus, Powdery_Mildew, Rust, Tungro`

**Excluded (no sufficient public labeled data found):** Neck_Blast, Sheath_Blight, False_Smut,
Downy_Mildew, Anthracnose.

### Data leakage — found, diagnosed, and fixed
An earlier training run using the **augmented** version of PlantVillage ("New Plant Diseases
Dataset") produced a suspicious 99.96% test accuracy. This was investigated and traced to a known
issue: the augmented dataset contains multiple rotated/flipped/zoomed copies of the same source
photo, and when split into train/test at the file level, near-duplicate copies of one leaf end up on
both sides of the split — the model partly memorizes rather than generalizes.

**Fix:** switched to the original, non-augmented PlantVillage dataset. Re-training produced
99.81% internal test accuracy — still very high, prompting a further real-world sanity check.

### Real-world generalization check
Since PlantVillage images (any version) are shot under controlled lab conditions, 11 real field/
extension-site photographs (never seen in training) were used as an out-of-distribution test:

- **Internal test accuracy: 99.81%**
- **Real-photo accuracy: ~45% (5/11 correct)**

This large gap is consistent with published findings (Mohanty et al., 2016) on PlantVillage-trained
models' limited field generalization, not an implementation error. A notable failure mode: two
genuinely Early_Blight tomato photos were misclassified as Late_Blight with 99%+ confidence —
high-confidence wrong answers of this kind indicate the model learned dataset-specific visual cues
(background, framing) rather than true disease-distinguishing features.

**Decision:** given final year project timeline constraints, this gap was documented rather than
chased further. Closing it would require field-collected training data or domain adaptation
techniques (background augmentation, style transfer, fine-tuning on a small real-world calibration
set) — noted as future work.

### Files changed
- `backend/app/ml/disease_detector.py` — `DISEASE_CLASSES` trimmed to the 11 trained classes (exact
  order matters — matches the training class-index mapping); added treatment text (English/Hindi/
  Tamil) for the 4 classes that were trained but previously had no treatment entry (Tungro,
  Powdery_Mildew, Leaf_Curl, Mosaic_Virus)
- `backend/ml/weights/efficientnet_disease.pt` — new trained weight file (not committed until
  training completes; ~70-80MB)

---

## 2. Yield Predictor

### What it was
`app/ml/yield_predictor.py` was not machine learning at all — a hardcoded formula (base yield per
crop x manually-chosen multipliers for soil type, moisture, pH, disease severity). It also silently
**ignored two of its own accepted parameters**, `rainfall_mm` and `temperature_avg` — a real bug,
separate from the "not really ML" issue.

**Also discovered during integration:** `predict_yield()` was never actually called from any API
route or service in the backend. `YIELD_MODEL_PATH` was declared in `config.py` but unused
elsewhere — the yield prediction feature was scaffolded but never wired up.

### What was built

**Training** (Colab notebook: `KrishiIQ_Yield_Predictor_Training.ipynb`):
- Dataset: `samuelotiattakorah/agriculture-crop-yield` (1,000,000 rows: Region, Soil_Type, Crop,
  Rainfall_mm, Temperature_Celsius, Fertilizer_Used, Irrigation_Used, Yield_tons_per_hectare)
- Trained and compared RandomForestRegressor vs GradientBoostingRegressor on 4 features (crop, soil
  type, rainfall, temperature) predicting yield
- **Result: GradientBoosting, R²=0.591, MAE=359.0 kg/acre, RMSE=439.7 kg/acre**
- Exported model + label encoders + feature column order via `joblib`

**Honest scope limitation:** this dataset does not include soil pH, moisture, or nitrogen readings
— no well-matched public dataset combining those with crop/rainfall/temperature/yield was found.
Rather than fabricate a relationship by merging two unrelated datasets, the model trains only on the
4 features it has genuine data for. `avg_soil_ph`, `avg_soil_moisture`, `avg_nitrogen` remain in the
function signature for interface compatibility but aren't used by this model version.

**Category coverage gap:** the training dataset's crop/soil categories are generic (Barley, Cotton,
Maize, Rice, Soybean, Wheat / Chalky, Clay, Loam, Peaty, Sandy, Silt), not fully matching the app's
India-specific categories (e.g. sugarcane, groundnut, sorghum; sandy_loam, black_cotton,
red_laterite). Resolved with a **hybrid design**:

- If the crop AND soil type are both ones the model was trained on → use the real trained model
- Otherwise → fall back to the original rule-based formula
- The API response includes `"prediction_method": "ml_model"` or `"heuristic_fallback"` so the
  frontend can display an appropriate confidence indicator rather than presenting both as equally
  precise

### On R²=0.591 — why this is a reasonable result, not a weak one
Unlike the disease detector's suspicious 99.96%, an R² around 0.59 using only 4 features (crop,
soil type, rainfall, temperature) is plausible and defensible: real-world yield also depends on
fertilizer amount and timing, irrigation practices, pest pressure, and farming technique — none of
which are in this dataset. MAE of 359 kg/acre against typical yields in the 1,500-3,000 kg/acre
range is roughly 15-20% relative error, appropriate for a decision-support estimate rather than a
precision guarantee.

### New API endpoint (previously did not exist)
`GET /api/v1/crops/{crop_id}/predict-yield` — added to `backend/app/api/yield_prediction.py`.
Automatically gathers:
- Soil type from the farm record
- Latest sensor reading for moisture/pH/nitrogen (gracefully handles no sensor data)
- Current weather (temperature + summed forecast rainfall) via the existing weather service
- Most recent disease detection severity for the farm

Then calls the hybrid predictor and returns the result, including `prediction_method`.

### Files changed / added
- `backend/app/ml/yield_predictor.py` — rewritten as hybrid ML/heuristic predictor
- `backend/app/api/yield_prediction.py` — **new**, the endpoint that didn't exist before
- `backend/app/schemas/yield_prediction.py` — **new**, response schema
- `backend/app/main.py` — needs router registration added (see integration notes)
- `backend/ml/weights/` — 4 new files: `yield_predictor_model.pkl`, `crop_encoder.pkl`,
  `soil_encoder.pkl`, `feature_columns.pkl`
- **Frontend integration (web dashboard + Flutter app) was not yet connected to this endpoint as of
  this document** — see "Remaining Work" below

---

## 3. Field-Level Pest/Disease Spread Risk Model

### What it was
`app/ml/gnn_model.py` was documented and named as a "Graph Neural Network," including in the
project's tech stack summary. In reality, it contained no neural network, no `torch-geometric`
usage (despite being a listed dependency), and no learned/trained parameters at all. It was a
deterministic formula: haversine distance between farms x a same-crop multiplier x a wind-direction
bearing calculation, with hand-chosen weights (0.6, 1.5, etc).

### Why it was not converted into a real GNN
A genuine GNN requires historical, labeled farm-to-farm disease-spread event data to learn from.
No such dataset was available or collectible within project scope. Training a GNN without that data
would produce a model that appears more sophisticated on paper while not actually learning real
spread dynamics — arguably worse than an honest heuristic, since it would misrepresent its own
reliability.

### What was done instead
1. **Renamed and re-documented** as `field_risk_model.py` — a geospatial risk heuristic, with the
   docstring plainly explaining what it is and why it isn't a GNN.
2. **Bug found and fixed during the rename:** in `dashboard.py`, every farm dictionary passed to the
   risk calculation had `"crop": None` hardcoded. Since `None == None` evaluates to `True` in
   Python, the same-crop 1.5x risk multiplier was silently firing for *every* farm pair regardless
   of what was actually planted — the crop-matching logic had never once compared real crop values.
   Fixed by looking up each farm's current active crop from its `CropRecord` before building the
   risk graph.
3. **Cleanup:** `torch-geometric` (never actually imported anywhere in the codebase) flagged for
   removal from `requirements.txt` — reduces install size and memory footprint, relevant given the
   backend runs on Render's free tier (512MB RAM).

### Files changed
- `backend/app/ml/gnn_model.py` → replaced by `backend/app/ml/field_risk_model.py`
- `backend/app/api/dashboard.py` — updated import; fixed crop lookup in `get_pest_spread_risk()`
- `backend/requirements.txt` — `torch-geometric` removed (unused); `scikit-learn` now genuinely
  needed (previously listed but unused, now required by the yield predictor)
- `backend/app/config.py` — `GNN_MODEL_PATH` now unused, safe to remove

---

## Deployment Notes

The backend is deployed on **Render's free tier (512MB RAM, 0.1 CPU, sleeps after 15 min idle)**.
Running PyTorch + `timm` + an EfficientNet-B4 checkpoint alongside the rest of the FastAPI app is a
real risk on this tier — importing `torch` alone commonly uses 150-250MB, before the model or the
rest of the app's memory needs are counted. Two practical options going forward:

1. Accept the risk for demo/viva purposes and document the constraint in the report
2. Offload disease-detection inference specifically to a free Hugging Face Space (16GB RAM on the
   free CPU tier), with the Render backend calling it over HTTP for that one endpoint — everything
   else stays on Render unchanged

This was flagged but not yet implemented as of this document.

---

## Remaining Work

- [ ] Wire the new `/crops/{crop_id}/predict-yield` endpoint into the web dashboard and Flutter app
      (neither currently calls it — confirmed by codebase search, no existing yield-prediction UI
      exists in either frontend)
- [ ] Decide on Render vs Hugging Face Space for disease-detector inference hosting
- [ ] Optional: source additional labeled data for the 5 excluded disease classes (Neck_Blast,
      Sheath_Blight, False_Smut, Downy_Mildew, Anthracnose) if broader class coverage becomes a
      requirement
- [ ] Optional: address the disease detector's real-world generalization gap via field-collected
      data or domain adaptation techniques, if time permits beyond current project scope
