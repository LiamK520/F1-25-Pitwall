# F1 25 Pit Wall

Real time pit wall dashboard using UDP telemetry from EA SPORTS F1 25.


## Ongoing

- API/Websocket layer        

## Todo

- Backend analysis
    - Features TBD
- Basic react frontend
- Documentation (minor documentation exists for some functions but overhaul planned)

## Backlog

- Alignment of CarStatus packets to LapData and CarTelemetry (e.g. for plotting ers vs lap distance)
- Parsing of MotionEx, LobbyInfo and TimeTrial packets

## Done

- Parsing of main UDP packets
- Backend internal application state
    - Storing up to date car and session states
    - Frame alignment of LapData and CarTelemetry packets
    - Flashback handling
        - Same lap flashbacks
        - Flashback to different laps