import { useEffect, useState, useRef } from "react"

import type { AvailableLapsResponse, StateResponse, LapTelemetryResponse } from "../types/api"

import TelemetryGraph, {type TelemetryMetric} from "./TelemetryGraph"

interface AnalysisPanelProps {
    state: StateResponse
}

interface AnalysisGraphConfig {
    id: number
    metric: TelemetryMetric
}

function AnalysisPanel({state}: AnalysisPanelProps) {
    const [selectedCarIndex, setSelectedCarIndex] = useState<number | null>(null)
    const [availableLaps, setAvailableLaps] = useState<number[]>([])
    const [selectedLap, setSelectedLap] = useState<number | null>(null)
    const [lapTelemetry, setLapTelemetry] = useState<LapTelemetryResponse | null>(null)
    
    const nextGraphId = useRef(2)
    const [graphs, setGraphs] = useState<AnalysisGraphConfig[]>([{
        id: 1,
        metric: "speed"
    }])

    function addGraph() {
        const id = nextGraphId.current
        nextGraphId.current += 1

        setGraphs((current) => [
            ...current,
            {
                id,
                metric: "speed"
            }
        ])
    }

    function removeGraph(id: number) {
        setGraphs((current) =>
            current.filter((graph) => graph.id !== id)
        )
    }

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

                        // reset here to avoid calling the old laps with new driver
                        setAvailableLaps([])
                        setSelectedLap(null)
                        setLapTelemetry(null)
                    }}
                >
                    <option value="">Select Driver</option>

                    {state.cars.
                    filter((car) => car.name !== null && car.name.trim() !== "").map((car) => (
                        <option key={car.index} value={car.index}>
                            {car.name ?? `Car ${car.driver_id}`}
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

            {lapTelemetry !==null && selectedCarIndex !== null && selectedLap !== null && (
                <>
                {graphs.map((graph) => (
                    <div key={graph.id}>
                        <label>
                            Graph

                            <select
                                value={graph.metric}
                                onChange={(event) => {
                                    const metric = event.target.value as TelemetryMetric

                                    setGraphs((current) =>
                                        current.map((item) =>
                                            item.id === graph.id
                                                ? { ...item, metric }
                                                : item
                                        )
                                    )
                                }}
                            >
                                <option value="speed">Speed</option>
                                <option value="throttle">Throttle</option>
                                <option value="brake">Brake</option>
                                <option value="steer">Steering</option>
                                <option value="gear">Gear</option>
                                <option value="rpm">RPM</option>
                            </select>
                        </label>

                        <TelemetryGraph
                            metric={graph.metric}
                            traces={[
                                {
                                    label:
                                        `${state.cars[selectedCarIndex]?.name ?? `Car ${selectedCarIndex}`} ` +
                                        `Lap ${selectedLap}`,
                                    telemetry: lapTelemetry,
                                },
                            ]}
                        />
                        <button onClick={() => removeGraph(graph.id)}>
                            Remove
                         </button>
                    </div>
                ))}

                <button onClick={addGraph}>
                    + Add graph
                </button>
                </>
            )}
        </section>
    )
}

export default AnalysisPanel