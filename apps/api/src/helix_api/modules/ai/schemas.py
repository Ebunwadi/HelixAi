from pydantic import BaseModel, ConfigDict, Field


class InvestigationInterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class InvestigationIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: str | None = None
    issue_type: str
    time_reference: str | None = None
    requested_actions: list[str]
    summary: str


class ModelMetadata(BaseModel):
    model: str
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int


class InvestigationInterpretResponse(BaseModel):
    intent: InvestigationIntent
    model: ModelMetadata
