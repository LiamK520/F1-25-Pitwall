import { useEffect, useState} from "react"
import type { RefObject } from "react"

import type { LiveCar, LiveFrame, StateResponse } from "../types/api"


interface DriverTelemetryProps {
    state: StateResponse
    carIndex: number
    latestFrameRef: RefObject<LiveFrame | null>
}

// in ms
const REFRESH_RATE = 50

function DriverTelemetry({state, carIndex, latestFrameRef}: DriverTelemetryProps) {
    const [car, setCar] = useState<LiveCar | null>(null)

    useEffect(() => {
        const timer = window.setInterval(() => {
            const frame = latestFrameRef.current

            if (frame !== null) {
                setCar(frame.cars[carIndex])
            }
        }, REFRESH_RATE)
        
        return () => {
            window.clearInterval(timer)
        }
    }, [carIndex, latestFrameRef])

    const participant = state.cars[carIndex]

    if (car === null) {
        return <section>Waiting for telemetry</section>
    }

    return (
        <section>
            <h2>
                {participant?.name ?? `Car ${carIndex}`}
            </h2>

            <p>Speed: {car.speed} km/h</p>
            <p>Gear: {car.gear}</p>
            <p>RPM: {car.rpm}</p>
            <p>Throttle: {(car.throttle * 100).toFixed(0)}%</p>
            <progress value={car.throttle} max={1}/>
            <p>Brake: {(car.brake * 100).toFixed(0)}%</p>
            <progress value={car.brake} max={1}/>
            <p>Steer: {(car.steer * 100).toFixed(0)}%</p>
            <progress value={car.steer + 1} max={2}/>
            <p>DRS: {car.drs ? "OPEN" : "CLOSED"}</p>
            <p>Position: P{car.position}</p>
            <p>Lap: {car.lap}</p>
        </section>
    )
}


export default DriverTelemetry