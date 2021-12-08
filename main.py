import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host=os.environ.get('BACKEND_HOST', '0.0.0.0'),
        port=int(os.environ.get('BACKEND_PORT', '8000')),
        log_level="info"
    )
