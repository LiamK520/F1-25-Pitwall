import {useEffect, useRef, useState} from "react"

import type {RefObject} from "react"
import type {MotionFrame, LiveFrame} from "../types/api"

// ms
const REFRESH_RATE = 50
const MAP_WIDTH = 1000
const MAP_HEIGHT = 600
const MAP_PADDING = 50

interface TrackMapProps {
    latestMotionRef: RefObject<MotionFrame | null>
    latestFrameRef: RefObject<LiveFrame | null>
}

function TrackMap({latestMotionRef, latestFrameRef}: TrackMapProps) {
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

    const bounds = boundsRef.current
    const worldWidth = bounds.maxX - bounds.minX
    const worldHeight = bounds.maxZ - bounds.minZ

    const scaleX = (MAP_WIDTH - MAP_PADDING * 2) / worldWidth

    const scaleY = (MAP_HEIGHT - MAP_PADDING * 2) / worldHeight

    const scale = Math.min(scaleX, scaleY)

    const worldCentreX = (bounds.minX + bounds.maxX) / 2

    const worldCentreZ = (bounds.minZ + bounds.maxZ) / 2

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

                    {frame !== null && worldWidth > 0 && worldHeight > 0 && (
                        frame.cars.filter((car) => activeCars.has(car.index)).
                        map((car) => {
                            const carX = MAP_WIDTH / 2 + (car.x - worldCentreX) * scale
                            const carY = MAP_HEIGHT / 2 + (car.z - worldCentreZ) * scale

                            return (
                                <circle
                                    key={car.index}
                                    cx={carX}
                                    cy={carY}
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