from dataclasses import asdict, fields

from vf_app.api.endpoints import AppConfigDto
from vf_app.core.services import Config

dct = {
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


def test_convert_appconfig_to_config():
    app_config: AppConfigDto = AppConfigDto(fields=dct)
    config = app_config.to_config()
    config_dict = asdict(config)

    normalized_dct = {key: type(config_dict[key])(value) for key, value in dct.items()}

    assert config_dict == normalized_dct


def test_convert_config_to_appconfig():
    config = Config(1, 2, 3, 4.0, 5.0, 6.0, 7.0, 8.0, 9, 10.0, 11)
    app_config: AppConfigDto = AppConfigDto.to_dto(config)
    assert app_config.fields == dct


def test_dto_roundtrip():
    dto = AppConfigDto(fields=dct)
    config = dto.to_config()
    dto2 = AppConfigDto.to_dto(config)
    assert dto2.fields == dct
