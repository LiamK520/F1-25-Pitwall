import type { StateResponse, LiveFrame } from "../types/api";

interface TimingTowerProps {
    state: StateResponse
    frame: LiveFrame

    onSelectCar: (index: number) => void
}

function formatGap(ms: number): string {
    // just in case
    if (ms <= 0) {
        return "-"
    }

    return `+${(ms / 1000).toFixed(3)}`
}

function formatLapTime(ms: number): string {
    // if no lap set return dash for now
    if (ms <= 0) {
        return "-"
    }

    const min = Math.trunc(ms / 60000)
    const secs = ((ms % 60000) / 1000).toFixed(3).padStart(6, "0")
    return `${min}:${secs}`
}

function TimingTower({state, frame, onSelectCar}: TimingTowerProps) {
    // get copy of active cars sorted by their position
    // filters out invalid and inactive cars (0 and 1)
    const rows = frame.cars.filter(
        (car) => car.result_status !== 0 && car.result_status !== 1
    ).sort((a, b) => a.position - b.position)

    return (
        <section>
            <h2>Timing</h2>
            <table>
                <thead>
                    <tr>
                        <th>POS</th>
                        <th>DRIVER</th>
                        <th>GAP</th>
                        <th>INTERVAL</th>
                        <th>LAP</th>
                        <th>LAST</th>
                        <th>SPEED</th>
                    </tr>
                </thead>

                <tbody>
                    {rows.map((car) => {
                        const participant = state.cars[car.index]

                        // note for last lap, manually overridng lap 1 (and earlier) as it seems that udp from game can contain data there even tho no lap
                        return (
                            <tr key={car.index} onClick = {() => onSelectCar(car.index)}>
                                <td>{car.position}</td>
                                <td>{participant?.name ?? `Car ${car.index}`}</td>
                                <td>{car.position === 1 ? "LEADER" : formatGap(car.delta_to_race_leader_ms)}</td>
                                <td>{car.position === 1 ? "-" : formatGap(car.delta_to_car_in_front_ms)}</td>
                                <td>{car.lap}</td>
                                <td>{car.lap <= 1 ? "-" : formatLapTime(car.last_lap_time_ms)}</td>
                                <td>{car.speed}</td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </section>
    )
}




export default TimingTower