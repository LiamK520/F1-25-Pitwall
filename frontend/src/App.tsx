import { useEffect, useState, useRef, act } from "react"

import type {
  LiveFrame,
  StateResponse,
  SessionUpdate,
} from "./types/api"

import TimingTower from "./components/TimingTower"
import DriverTelemetry from "./components/DriverTelemetry"
import InfoBar from "./components/InfoBar"
import PanelNavigator, {type DashboardTab} from "./components/PanelNavigator"
import TrackMap from "./components/TrackMap"
import ComparisonArea from "./components/ComparisonArea"

import "./App.css"

// ms
const REFRESH_RATE = 500

function App() {
  const [state, setState] = useState<StateResponse | null>(null)
  // use refs for frame so we dont update timing tower 20-60x a sec
  const latestFrameRef = useRef<LiveFrame | null>(null)
  const [timingFrame, setTimingFrame] = useState<LiveFrame | null>(null)

  const [wsConnected, setWsConnected] = useState(false)

  const [selectedCarIndex, setSelectedCarIndex] = useState<number | null>(null)

  const [activeTab, setActiveTab] = useState<DashboardTab>("live")


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

      else if (data.type == "session_update") {
        const update = data as SessionUpdate

        // update fields thjat are in update

        setState((current) => {
          if (current == null) return current;

          // ignore for now
          if (current.session_uid !== update.session_uid) return current;

          return {
            ...current,

            weather: update.weather,
            weather_name: update.weather_name,

            track_temperature: update.track_temperature,
            air_temperature: update.air_temperature,

            safety_car_status: update.safety_car_status,
            safety_car_status_name: update.safety_car_status_name,
          }
        })
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
    }, REFRESH_RATE)

    return () => {
      window.clearInterval(timer)
    }
  }, [])

  // set content to correct dashboard
  let content

  switch (activeTab) {
    case "live":
      content = (
        <div className="live-grid">
          <aside className="timing-area">
            {state && timingFrame && (
              <TimingTower
                  state={state}
                  frame={timingFrame}
                  onSelectCar={setSelectedCarIndex}
              />
            )}
            {state && selectedCarIndex !== null && (
                <DriverTelemetry
                    state={state}
                    carIndex={selectedCarIndex}
                    latestFrameRef={latestFrameRef}
                />
            )}
          </aside>

          <TrackMap />

          <ComparisonArea />
        </div>
      )
      break

    case "analysis":
        content = (
            <section className="analysis-panel">
                <h2>Analysis</h2>
                <p>Analysis panel coming soon</p>
            </section>
        )
        break

    case "session":
        content = (
            <section className="session-panel">
                <h2>Session</h2>
                <p>Session information coming soon</p>
            </section>
        )
        break
  }


  return (
    <div className="app-shell">
        <h1 className="app-title">
            F1 25 Pit Wall
        </h1>

        <main className="app">
            <InfoBar state={state} frame={timingFrame}/>

            <div className="page-content">
                {content}
            </div>

            <PanelNavigator
                activeTab={activeTab}
                onTabChange={setActiveTab}
            />
        </main>
    </div>
  )


  /*
  return (
    <main className="app">
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

      {state && selectedCarIndex !== null && (
        <DriverTelemetry
          state={state}
          carIndex={selectedCarIndex}
          latestFrameRef={latestFrameRef}
        />
      )}
    </main>
  )
  */
}

export default App