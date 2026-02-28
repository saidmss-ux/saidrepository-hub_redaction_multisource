SUPPORTED_API_VERSIONS: tuple[str, ...] = ("v1",)
NEXT_API_VERSION: str = "v2"


def version_prefix(version: str) -> str:
    if version not in SUPPORTED_API_VERSIONS:
        raise ValueError(f"Unsupported API version: {version}")
    return f"/api/{version}"
