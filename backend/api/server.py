from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from udp.receiver import run_receiver
from state.application_state import ApplicationState
from api.schemas import StateResponse
from api.serialiser import serialise_live_frame, serialise_state

import asyncio

state = ApplicationState()

stop_event = threading.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event.clear()
    
    receive_thread = threading.Thread(target=run_receiver, args=(state, stop_event), daemon=True)

    receive_thread.start()

    yield

    stop_event.set()
    receive_thread.join(timeout=1.0)

app = FastAPI(title="F1 25 Pit Wall", lifespan=lifespan)

# basic health for server testing
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/state", response_model=StateResponse)
def get_state():
    return serialise_state(state)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    last_sent: tuple[int, int] | None = None

    try:
        while True:
            live_frame = state.latest_live_frame

            if live_frame is not None:
                # use both session uid and frame in key just in case session changes or something
                key = (state.session_uid, live_frame.overall_frame_identifier)

                if key != last_sent:
                    response = serialise_live_frame(live_frame)

                    await websocket.send_json(response.model_dump())

                    last_sent = key

            # send at approx 20hz
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass