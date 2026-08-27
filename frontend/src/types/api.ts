export interface CarState {
  index: number

  name: string | null
  driver_id: number | null
  race_number: number | null
  team_id: number | null

  position: number | null
  lap: number | null
  sector: number | null
  lap_distance: number | null
  result_status: number | null

  speed: number | null
  gear: number | null
  rpm: number | null
}

export interface StateResponse {
  session_uid: number | null

  track_id: number | null
  track_name: string | null

  session_type: number | null
  session_name: string | null

  total_laps: number | null
  weather: number | null
  weather_name: string | null

  track_temperature: number | null
  air_temperature: number | null

  safety_car_status: number | null
  safety_car_status_name: string | null

  num_active_cars: number
  player_car_index: number | null

  cars: CarState[]
}


export interface SessionUpdate {
    type: "session_update"

    session_uid: number

    weather: number
    weather_name: string

    track_temperature: number
    air_temperature: number

    safety_car_status: number
    safety_car_status_name: string
}


export interface LiveCar {
  index: number

  last_lap_time_ms: number
  current_lap_time_ms: number

  sector1_time_ms: number
  sector2_time_ms: number

  delta_to_car_in_front_ms: number
  delta_to_race_leader_ms: number

  lap_distance: number
  total_distance: number
  safety_car_delta: number

  position: number
  lap: number
  pit_status: number
  num_pit_stops: number
  sector: number

  current_lap_invalid: boolean

  penalties: number
  total_warnings: number
  corner_cutting_warnings: number
  unserved_drive_throughs: number
  unserved_stop_go: number

  grid_position: number
  driver_status: number
  result_status: number

  pit_lane_timer_active: boolean
  pit_lane_time_ms: number
  pit_stop_time_ms: number
  pit_stop_should_serve_penalty: boolean

  speed_trap_fastest_speed: number
  speed_trap_fastest_lap: number | null

  speed: number
  throttle: number
  steer: number
  brake: number
  clutch: number

  gear: number
  rpm: number
  drs: boolean

  rev_lights_percent: number
  rev_lights_bit_value: number

  brakes_temperature: [number, number, number, number]
  tyres_surface_temperature: [number, number, number, number]
  tyres_inner_temperature: [number, number, number, number]

  engine_temperature: number

  tyres_pressure: [number, number, number, number]
  surface_type: [number, number, number, number]
}

export interface LiveFrame {
  type: "live_frame"

  session_uid: number

  frame: number
  overall_frame: number
  session_time: number

  player_car_index: number
  secondary_player_car_index: number | null

  time_trial_pb_car_index: number | null
  time_trial_rival_car_index: number | null

  mfd_panel_index: number | null
  mfd_panel_index_secondary_player: number | null
  suggested_gear: number | null

  cars: LiveCar[]
}