from dataclasses import dataclass, fields, replace
from datetime import datetime, timedelta
from typing import List, Union

import numpy as np
import numpy.typing as npt
from vf_app.model.model import Model, XGBRegressorConfig


@dataclass
class TimeSeria:
    start: datetime
    step: timedelta
    size: int
    seria: List[float]


@dataclass
class Config:
    random_state: int
    n_estimators: int
    max_depth: int
    learning_rate: float
    subsample: float
    colsample_bytree: float
    reg_lambda: float
    reg_alpha: float
    verbosity: int
    z_score_default: float
    z_score_percentile: Union[int, float]

    def get_XGBRegressorConfig(self) -> XGBRegressorConfig:
        return {
            "random_state": self.random_state,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "reg_lambda": self.reg_lambda,
            "reg_alpha": self.reg_alpha,
            "verbosity": self.verbosity,
        }

    def merge_in_new(self, another_config: "Config"):
        update_values = {}
        for field in fields(self):
            value = getattr(another_config, field.name)
            if value is not None:
                update_values[field.name] = value
        return replace(self, **update_values)


class ConfigService:
    def __init__(self, config: Config):
        self.config: Config = config

    def get_config(self) -> Config:
        return self.config

    def update_config(self, new_config: Config):
        self.config = new_config.merge_in_new(new_config)


class ModelService:
    is_model_calibrate: bool = False

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.reload_model()

    def reload_model(self):
        config = self.config_service.get_config()
        self.model = Model(
            config.get_XGBRegressorConfig(),
            config.z_score_default,
            config.z_score_percentile,
        )
        self.is_model_calibrated = False

    def calibrate_model(self, time_seria: TimeSeria, break_points: List[int]):
        break_points_seria = np.arange(0, time_seria.size)
        break_points_seria[break_points] = 1
        self.model.train_z_score(np.array((time_seria.seria,)), break_points_seria)
        self.is_model_calibrated = True

    def get_break_points(self, time_seria: TimeSeria) -> npt.NDArray[np.int64]:
        self.model.calc_break_points(np.array(time_seria.seria))
        return self.model.break_points

    def predict_single_seria(
        self, seria_x: TimeSeria, seria_y: TimeSeria
    ) -> npt.NDArray[np.float64]:
        self._validate(seria_x, seria_y)
        return self.model.predict_single_seria(seria_x.seria, seria_y.seria)

    def _validate(self, seria_x, seria_y):
        pass
