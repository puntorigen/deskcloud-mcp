import os

import uvicorn


def main() -> None:
    """Entry point for `deskcloud-mcp`.

    Starts the FastAPI server. Configure with environment variables:

    - HOST (default: 0.0.0.0)
    - PORT (default: 8000)
    """

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
    )
