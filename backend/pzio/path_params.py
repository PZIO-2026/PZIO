"""Shared annotated types for numeric path parameters.

PostgreSQL stores primary keys as int4, so an id above this range cannot
exist in the database. Without the upper bound the query layer raises
DataError and the API responds with 500 instead of a validation error.
"""

from typing import Annotated

from fastapi import Path

INT4_MAX = 2_147_483_647

PathId = Annotated[int, Path(ge=1, le=INT4_MAX)]
