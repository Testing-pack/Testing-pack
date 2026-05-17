import asyncio
import sys

if sys.platform == "win32":
    from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import uvicorn
from split_integration.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)