from typing import Dict

from vf_app.core.services import Config, ConfigService, ModelService

default: Dict[str, int | float] = {
    "random_state": 1,
    "n_estimators": 2,
    "max_depth": 3,
    "learning_rate": 4.0,
    "subsample": 5.0,
    "colsample_bytree": 6.0,
    "reg_lambda": 7.0,
    "reg_alpha": 8.0,
    "verbosity": 9,
    "z_score_default": 10.0,
    "z_score_percentile": 11,
}

config: Config = Config(**default)  # type: ignore[arg-type]
config_service: ConfigService = ConfigService(config)
model_service: ModelService = ModelService(config_service)
