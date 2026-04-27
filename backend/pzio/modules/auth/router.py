from fastapi import APIRouter

# Endpoints in this module: see SAD §4.1 (paths /api/auth/* and /api/users/*).
# Each route should declare its full path on the decorator — no router-level prefix
# is set because the auth module owns multiple URL roots.
router = APIRouter(tags=["Auth"])
