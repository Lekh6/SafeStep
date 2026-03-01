# SafeStep CV-Driven Pedestrian Signal Orchestration

This document translates the proposed concept into an implementation-ready software design for a camera-integrated pedestrian crossing control system.

## 1) Objective and Scope

SafeStep coordinates:

- Computer vision (CV) from roadside cameras.
- Pedestrian signal controllers and traffic phases.
- Enforcement/event logging (plate/body capture, incident records).
- Emergency handling (vehicle priority and pedestrian-collision reporting).

The system must always prioritize safety, then balance pedestrian service and traffic throughput.

## 2) Core Runtime Modules

1. **Perception Engine**
   - Pedestrian detection/tracking in preconfigured waiting and crossing zones.
   - Vehicle detection/tracking for approach lanes.
   - License plate and vehicle appearance capture for violations.
   - Emergency vehicle/siren detection.
   - Accident detection.

2. **State Estimator**
   - Computes live metrics:
     - `ped_wait_count`
     - `ped_avg_wait_s`
     - `ped_queue_pressure`
     - `traffic_flow_rate`
     - `traffic_queue_length`
     - `crosswalk_occupied`
   - Maintains confidence scores and stale-data timers.

3. **Decision Engine**
   - Dynamic thresholding for pedestrians and traffic.
   - Multi-objective scoring to choose: hold vehicle green, give walk, all-red emergency, or suspended crossing mode.
   - Hard safety constraints and preemption priorities.

4. **Signal Controller Adapter**
   - Sends commands to pedestrian signal controllers / traffic cabinet interfaces.
   - Reads acknowledgements and lamp state feedback.
   - Enforces minimum phase durations and legal inter-green intervals.

5. **Event & Evidence Service**
   - Stores encrypted plate data and incident snapshots.
   - Writes tamper-evident logs.
   - Handles escalation policies (e.g., repeated offenders).

6. **Safety Supervisor**
   - Watchdog for CV failures, comms failures, model drift, and heartbeat loss.
   - Triggers deterministic fail-safe: controller automatic mode.

## 3) Mapping of Your 13-Point Plan to Software Behavior

### 3.1 Pedestrian zone monitoring
- Define two square wait zones (both sides of crosswalk) plus optional approach corridors.
- Approach detections increase *soft* intent score only; wait-zone occupancy is primary trigger.

### 3.2 Dynamic pedestrian threshold
- Base threshold decreases as:
  - waiting count increases,
  - wait time increases.
- Example:
  - `ped_threshold = base - a*ped_wait_count - b*ped_avg_wait_s`, clamped to safe range.

### 3.3 Simultaneous traffic assessment
- Continuous traffic metrics from vehicle tracks.
- Decision compares pedestrian pressure vs. traffic pressure using weighted policy.

### 3.4 Execute crossing decision
- If decision score exceeds policy threshold and safety constraints pass:
  - Request phase transition.
  - Enter pedestrian WALK state.

### 3.5 Mid-crossing occupancy checks
- During WALK/clearance:
  - Keep monitoring crossing occupancy.
  - Extend clearance if legally allowed and occupancy remains true.

### 3.6 Traffic quality-of-life threshold and suspended crossing mode
- If traffic pressure exceeds configured cap:
  - Crosswalk requests can be temporarily suspended (except emergency safety triggers).
  - Suspension is time-bounded and auditable.

### 3.7 Violation detection during active crossing
- If vehicle enters protected crosswalk during active pedestrian right-of-way:
  - classify as violation event.

### 3.8 Plate/body capture, escalation, pedestrian-collision dispatch
- Capture plate ROI + vehicle full-body frame.
- Encrypt sensitive records at rest.
- Escalate according to policy (repeat rate, severity).
- Pedestrian-collision detection triggers emergency call workflow.

### 3.9 Emergency vehicle handling
- Detect siren/emergency light patterns/vehicle class.
- Issue all-red for pedestrian movements as policy dictates and release corridor priority.

### 3.10 Fail-safe fallback
- On persistent errors/timeouts:
  - relinquish to cabinet automatic mode.
  - generate operator alert.

### 3.11 Encrypted license plate logging
- Use envelope encryption and key rotation.
- Store minimal PII required by policy.

### 3.12 Predictive triggering (optional)
- Forecast near-term pedestrian arrivals using trajectory vectors/history.
- Only used as advisory; cannot violate safety constraints.

### 3.13 Emergency all-red on unauthorized pedestrian step-in
- If a pedestrian enters crosswalk while vehicle movement has right-of-way:
  - trigger immediate emergency all-red interlock.
  - keep all-red until crosswalk clear and minimum safety hold met.

## 4) Decision Policy (Recommended Priority Order)

1. **Hard safety interlocks**
   - Unauthorized pedestrian in carriageway → immediate all-red.
   - Active crosswalk occupancy during phase change conflict → block transition.

2. **Emergency preemption**
   - Emergency vehicle handling policy.

3. **Collision/incident handling**
   - Freeze into safe state + notify emergency services.

4. **Normal optimization layer**
   - Pedestrian-vs-traffic weighted thresholding.

## 5) Controller Integration Requirements

Because this software works in tandem with cameras *and* pedestrian signal controllers:

- Support standard controller protocols or cabinet I/O bridge.
- Required commands:
  - `request_ped_phase`
  - `force_all_red`
  - `suspend_ped_service`
  - `resume_normal_operation`
- Required feedback:
  - current phase state
  - lamp confirmation
  - command ack/nack
  - controller health heartbeat

## 6) Data Model (Minimum)

- `CrossingState`
  - `mode`: normal | emergency | suspended | failsafe
  - `ped_signal`: dont_walk | walk | flashing_dont_walk
  - `vehicle_phase`: green/yellow/red per approach
  - `crosswalk_occupied`: bool
- `PedMetrics`
  - counts, wait-time histogram, intent score
- `TrafficMetrics`
  - approach flow, occupancy, queue estimate
- `EventRecord`
  - type, timestamp, confidence, media refs, encrypted identifiers

## 7) Safety, Legal, and Operational Guardrails

- Never shorten legally required clearance intervals.
- Preserve auditable timeline for each command and detected trigger.
- Apply retention and access controls for enforcement media.
- Provide operator override and maintenance mode.
- Run continuous health checks with bounded failover time.

## 8) Acceptance Criteria ("Done" Definition)

The plan is considered implementation-ready when all are true:

1. Zone configuration and calibration validated on site.
2. Decision engine demonstrates stable behavior under mixed demand.
3. Controller adapter passes command/feedback integration tests.
4. Emergency all-red trigger validates under simulated unauthorized entry.
5. Violation capture and encryption validated end-to-end.
6. Failsafe reversion to automatic mode verified under forced faults.
7. Monitoring dashboards and incident exports available to operators.

## 9) Suggested Next Build Milestones

1. Build simulator + replay harness for pedestrian/traffic scenarios.
2. Integrate cabinet adapter with dry-run mode.
3. Stand up event storage with encryption/KMS.
4. Implement and test emergency all-red interlock first.
5. Run phased pilot at one intersection with shadow mode before live control.
