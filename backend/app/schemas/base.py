from pydantic import BaseModel, ConfigDict


class BaseRequestSchema(BaseModel):
    """Base for request payloads that rejects undeclared fields."""

    model_config = ConfigDict(extra="forbid")
