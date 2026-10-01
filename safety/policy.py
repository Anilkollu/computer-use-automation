from urllib.parse import urlparse


ALLOWED_ORIGINS = {
    "http://127.0.0.1:3000",
}

ALLOWED_ROUTES = {
    "/login.html",
    "/dashboard.html",
    "/payment.html",
}

ALLOWED_ACTIONS = {
    "click",
    "fill",
    "finish",
}


class SafetyError(Exception):
    pass


def validate_url(url: str):
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    if origin not in ALLOWED_ORIGINS:
        raise SafetyError(
            f"Blocked URL: origin is not allowlisted: {origin}"
        )

    if parsed.path not in ALLOWED_ROUTES:
        raise SafetyError(
            f"Blocked URL: route is not allowlisted: {parsed.path}"
        )


def validate_action(action: dict):
    action_type = action.get("action")

    if action_type not in ALLOWED_ACTIONS:
        raise SafetyError(
            f"Blocked action: {action_type}"
        )


def validate_page(page):
    validate_url(page.url)