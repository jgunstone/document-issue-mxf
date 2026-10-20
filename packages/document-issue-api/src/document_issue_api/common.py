"""Shared HTTP boundary rules; domain validation remains in document-issue."""

from copy import deepcopy
from typing import get_args

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, ValidationError, WrapValidator, create_model, field_validator


def require(db, model, identity):
    row = db.get(model, identity)
    if row is None:
        raise HTTPException(404, f"{model.__name__} {identity} not found")
    return row


class PartialModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_nonnullable_null(cls, value, info):
        annotation = cls.model_fields[info.field_name].annotation
        if value is None and type(None) not in get_args(annotation):
            raise ValueError("This field cannot be null")
        return value


def partial_model(name, model, **overrides):
    """Publish field contracts, but defer scalar validation until the full merge.

    A None default is an internal omission sentinel, not a nullable annotation.
    This preserves input normalization implemented as domain field-validator methods
    (such as legacy issue-format codes), without validating an incomplete model.
    Nested partial models still parse normally so their supplied fields are tracked.
    """
    fields = {}
    for key, source in model.model_fields.items():
        field = deepcopy(source)
        field.default = None
        field.default_factory = None
        field.validate_default = False
        annotation = overrides.get(key, field.annotation)
        field.annotation = annotation
        if key not in overrides:
            field.metadata.append(WrapValidator(lambda value, handler: value))
        fields[key] = (annotation, field)
    return create_model(name, __base__=PartialModel, **fields)


def merge_patch(current, supplied):
    result = dict(current)
    for key, value in supplied.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_patch(result[key], value)
        else:
            result[key] = value
    return result


def validate_patch(model, current, patch):
    try:
        return model.model_validate(
            merge_patch(current, patch.model_dump(exclude_unset=True, by_alias=False, warnings=False)),
        )
    except ValidationError as exc:
        errors = [
            {**error, "loc": ("body", *error["loc"])}
            for error in exc.errors(include_context=False)
        ]
        raise RequestValidationError(errors) from exc
