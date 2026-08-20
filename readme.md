# F1 25 Pit Wall

Real time pit wall dashboard using UDP telemetry from EA SPORTS F1 25.


## ONGOING

- Backend internal application state
-- Flashback handling

## TODO

- API/Websocket layer
- Basic react frontend
- Documentation (minor documentation exists for some functions but overhaul planned)

## DONE

- Parsing of UDP packets (excluding motion_ex, lobby_info and time_trial packets - might support these in the future)
- UDP parser tests
- Backend internal application state
-- Storing up to date car and session states
-- Frame alignment of LapData and CarTelemetry packets

## Backlog

- Alignment of CarStatus packets to LapData and CarTelemetry (e.g. for plotting ers vs lap distance)