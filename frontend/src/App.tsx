import { useEffect, useState, useRef } from "react"

import type {
  LiveFrame,
  StateResponse,
} from "./types/api"

import TimingTower from "./components/TimingTower"

function App() {
  const [state, setState] = useState<StateResponse | null>(null)
  // use refs for frame so we dont update timing tower 20-60x a sec
  const latestFrameRef = useRef<LiveFrame | null>(null)
  const [timingFrame, setTimingFrame] = useState<LiveFrame | null>(null)

  const [wsConnected, setWsConnected] = useState(false)

  const [selectedCarIndex, setSelectedCarIndex] = useState<number | null>(null)

  async function loadState() {
    const response = await fetch("/state")
    const data: StateResponse = await response.json()

    setState(data)
  }

  // init state
  useEffect(() => {
    loadState()
  }, [])

  // if state not up to date load it again
  useEffect(() => {
  if (timingFrame === null) {
    return
  }

  if (timingFrame.session_uid !== state?.session_uid) {
    loadState()
  }
}, [timingFrame?.session_uid])

  // websocket connection
  useEffect(() => {
    const protocol =
      window.location.protocol === "https:" ? "wss" : "ws"

    const socket = new WebSocket(
      `${protocol}://${window.location.host}/ws`
    )

    socket.onopen = () => {
      setWsConnected(true)
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === "live_frame") {
        latestFrameRef.current = data as LiveFrame
      }
    }

    socket.onclose = () => {
      setWsConnected(false)
    }

    return () => {
      socket.close()
    }
  }, [])

  // refresh timing tower 2x a second
  useEffect(() => {
    const timer = window.setInterval(() => {
      const latest = latestFrameRef.current

      if (latest !== null) {
        setTimingFrame(latest)
      }
    }, 500)

    return () => {
      window.clearInterval(timer)
    }
  }, [])


  return (
    <main>
      <h1>F1 25 Pit Wall</h1>

      <h2>Backend</h2>

      <p>HTTP state: {state ? "Connected" : "Loading..."}</p>

      <p>WebSocket: {wsConnected ? "Connected" : "Disconnected"}</p>

      <h2>Session</h2>

      <p>Session UID: {state?.session_uid ?? "No session"}</p>

      <p>Active cars: {state?.num_active_cars ?? 0}</p>

      <h2>Live</h2>

      <p>Overall frame: {timingFrame?.overall_frame ?? "-"}</p>

      <p>Session time: {timingFrame?.session_time.toFixed(2) ?? "-"}</p>

      <p>Live cars: {timingFrame?.cars.length ?? 0}</p>

      {state && timingFrame && (
        <TimingTower
          state={state}
          frame={timingFrame}
          onSelectCar={setSelectedCarIndex}
        />
      )}

      <p>Selected car: {selectedCarIndex ?? "None"}</p>
    </main>
  )
}

export default App