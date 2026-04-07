"""Web admin panel: /admin/* routes with Jinja2 templates and cookie auth."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import settings
from db import repo

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

# ─── auth helpers ────────────────────────────────────────────────────────────

_COOKIE = "admin_tok"


def _expected_token() -> str:
    return hashlib.sha256(f"{settings.ADMIN_PASSWORD}:caliadmin".encode()).hexdigest()


def _is_authed(request: Request) -> bool:
    if not settings.ADMIN_PASSWORD:
        return False
    return request.cookies.get(_COOKIE) == _expected_token()


def require_auth(request: Request) -> None:
    if not _is_authed(request):
        # Raise is not practical here; callers redirect manually
        pass


AdminAuth = Annotated[None, Depends(require_auth)]


def _redirect_if_unauthed(request: Request) -> RedirectResponse | None:
    if not _is_authed(request):
        return RedirectResponse("/admin/login", status_code=302)
    return None


# ─── login / logout ──────────────────────────────────────────────────────────


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if _is_authed(request):
        return RedirectResponse("/admin/", status_code=302)
    return templates.TemplateResponse(request, "admin/login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, password: Annotated[str, Form()]) -> HTMLResponse:
    if not settings.ADMIN_PASSWORD:
        return templates.TemplateResponse(
            request, "admin/login.html", {"error": "ADMIN_PASSWORD не задан в .env"}
        )
    if password == settings.ADMIN_PASSWORD:
        resp = RedirectResponse("/admin/", status_code=302)
        resp.set_cookie(_COOKIE, _expected_token(), httponly=True, samesite="lax")
        return resp
    return templates.TemplateResponse(
        request, "admin/login.html", {"error": "Неверный пароль"}
    )


@router.get("/logout")
async def logout() -> RedirectResponse:
    resp = RedirectResponse("/admin/login", status_code=302)
    resp.delete_cookie(_COOKIE)
    return resp


# ─── dashboard ───────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    stats = await repo.get_stats(settings.DB_PATH)
    expiring = await repo.get_expiring_subscriptions(settings.DB_PATH, days=3)
    return templates.TemplateResponse(
        request, "admin/dashboard.html", {"stats": stats, "expiring": expiring, "active": "dashboard"}
    )


# ─── users ───────────────────────────────────────────────────────────────────


@router.get("/users", response_class=HTMLResponse)
async def users_list(request: Request, q: str = "") -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    if q:
        user = await repo.find_user(settings.DB_PATH, q)
        users = [user] if user else []
    else:
        users = await _get_all_users()
    return templates.TemplateResponse(
        request, "admin/users.html", {"users": users, "q": q, "active": "users"}
    )


async def _get_all_users() -> list[dict]:
    import aiosqlite
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY last_seen DESC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ─── subscriptions ───────────────────────────────────────────────────────────


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_list(request: Request, status: str = "") -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    subs = await _get_subscriptions_filtered(status)
    return templates.TemplateResponse(
        request,
        "admin/subscriptions.html",
        {"subs": subs, "status_filter": status, "active": "subscriptions"},
    )


async def _get_subscriptions_filtered(status: str) -> list[dict]:
    import aiosqlite
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            async with db.execute(
                """
                SELECT s.*, u.username, u.first_name, p.name AS product_name
                FROM subscriptions s
                LEFT JOIN users u USING (telegram_id)
                LEFT JOIN products p USING (product_id)
                WHERE s.status = ?
                ORDER BY s.updated_at DESC
                """,
                (status,),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                """
                SELECT s.*, u.username, u.first_name, p.name AS product_name
                FROM subscriptions s
                LEFT JOIN users u USING (telegram_id)
                LEFT JOIN products p USING (product_id)
                ORDER BY s.updated_at DESC
                """
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


@router.post("/subscriptions/{sub_id}/status", response_class=HTMLResponse)
async def subscription_set_status(
    request: Request,
    sub_id: int,
    new_status: Annotated[str, Form()],
) -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    import aiosqlite
    from datetime import datetime
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, datetime.utcnow().isoformat(), sub_id),
        )
        await db.commit()
    return RedirectResponse("/admin/subscriptions", status_code=302)


# ─── products ────────────────────────────────────────────────────────────────


@router.get("/products", response_class=HTMLResponse)
async def products_list(request: Request, msg: str = "") -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    products = await repo.get_all_products(settings.DB_PATH)
    return templates.TemplateResponse(
        request, "admin/products.html", {"products": products, "msg": msg, "active": "products"}
    )


@router.post("/products", response_class=HTMLResponse)
async def product_create(
    request: Request,
    product_id: Annotated[str, Form()],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    channel_id: Annotated[int, Form()],
    discussion_id: Annotated[int, Form()],
    prodamus_url: Annotated[str, Form()],
    price: Annotated[int, Form()],
    subscription_id: Annotated[int, Form()],
) -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    try:
        await repo.create_product(
            settings.DB_PATH,
            {
                "product_id": product_id,
                "name": name,
                "description": description,
                "channel_id": channel_id,
                "discussion_id": discussion_id,
                "prodamus_url": prodamus_url,
                "price": price,
                "subscription_id": subscription_id,
            },
        )
        return RedirectResponse("/admin/products?msg=created", status_code=302)
    except Exception as e:
        products = await repo.get_all_products(settings.DB_PATH)
        return templates.TemplateResponse(
            request, "admin/products.html", {"products": products, "msg": "", "error": str(e), "active": "products"}
        )


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def product_edit_form(request: Request, product_id: str) -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        return RedirectResponse("/admin/products", status_code=302)
    return templates.TemplateResponse(
        request, "admin/product_edit.html", {"product": product, "error": None, "active": "products"}
    )


@router.post("/products/{product_id}/edit", response_class=HTMLResponse)
async def product_edit_submit(
    request: Request,
    product_id: str,
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    channel_id: Annotated[int, Form()],
    discussion_id: Annotated[int, Form()],
    prodamus_url: Annotated[str, Form()],
    price: Annotated[int, Form()],
    subscription_id: Annotated[int, Form()],
) -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    try:
        await repo.update_product(
            settings.DB_PATH,
            product_id,
            {
                "name": name,
                "description": description,
                "channel_id": channel_id,
                "discussion_id": discussion_id,
                "prodamus_url": prodamus_url,
                "price": price,
                "subscription_id": subscription_id,
            },
        )
        return RedirectResponse("/admin/products?msg=updated", status_code=302)
    except Exception as e:
        product = await repo.get_product(product_id, settings.DB_PATH) or {}
        return templates.TemplateResponse(
            request, "admin/product_edit.html", {"product": product, "error": str(e), "active": "products"}
        )


@router.post("/products/{product_id}/delete", response_class=HTMLResponse)
async def product_delete(request: Request, product_id: str) -> HTMLResponse:
    if redir := _redirect_if_unauthed(request):
        return redir
    await repo.delete_product(settings.DB_PATH, product_id)
    return RedirectResponse("/admin/products?msg=deleted", status_code=302)
