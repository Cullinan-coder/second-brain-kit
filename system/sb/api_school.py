"""Faz 3a Paket K: okul uçları (ders panosu, GANO, çalışma planı, program, hoca, başvuru, belgeler)."""
from __future__ import annotations

from datetime import date

from . import academic
from .webroutes import ApiError, Ctx, route


def _need_code(ctx: Ctx) -> str:
    code = str(ctx.arg("code", "") or "").strip()
    if not code:
        raise ApiError(400, "code gerekli")
    return code


@route("GET", "/api/v2/courses")
def _courses(ctx: Ctx) -> list:
    return academic.courses()


@route("GET", "/api/v2/course")
def _course(ctx: Ctx) -> dict:
    code = _need_code(ctx)
    d = academic.course_detail(code)
    if d is None:
        raise ApiError(404, f"ders bulunamadı: {code}")
    return d


@route("GET", "/api/v2/gpa")
def _gpa(ctx: Ctx) -> dict:
    g = academic.load_grades()
    out = academic.compute_gpa(g["entries"])
    out["source"] = g["source"]
    return out


@route("POST", "/api/v2/gpa/what-if")
def _what_if(ctx: Ctx) -> dict:
    changes = ctx.data.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ApiError(400, "changes: [{code, grade}] gerekli")
    g = academic.load_grades()
    try:
        new = academic.compute_gpa(g["entries"], changes)
    except (ValueError, TypeError, AttributeError) as e:
        raise ApiError(400, str(e))
    base = academic.compute_gpa(g["entries"])
    delta = round(new["gpa"] - base["gpa"], 2) if new["gpa"] is not None and base["gpa"] is not None else None
    return {"gpa": new["gpa"], "credits": new["credits"], "current": base["gpa"], "delta": delta}


@route("POST", "/api/v2/study-plan")
def _study_plan(ctx: Ctx) -> dict:
    code = _need_code(ctx)
    try:
        exam = date.fromisoformat(str(ctx.data.get("exam_date") or ""))
        hours = float(ctx.data.get("hours_per_day") or 2)
    except ValueError:
        raise ApiError(400, "exam_date (YYYY-AA-GG) ve hours_per_day (sayı) gerekli")
    if not 0 < hours <= 16:
        raise ApiError(400, "hours_per_day 0-16 arası olmalı")
    try:
        return academic.write_study_plan(code, exam, hours)
    except KeyError:
        raise ApiError(404, f"ders bulunamadı: {code}")
    except ValueError as e:
        raise ApiError(400, str(e))


@route("GET", "/api/v2/schedule")
def _schedule(ctx: Ctx) -> dict:
    return academic.schedule()


@route("GET", "/api/v2/course/instructor")
def _instructor(ctx: Ctx) -> dict:
    r = academic.instructor_contact(_need_code(ctx))
    if r is None:
        raise ApiError(404, "ders bulunamadı")
    return r


@route("GET", "/api/v2/applications")
def _applications(ctx: Ctx) -> list:
    return academic.applications()


@route("GET", "/api/v2/school-docs")
def _school_docs(ctx: Ctx) -> list:
    return academic.school_docs()
