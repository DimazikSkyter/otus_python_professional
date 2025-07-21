from typing import Any, Dict, Optional, Sequence, TypedDict, Union

import numpy as np
import numpy.typing as npt
from pwlf import pwlf
from vf_app.errors.errors import RFCModelNotInit
from xgboost import XGBRegressor


class ModelConfig(TypedDict, total=False):
    pass


class XGBRegressorConfig(TypedDict, total=False):
    random_state: int
    n_estimators: int
    max_depth: int
    learning_rate: float
    subsample: float
    colsample_bytree: float
    reg_lambda: float
    reg_alpha: float
    verbosity: int


class Model:
    def __init__(
        self,
        rfc_config: Optional[XGBRegressorConfig] = None,
        z_score_default: float = 2.5,
        z_score_percentile: Union[int, float] = 95,
    ):
        if not (0 <= z_score_percentile < 100):
            raise ValueError("z_score_percentile must be less then 100.")
        self.rfc_model: Optional[XGBRegressor] = None
        self.z_score_current = z_score_default
        self.rfc_config: XGBRegressorConfig = rfc_config or {}
        self.z_score_percentile: float = float(z_score_percentile)
        self.break_points: Optional[npt.NDArray[np.int64]] = None

    def train_z_score(
        self, X: npt.NDArray[np.float64], y: npt.NDArray[np.int64]
    ) -> float:
        defaults = {
            "random_state": 42,
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.3,
            "subsample": 1.0,
            "colsample_bytree": 0.8,
            "reg_lambda": 1.0,
            "reg_alpha": 0.0,
            "verbosity": 0,
        }
        params: Dict[str, Any] = {**defaults, **self.rfc_config}
        self.rfc_model = XGBRegressor(**params)
        self.rfc_model.fit(X, y)
        return self._calibrate_z_score_(X)

    def calc_break_points(self, X: npt.NDArray[np.float64]) -> None:
        if self.rfc_model is None:
            raise RFCModelNotInit()
        z_scores = self._calc_z_for_seria_(X)
        print("Z min/max:", z_scores.min(), z_scores.max())
        print(
            "Threshold at",
            self.z_score_percentile,
            "percentile =",
            np.percentile(z_scores, self.z_score_percentile),
        )
        indices = np.nonzero(z_scores > self.z_score_current)[0]
        self.break_points = indices.astype(np.int64)

    def predict_single_seria(
        self,
        single_seria_x: npt.NDArray[np.float64],
        single_seria_y: npt.NDArray[np.float64],
    ) -> npt.NDArray[np.float64]:
        if not hasattr(self, "break_points"):
            raise ValueError("Need to init break points before prediction.")
        pwlf_model = pwlf.PiecewiseLinFit(single_seria_x, single_seria_y)
        x_breaks = single_seria_x[self.break_points]
        print("Break indices:", self.break_points)
        print("Break x-values:", single_seria_x[self.break_points])
        pwlf_model.fit_with_breaks(x_breaks.tolist())
        return pwlf_model.predict(single_seria_x)

    def predict_full_seria(
        self, global_seria: Sequence[npt.NDArray[np.float64]]
    ) -> Sequence[npt.NDArray[np.float64]]:
        arr = np.array(global_seria)
        self.calc_break_points(arr)
        results: list[npt.NDArray[np.float64]] = []
        y = arr[-1, :]
        for row in arr[:-1, :]:
            results.append(self.predict_single_seria(row, y))
        return results

    def _calibrate_z_score_(self, seria: npt.NDArray[np.float64]) -> float:
        z = self._calc_z_for_seria_(seria)
        new_threshold = float(np.percentile(z, self.z_score_percentile))
        self.z_score_current = new_threshold
        return new_threshold

    def _calc_z_for_seria_(
        self, seria: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        if self.rfc_model is None:
            raise RFCModelNotInit()
        proba = self.rfc_model.predict(seria)
        dp = np.gradient(proba)
        return (dp - dp.mean()) / dp.std()
