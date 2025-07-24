from dataclasses import asdict, fields
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from vf_app.core.services import Config, TimeSeria
from vf_app.dependencies import config_service, model_service

app = FastAPI()
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "resource" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class AppConfigDto(BaseModel):
    fields: Dict[str, Any]

    def to_config(self) -> Config:
        return Config(
            **{
                field.name: self.fields.get(field.name)
                for field in fields(Config)  # type: ignore[arg-type]
            }
        )

    @staticmethod
    def to_dto(config: Config) -> "AppConfigDto":
        return AppConfigDto(fields=asdict(config))


class TimeSeriaDto(BaseModel):
    start: datetime
    step: timedelta
    size: int
    seria: List[float]
    break_points: Optional[List[int]] = None

    def to_time_seria(self):
        return TimeSeria(self.start, self.step, self.size, self.seria)


def get_config_service():
    return config_service


def get_model_service():
    return model_service


@app.get("/", response_class=HTMLResponse)
async def info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


@app.get("/model/configuration")
async def get_configuration(cs=Depends(get_config_service)):
    return AppConfigDto.to_dto(cs.get_config())


@app.put("/model/configuration")
async def upload_model_configuration(
    app_config: AppConfigDto,
    cs=Depends(get_config_service),
    ms=Depends(get_model_service),
):
    cs.update_config(app_config.to_config())
    ms.reload_model()
    return {"status": "ok"}


@app.post("/metrics/callibrate_model")
async def calibrate_model(time_seria_dto: TimeSeriaDto, ms=Depends(get_model_service)):
    ms.calibrate_model(time_seria_dto.to_time_seria(), time_seria_dto.break_points)
    return {"status": "ok"}


@app.post("/metrics/break_points")
async def seek_break_points(
    time_seria_dto: TimeSeriaDto, ms=Depends(get_model_service)
):
    breakpoints = ms.get_break_points(time_seria_dto.to_time_seria())
    return {"break_points": breakpoints.tolist()}


@app.post("/metrics/predict/plr")
async def predict_piecewise_linear_regress(
    time_seria_dto: TimeSeriaDto, ms=Depends(get_model_service)
):
    prediction = ms.predict_single_seria(time_seria_dto.to_time_seria())
    return {"y_hat": prediction.tolist()}
