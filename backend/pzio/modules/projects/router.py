from fastapi import APIRouter

# Endpoints in this module: see SAD §4.2 (paths /api/projects/* and /api/sprints/*).
router = APIRouter(tags=["Projects"])
