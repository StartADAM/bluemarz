from typing import TypeVar

import pydantic
import httpx

from pydantic.alias_generators import to_camel


class CamelCaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


__M = TypeVar("__M", bound=pydantic.BaseModel)


def desserialize_response(response: httpx.Response, cls: type[__M]) -> __M:
    return cls.model_validate(response.json())


def to_json(cls: pydantic.BaseModel) -> str:
    return cls.model_dump_json(exclude_none=True, by_alias=True)


def to_dict(cls: pydantic.BaseModel) -> str:
    return cls.model_dump(exclude_none=True, by_alias=True)
