import type {StateResponse, LiveFrame } from "../types/api"


interface InfoBarProps {
    state: StateResponse | null
    frame: LiveFrame | null
}

function InfoBar({state, frame}: InfoBarProps) {
    const leader = frame?.cars.find((car) => car.position === 1)

    const currentLap = leader?.lap ?? null
    return (
        <header className="info-bar">
            <p>
                Track: {state?.track_name ?? "-"}
            </p>

            <p>
                {state?.session_name ?? "-"}
            </p>

            <p>
                Lap: {currentLap ?? "-"}/{state?.total_laps ?? "-"}
            </p>

            <p>
                Weather: {state?.weather_name ?? "-"}
            </p>

            <p>
                Track: {state?.track_temperature ?? "-"}°C
            </p>

            <p>
                Air: {state?.air_temperature ?? "-"}°C
            </p>

            <p>
                SC: {state?.safety_car_status_name ?? "-"}
            </p>
        </header>
    )
}


export default InfoBar