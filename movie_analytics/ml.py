from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "log_gross"
# Khong dua score va votes vao: hai bien nay chi co sau khi phim ra rap.
NUMERIC_FEATURES = ["log_budget", "runtime", "year", "release_month",
                    "director_track", "star_track", "company_track"]
CATEGORICAL_FEATURES = ["genre", "rating_group", "season", "is_us"]
SPLIT_YEAR = 2015  # Huấn luyện trên quá khứ, kiểm định trên tương lai


@dataclass
class ModelResult:

    name: str
    pipeline: Pipeline
    r2: float
    mae_log: float
    median_error_ratio: float
    y_test: np.ndarray = field(repr=False, default=None)
    y_pred: np.ndarray = field(repr=False, default=None)
    n_train: int = 0
    n_test: int = 0


def _expanding_track_record(df: pd.DataFrame, key: str) -> pd.Series:
    ordered = df.sort_values("release_date")
    track = ordered.groupby(key, observed=True)[TARGET].transform(
        # shift(1) de khong lay chinh bo phim dang du bao
        lambda s: s.expanding().mean().shift(1)
    )
    return track.reindex(df.index)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df[df["has_financials"] & df["release_date"].notna()].copy()
    data = data[data["gross_real"] > 0]

    is_us = data["country"].eq("United States").fillna(False).to_numpy(dtype=bool)
    data["is_us"] = np.where(is_us, "US", "Non-US")
    data["director_track"] = _expanding_track_record(data, "director")
    data["star_track"] = _expanding_track_record(data, "star")
    data["company_track"] = _expanding_track_record(data, "company")

    columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET, "name", "year", "gross_real"]
    return data[list(dict.fromkeys(columns))].dropna(subset=[TARGET, "log_budget"])


def _make_pipeline(estimator) -> Pipeline:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", min_frequency=20)),
        ]
    )
    preprocessor = ColumnTransformer(
        [("num", numeric, NUMERIC_FEATURES), ("cat", categorical, CATEGORICAL_FEATURES)]
    )
    return Pipeline([("prep", preprocessor), ("model", estimator)])


def time_split(features: pd.DataFrame, split_year: int = SPLIT_YEAR):
    train = features[features["year"] < split_year]
    test = features[features["year"] >= split_year]
    x_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    return train[x_cols], train[TARGET], test[x_cols], test[TARGET]


def train_models(features: pd.DataFrame, split_year: int = SPLIT_YEAR) -> list[ModelResult]:
    x_train, y_train, x_test, y_test = time_split(features, split_year)

    candidates = {
        "Ridge (tuyến tính)": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=350, max_depth=16, min_samples_leaf=5, random_state=42, n_jobs=-1
        ),
    }

    results = []
    for name, estimator in candidates.items():
        pipeline = _make_pipeline(estimator).fit(x_train, y_train)
        y_pred = pipeline.predict(x_test)
        results.append(
            ModelResult(
                name=name,
                pipeline=pipeline,
                r2=r2_score(y_test, y_pred),
                mae_log=mean_absolute_error(y_test, y_pred),
                median_error_ratio=float(10 ** np.median(np.abs(y_test - y_pred))),
                y_test=y_test.to_numpy(),
                y_pred=y_pred,
                n_train=len(x_train),
                n_test=len(x_test),
            )
        )
    return results


def feature_importance(result: ModelResult, features: pd.DataFrame,
                       split_year: int = SPLIT_YEAR, top_n: int = 12) -> pd.DataFrame:
    _, _, x_test, y_test = time_split(features, split_year)
    scores = permutation_importance(
        result.pipeline, x_test, y_test, n_repeats=5, random_state=42, n_jobs=-1
    )
    table = pd.DataFrame(
        {"feature": NUMERIC_FEATURES + CATEGORICAL_FEATURES, "importance": scores.importances_mean}
    )
    return table.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)


def predict_single(result: ModelResult, payload: dict) -> dict:
    frame = pd.DataFrame([payload])
    log_pred = float(result.pipeline.predict(frame)[0])
    gross = 10 ** log_pred
    budget = 10 ** float(payload["log_budget"])
    return {
        "log_gross": log_pred,
        "gross_real": gross,
        "multiple": gross / budget if budget else np.nan,
        "band_low": gross / result.median_error_ratio,
        "band_high": gross * result.median_error_ratio,
    }
