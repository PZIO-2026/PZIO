from fastapi import APIRouter

# Endpoints in this module: see SAD §4.3 (paths /api/tasks/* and /api/projects/{id}/tasks).
router = APIRouter(tags=["Tasks"])
