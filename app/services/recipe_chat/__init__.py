"""Recipe conversation on top of recipe_session (EPIS snapshot recipes).

Text answers are the default.  Every quantity shown is either the recipe
source text or an exact Decimal calculation in Python; cup-based amounts are
never converted because the source does not define its cup.
"""
