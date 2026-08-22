from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI

from udp.receiver import run_receiver
from state.application_state import ApplicationState

state = ApplicationState()

stop_event = threading.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
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

@app.get("/state")
def get_state():
    car = state.player_car

    return {
        "session_uid": state.session_uid,
        "num_active_cars": state.num_active_cars,
        "player_car_index": state.player_car_index,

        "player": {
            "lap": car.lap.current_lap_num
                if car is not None and car.lap is not None
                else None,

            "lap_distance": car.lap.lap_distance
                if car is not None and car.lap is not None
                else None,

            "speed": car.telemetry.speed
                if car is not None and car.telemetry is not None
                else None,

            "gear": car.telemetry.gear
                if car is not None and car.telemetry is not None
                else None,

            "rpm": car.telemetry.engine_rpm
                if car is not None and car.telemetry is not None
                else None,
        }
    }