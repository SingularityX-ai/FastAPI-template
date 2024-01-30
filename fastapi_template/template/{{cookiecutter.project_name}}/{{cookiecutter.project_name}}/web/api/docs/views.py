from fastapi import APIRouter, Request
from fastapi.openapi.docs import (get_redoc_html, get_swagger_ui_html,
                                  get_swagger_ui_oauth2_redirect_html)
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/docs", include_in_schema=False)
async def swagger_ui_html(request: Request) -> HTMLResponse:
    """
    Render Swagger UI.

    Args:
        request (Request): Current request.

    Returns:
        HTMLResponse: Rendered Swagger UI.

    Raises:
        None

    """
    title = request.app.title
    return get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=f"{title} - Swagger UI",
        oauth2_redirect_url=str(request.url_for("swagger_ui_redirect")),
        swagger_js_url="/static/docs/swagger-ui-bundle.js",
        swagger_css_url="/static/docs/swagger-ui.css",
    )


@router.get("/swagger-redirect", include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    """
    Redirect to swagger.

    :return: HTMLResponse: Redirect to swagger.
    """
    return get_swagger_ui_oauth2_redirect_html()


@router.get("/redoc", include_in_schema=False)
async def redoc_html(request: Request) -> HTMLResponse:
    """
    Render the Redoc UI.

    :param request: The current request.
    :type request: Request
    :return: The rendered Redoc UI.
    :rtype: HTMLResponse
    :raises: None
    """
    title = request.app.title
    return get_redoc_html(
        openapi_url=request.app.openapi_url,
        title=f"{title} - ReDoc",
        redoc_js_url="/static/docs/redoc.standalone.js",
    )
