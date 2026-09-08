import { useMemo } from "react"
import ReactECharts from "echarts-for-react"

import type { LapTelemetryResponse } from "../types/api"

export interface TelemetryTrace{
    label: string
    telemetry: LapTelemetryResponse
}

export type TelemetryMetric =
    | "speed"
    | "throttle"
    | "brake"
    | "steer"
    | "gear"
    | "rpm"

interface TelemetryGraphProps {
    traces: TelemetryTrace[]
    metric: TelemetryMetric
}

const METRIC_CONFIG = {
    speed: {
        title: "Speed",
        unit: "km/h",
    },
    throttle: {
        title: "Throttle",
        unit: "%",
    },
    brake: {
        title: "Brake",
        unit: "%",
    },
    steer: {
        title: "Steering",
        unit: "",
    },
    gear: {
        title: "Gear",
        unit: "",
    },
    rpm: {
        title: "RPM",
        unit: "rpm",
    },
} as const

function TelemetryGraph({traces, metric}: TelemetryGraphProps) {
    const option = useMemo(() => {
        const config = METRIC_CONFIG[metric]

        return {
            title: {
                text: config.title,
            },

            tooltip: {
                trigger: "axis"
            },

            legend: {
                show: traces.length > 1,
            },

            grid: {
                left: 60,
                right: 30,
                top: 50,
                bottom: 45,
            },

            xAxis: {
                type: "value",
                name: "Lap distance (m)"
            },

            yAxis: {
                type: "value",
                name: config.unit
            },

            series: traces.map((trace) => ({
                name: trace.label,
                type: "line",

                showSymbol: false,
                animation: false,

                data: trace.telemetry.lap_distance.map(
                    (distance, index) => {
                        let value = trace.telemetry[metric][index]

                        // display pedals as percent
                        if (metric == "throttle" || metric == "brake") {
                            value *= 100
                        }

                        return [distance, value]
                    }
                )
            }))
        }
    }, [traces, metric])

    return (
        <ReactECharts 
            option={option}
            style={{
                width: "100%",
                height: "400px"
            }}
        />
    )
}

export default TelemetryGraph