"""Checks expand-and-contract migration safety."""

FORBIDDEN_IN_DEPLOY = ("DROP TABLE", "DROP COLUMN", "RENAME COLUMN")
