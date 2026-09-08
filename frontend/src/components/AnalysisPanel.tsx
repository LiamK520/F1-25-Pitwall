import { useEffect, useState} from "react"

import type { AvailableLapsResponse, StateResponse, LapTelemetryResponse } from "../types/api"

interface AnalysisPanelProps {
    state: StateResponse
}

function AnalysisPanel({state}: AnalysisPanelProps) {
    const [selectedCarIndex, setSelectedCarIndex] = useState<number | null>(null)
    const [availableLaps, setAvailableLaps] = useState<number[]>([])
    const [selectedLap, setSelectedLap] = useState<number | null>(null)
    const [lapTelemetry, setLapTelemetry] = useState<LapTelemetryResponse | null>(null)

    useEffect(() => {
        if (selectedCarIndex == null) {
            // no car reset stuff
            setAvailableLaps([])
            setSelectedLap(null)
            return
        }

        async function loadAvailableLaps() {
            const response = await fetch(
                `/analysis/cars/${selectedCarIndex}/laps`
            )

            if (!response.ok) {
                throw new Error(
                    `error: failed to load laps for car ${selectedCarIndex}: HTTP ${response.status}`
                )
            }

            const data: AvailableLapsResponse = await response.json()

            setAvailableLaps(data.laps)
            setSelectedLap(null)
        }

        loadAvailableLaps()
    }, [selectedCarIndex])

    useEffect(() => {
        if (selectedCarIndex === null || selectedLap === null) {
            setLapTelemetry(null)
            return
        }

        async function loadLapTelemetry() {
            const response = await fetch(`/analysis/cars/${selectedCarIndex}/laps/${selectedLap}`)

            if (!response.ok) {
                throw new Error(
                    `error: could not fetch lap ${selectedLap} for car ${selectedCarIndex}: HTTP ${response.status}`
                )
            }

            const data: LapTelemetryResponse = await response.json()

            setLapTelemetry(data)
        }

        loadLapTelemetry()
    }, [selectedCarIndex, selectedLap])

    return (
        <section className="analysis-panel">
            <h2>Analysis</h2>
            <label>
                Driver

                <select
                    value = {selectedCarIndex ?? ""}
                    onChange={(event) => {
                        const value = event.target.value

                        setSelectedCarIndex(value == "" ? null : Number(value))
                    }}
                >
                    <option value="">Select Driver</option>

                    {state.cars.
                    filter((car) => car.driver_id !== null).map((car) => (
                        <option key={car.index} value={car.index}>
                            {car.driver_id ?? `Car ${car.driver_id}`}
                        </option>
                    ))}
                </select>
            </label>

            <label>
                Lap

                <select
                    value={selectedLap ?? ""}
                    disabled={selectedCarIndex === null}
                    onChange={(event) => {
                        const value = event.target.value

                        setSelectedLap(value === "" ? null : Number(value))
                    }}
                >
                    <option value="">
                        {selectedCarIndex === null
                            ? "Select Driver First"
                            : availableLaps.length === 0
                                ? "No recorded laps"
                                : "Select lap"
                        }
                    </option>

                    {availableLaps.map((lap) => (
                        <option key={lap} value={lap}>
                            Lap {lap}
                        </option>
                    ))}
                </select>
            </label>

            {selectedCarIndex !== null && selectedLap !== null && (
                <p>
                    Selected:{" "}
                    {state.cars[selectedCarIndex]?.name ??
                        `CaR ${selectedCarIndex}`}{" "}
                        - lAP {selectedLap}
                </p>
            )}

            {lapTelemetry && (
                <div>
                    <p>Samples: {lapTelemetry.lap_distance.length}</p>
                    <p>First distance: {" "} {lapTelemetry.lap_distance[0]?.toFixed(1)} m</p>
                    <p>First speed: {" "} {lapTelemetry.speed[0]} km/h</p>
                </div>
            )}
        </section>
    )
}

export default AnalysisPanel