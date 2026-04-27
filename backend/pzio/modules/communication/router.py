from fastapi import APIRouter

# Endpoints in this module: see SAD §4.4 (paths /api/comments/*, /api/attachments/*,
# /api/tasks/{id}/comments, /api/tasks/{id}/attachments).
router = APIRouter(tags=["Communication"])
