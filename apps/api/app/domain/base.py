"""Python uses snake_case; the public JSON contract always uses camelCase."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Score = Annotated[float, Field(ge=0, le=100)]
Confidence = Annotated[float, Field(ge=0, le=1)]
Milliseconds = Annotated[int, Field(ge=0)]


class ContractModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        allow_inf_nan=False,
    )
