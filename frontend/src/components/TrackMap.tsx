import {useEffect, useRef, useState} from "react"

import type {RefObject} from "react"
import type {MotionFrame, LiveFrame, TrackGeometry} from "../types/api"

// ms
const REFRESH_RATE = 50
const MAP_WIDTH = 1000
const MAP_HEIGHT = 600
const MAP_PADDING = 50

interface TrackMapProps {
    latestMotionRef: RefObject<MotionFrame | null>
    latestFrameRef: RefObject<LiveFrame | null>
    geometry: TrackGeometry | null
}

function TrackMap({latestMotionRef, latestFrameRef, geometry}: TrackMapProps) {
    const [frame, setFrame] = useState<MotionFrame | null>(null)

    // bounds for max and min x and z so far
    const boundsRef = useRef({
        minX: Infinity,
        maxX: -Infinity,
        minZ: Infinity,
        maxZ: -Infinity
    })

    useEffect(() => {
        const timer = window.setInterval(() => {
            const latest = latestMotionRef.current;
            const latestLive = latestFrameRef.current;

            if (latest !== null) {
                // set of valid car indices
                // 2 = racing so just use that for now
                // TODO: maybe keep dnfs but greyed?
                const activeCars = new Set(latestLive?.cars.filter((car) => {
                    return car.result_status === 2
                }).map((car) => car.index))

                for (const car of latest.cars) {
                    // skip invalid car
                    if (!activeCars.has(car.index)) continue;

                    boundsRef.current.minX = Math.min(
                        boundsRef.current.minX,
                        car.x
                    )

                    boundsRef.current.maxX = Math.max(
                        boundsRef.current.maxX,
                        car.x
                    )

                    boundsRef.current.minZ = Math.min(
                        boundsRef.current.minZ,
                        car.z
                    )

                    boundsRef.current.maxZ = Math.max(
                        boundsRef.current.maxZ,
                        car.z
                    )
                }
                setFrame(latest)
            }
        }, REFRESH_RATE)

        return () => {
            window.clearInterval(timer)
        }
    }, [latestMotionRef])

    const bounds = geometry ? {
        minX: geometry.min_x,
        maxX: geometry.max_x,
        minZ: geometry.min_z,
        maxZ: geometry.max_z
    } : boundsRef.current
    const worldWidth = bounds.maxX - bounds.minX
    const worldHeight = bounds.maxZ - bounds.minZ

    const scaleX = (MAP_WIDTH - MAP_PADDING * 2) / worldWidth

    const scaleY = (MAP_HEIGHT - MAP_PADDING * 2) / worldHeight

    const scale = Math.min(scaleX, scaleY)

    const worldCentreX = (bounds.minX + bounds.maxX) / 2

    const worldCentreZ = (bounds.minZ + bounds.maxZ) / 2

    function toMapPoint(x: number, z: number) {
        return {
            x: MAP_WIDTH / 2 + (x - worldCentreX) * scale,
            y: MAP_HEIGHT / 2 + (z - worldCentreZ) * scale
        }
    }

    function pointsToSvg(points: TrackGeometry["points"]) {
        return points.map((point) => {
            const mapped = toMapPoint(point.x, point.z)

            return `${mapped.x},${mapped.y}`
        }).join(" ")
    }

    // separate points into sectors
    const sector1 = geometry
        ? geometry.points.filter((point) =>
            point.distance >= 0 &&
            point.distance <= geometry.sector_2_start
        )
        : []

    const sector2 = geometry
        ? geometry.points.filter((point) =>
            point.distance >= geometry.sector_2_start &&
            point.distance <= geometry.sector_3_start
        )
        : []

    const sector3 = geometry
        ? geometry.points.filter((point) =>
            point.distance >= geometry.sector_3_start
        )
        : []

    // get as svg point
    const sector1Points = pointsToSvg(sector1)
    const sector2Points = pointsToSvg(sector2)

    const sector3Points = geometry && sector3.length > 0
        ? pointsToSvg([
            ...sector3,
            geometry.points[0]
        ])
        : ""

    // TODO: tidy up to use this calc once only
    const liveFrame = latestFrameRef.current

    const activeCars = new Set(
        liveFrame?.cars
            .filter((car) =>
                car.result_status == 2
            )
            .map((car) => car.index)
    )

    return (
        <section className="track-map">
            <h2>Track map</h2>
            <div className="track-map-canvas">
                <svg
                    viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
                    width="100%"
                    height="100%">  

                    {geometry && (
                        <>
                            <polyline
                                points={sector1Points}
                                fill="none"
                                stroke="#e10600"
                                strokeWidth="4"
                                strokeLinejoin="round"
                                strokeLinecap="round"
                            />

                            <polyline
                                points={sector2Points}
                                fill="none"
                                stroke="#ffd500"
                                strokeWidth="4"
                                strokeLinejoin="round"
                                strokeLinecap="round"
                            />

                            <polyline
                                points={sector3Points}
                                fill="none"
                                stroke="#00a8ff"
                                strokeWidth="4"
                                strokeLinejoin="round"
                                strokeLinecap="round"
                            />
                        </>
                    )}

                    {frame !== null && worldWidth > 0 && worldHeight > 0 && (
                        frame.cars.filter((car) => activeCars.has(car.index)).
                        map((car) => {
                            const point = toMapPoint(car.x, car.z)

                            return (
                                <circle
                                    key={car.index}
                                    cx={point.x}
                                    cy={point.y}
                                    r="6"
                                    fill="white"
                                />
                            )
                        })
                    )}

                </svg>
            </div>
        </section>
    )
}


export default TrackMap