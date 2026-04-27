from fastapi import APIRouter

# Endpoints in this module: see SAD §4.5 (paths /api/admin/*, /api/task-types,
# /api/tasks/{id}/history).
router = APIRouter(tags=["Admin"])
