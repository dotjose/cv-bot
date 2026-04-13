from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.services import profile_store

router = APIRouter(tags=["profile"])


@router.get("/profile/overview")
async def profile_overview():
    try:
        p = await profile_store.load_dynamic_profile(get_settings())
        return profile_store.normalize_overview(p.get("overview"))
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to load profile"})


@router.get("/profile/skills")
async def profile_skills():
    try:
        p = await profile_store.load_dynamic_profile(get_settings())
        return {"skills": p["skills"]}
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to load profile"})


@router.get("/profile/projects")
async def profile_projects():
    try:
        p = await profile_store.load_dynamic_profile(get_settings())
        return {"projects": profile_store.normalize_projects_list(p.get("projects"))}
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to load profile"})


@router.get("/profile/experience")
async def profile_experience():
    try:
        p = await profile_store.load_dynamic_profile(get_settings())
        return {"experience": p["experience"]}
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to load profile"})


@router.get("/profile/education")
async def profile_education():
    try:
        p = await profile_store.load_dynamic_profile(get_settings())
        return {"education": p["education"]}
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Failed to load profile"})


@router.get("/profile/contact")
async def profile_contact():
    """Static contact — same fields as frontend STATIC_PROFILE / ContactCard."""
    return profile_store.static_contact()


@router.get("/profile/availability")
async def profile_availability():
    """Static availability — additive endpoint."""
    return profile_store.static_availability()
