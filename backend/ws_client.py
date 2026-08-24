import asyncio
import json

import websockets


async def main():
    uri = "ws://127.0.0.1:8000/ws"

    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()

            data = json.loads(message)

            # no data validation or anything just simple test
            # will probably delete this file later

            print(
                f"frame={data['overall_frame']} "
                f"time={data['session_time']:.2f} "
                f"cars={len(data['cars'])}"
            )

            if data["cars"]:
                car = data["cars"][0]

                print(
                    f"  car 0 | "
                    f"P{car['position']} | "
                    f"lap {car['lap']} | "
                    f"{car['speed']} km/h | "
                    f"gap {car['delta_to_car_in_front_ms']} ms"
                )


asyncio.run(main())