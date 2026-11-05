from sqlalchemy import Integer
from sqlalchemy.dialects.mysql import BIGINT


BIGINT_UNSIGNED = BIGINT(unsigned=True).with_variant(Integer(), "sqlite")
