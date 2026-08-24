import { useEffect, useState} from "react"
import type { RefObject } from "react"

import type { LiveCar, LiveFrame, StateResponse } from "../types/api"


interface DriverTelemetryProps {
    state: StateResponse
    carIndex: number
    latestFrameRef: RefObject<LiveFrame | null>
}