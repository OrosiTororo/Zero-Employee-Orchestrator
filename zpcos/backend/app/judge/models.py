"""Judge パイプラインの Pydantic モデル定義。"""

from pydantic import BaseModel, Field


class Segment(BaseModel):
    id: str
    text: str
    category: str = Field(description="claim | number | name | logic")


class SampleResult(BaseModel):
    segment_id: str
    model_name: str
    response: str
    agrees: bool


class EvalResult(BaseModel):
    segment_id: str
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


class JudgeResult(BaseModel):
    segments: list[Segment]
    samples: list[SampleResult]
    eval_results: list[EvalResult]
    improved_output: str
    overall_score: float = Field(ge=0.0, le=1.0)
