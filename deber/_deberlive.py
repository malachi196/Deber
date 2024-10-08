from fastapi import FastAPI
import uvicorn
import asyncio
from multiprocessing import Process
import signal
from typing import NoReturn, Literal

app = FastAPI()

@app.get("/")
async def _index():
    return "deber[DEBUG] is online"

class InvalidThread(Exception):
    """The thread provided does not exist"""


def __run():
    try:
        uvicorn.run(host="localhost", app=app, port=8080)
    except KeyboardInterrupt:
        pass


def keep_alive() -> FastAPI:
    """keeps the server alive by creating a webserver that is active even if the processor is offline"""
    webserver = Process(target=__run)
    try:
        webserver.start()
    except KeyboardInterrupt:
        webserver.terminate()