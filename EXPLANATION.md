# Buffet Queuing System Simulation - Implementation Explanation

## Overview
This document explains the implementation of a **self-service buffet system simulation** using discrete-event simulation techniques. The system models customers moving through multiple food counters with a feedback loop for customers who return for additional servings.

---

## System Model

### Type: Open Queuing Network with Feedback Loop
- **Open Network**: Customers enter from outside (arrivals) and eventually exit
- **Feedback Loop**: After dining, customers may return to food counters based on probability
- **M/M/c Queues**: Each service station follows an M/M/c queuing model
  - First M: Poisson arrivals (exponential inter-arrival times)
  - Second M: Exponential service times
  - c: Multiple parallel servers

---

## Customer Journey (4 Steps)

### Step 1: Arrival and Waiting
- Customers arrive following a Poisson process (rate λ)
- Wait at entrance if all entry positions are busy
- Modeled as **Station 0** (Waiting Area)

### Step 2: Food Service (Sequential)
Customers visit three food counters in order:
1. **Station 1**: Appetizer Counter
2. **Station 2**: Main Course Counter
3. **Station 3**: Dessert Counter

### Step 3: Dining
- **Station 4**: Dining Area
- Customers occupy tables to eat their food
- Must queue if all tables are occupied

### Step 4: Decision Point
After eating, customer decides:
- **Probability δ**: Return to food counters (skip entrance, go back to appetizers)
- **Probability (1-δ)**: Exit the system

---

## Implementation Structure

### Class 1: ServiceStation
**Purpose**: Represents a single M/M/c service point

**Attributes**:
- `env`: SimPy simulation environment
- `num_servers`: Number of parallel servers (c in M/M/c)
- `mean_service_time`: Average service time (1/µ where µ is service rate)
- `resource`: SimPy Resource managing the c servers
- `wait_times`: List of queue waiting times
- `service_times`: List of actual service durations
- `queue_lengths`: List of queue lengths at each arrival
- `customers_served`: Total count of customers

**Method: serve(customer_id)**
1. Records arrival time and current queue length
2. Requests a server using `resource.request()` (waits if all busy)
3. Calculates wait time once server is acquired
4. Generates service time from exponential distribution
5. Simulates service via `env.timeout(service_time)`
6. Automatically releases server when done
7. Increments customer counter

**Key Feature**: The `yield request` statement pauses execution if all servers are busy. When a server becomes available, the customer resumes from that point with an updated `env.now` time.

---

### Class 2: BuffetSimulation
**Purpose**: Main controller managing the entire simulation

**Attributes**:
- `env`: SimPy environment
- `stations`: Dictionary of ServiceStation objects
- `station_names`: Dictionary for display names
- `customer_count`: Counter for unique IDs
- `total_customers`: Total arrivals
- `completed_customers`: Customers who exited
- `requeue_count`: Number of re-queue events
- `customer_total_times`: List of total system times

**Method: setup_stations(station_configs)**
- Creates ServiceStation objects from configuration list
- Each config contains: name, num_servers, mean_service_time
- Stores stations in dictionary by name

**Method: generate_arrivals(mean_arrival_time, station_configs, requeue_prob)**
- Infinite loop generating customer arrivals
- Uses `random.expovariate(1.0 / mean_arrival_time)` for Poisson process
- Creates unique customer ID for each arrival
- Launches `customer_process` as parallel SimPy process

**Method: customer_process(customer_id, stations, requeue_prob)**
- Records start time
- Goes to entrance (waiting station) on first visit
- Enters while loop for re-queuing:
  - Visits appetizer → main course → dessert sequentially
  - Goes to dining area
  - Generates random number to decide: re-queue or exit
  - If re-queue: increments counter and continues loop
  - If exit: breaks loop
- Records total time and increments completion counter

**Method: run_simulation(until_time, mean_arrival_time, station_configs, requeue_prob)**
- Main entry point
- Calls `setup_stations()` to create all stations
- Starts `generate_arrivals()` process
- Runs simulation via `env.run(until=until_time)`
- Prints results

**Method: print_results()**
- Displays overall statistics (arrivals, completions, re-queues)
- Shows average/max/min total system time
- For each station, displays:
  - Number of servers
  - Customers served
  - Average and max wait times
  - Average service time
  - Average and max queue lengths
  - Server utilization percentage

---

## Parameter Mapping

| Real-World Factor | Model Component | Parameter | Description |
|-------------------|-----------------|-----------|-------------|
| Customer arrivals | Source | λ (arrival rate) | `mean_arrival_time = 1/λ` |
| Waiting area | Station 0 (M/M/c) | c₀, 1/µ₀ | Servers and service time |
| Appetizer counter | Station 1 (M/M/c) | c₁, 1/µ₁ | Servers and service time |
| Main course counter | Station 2 (M/M/c) | c₂, 1/µ₂ | Servers and service time |
| Dessert counter | Station 3 (M/M/c) | c₃, 1/µ₃ | Servers and service time |
| Dining area | Station 4 (M/M/c) | c₄, 1/µ₄ | Servers (tables) and eating time |
| Customer decision | Decision Point | δ (requeue_prob) | Probability of returning |

---

## Workload Definitions

### Workload 1: Off-Peak Hours
**Scenario**: Restaurant is not busy (weekday afternoon)

**Parameters**:
- Arrival rate: λ = 1 customer/minute → `mean_arrival_time = 1.0`
- Re-queue probability: δ = 0.2 (20% return for more food)
- Station capacities:
  - Waiting: 2 servers, 0.5 min service
  - Appetizer: 3 servers, 1.0 min service
  - Main Course: 3 servers, 1.5 min service
  - Dessert: 2 servers, 0.8 min service
  - Dining: 20 tables, 15.0 min eating time

**Testing Goal**: Baseline performance with low stress

---

### Workload 2: Peak Hours
**Scenario**: Restaurant is crowded (weekend lunch/dinner)

**Parameters**:
- Arrival rate: λ = 5 customers/minute → `mean_arrival_time = 0.2` (12 seconds)
- Re-queue probability: δ = 0.15 (15% - lower when busy)
- Station capacities (increased):
  - Waiting: 4 servers, 0.5 min service
  - Appetizer: 5 servers, 1.0 min service
  - Main Course: 5 servers, 1.5 min service
  - Dessert: 4 servers, 0.8 min service
  - Dining: 40 tables, 15.0 min eating time

**Testing Goal**: System throughput under high pressure, observe queues

---

## Key Implementation Details

### Discrete-Event Simulation
- Uses **SimPy** library for event-driven simulation
- Time advances in discrete jumps (not continuous)
- Events: arrival, service start, service end, customer decision

### Exponential Distributions
- **Inter-arrival times**: `random.expovariate(1.0 / mean_arrival_time)` creates Poisson process
- **Service times**: `random.expovariate(1.0 / mean_service_time)` creates memoryless service

### SimPy Resources
- `simpy.Resource(env, capacity=num_servers)` manages server pool
- Automatic queuing when all servers busy
- `with resource.request() as request:` pattern ensures proper release

### Generator Functions (yield)
- All process methods use `yield` to create SimPy processes
- `yield request`: Wait for resource
- `yield env.timeout(time)`: Advance simulation time
- `yield env.process(method())`: Start parallel process

### Time Tracking
- `env.now`: Current simulation time (minutes)
- Wait time = time when server acquired - arrival time
- Total time = time when exiting - time when entering

### Metrics Collection
- Lists store individual measurements for statistical analysis
- `statistics.mean()` calculates averages
- `max()` and `min()` find extremes
- Server utilization = (total busy time) / (total available time)

---

## Execution Flow

1. **Initialization**: Set random seed (42) for reproducibility
2. **Simulation Duration**: 480 minutes (8 hours)
3. **Workload 1**: Run off-peak scenario, display results
4. **User Pause**: Wait for Enter key
5. **Workload 2**: Run peak hours scenario, display results
6. **Completion**: Show summary message

---

## Performance Metrics Reported

### Overall Statistics
- Total customers arrived
- Customers completed (exited)
- Customers still in system at end
- Number of re-queue events
- Average/Max/Min total time in system

### Per-Station Metrics
- Number of servers
- Total customers served
- Average and maximum wait time
- Average service time
- Average and maximum queue length
- Server utilization percentage

---

## Compliance with Phase 1 Specifications

✅ **System Model**: Open queuing network with feedback loop  
✅ **Customer Journey**: All 4 steps implemented  
✅ **M/M/c Queues**: All stations use exponential distributions  
✅ **SimPy Library**: Discrete-event simulation framework  
✅ **Two Workloads**: Off-peak (λ=1) and Peak (λ=5)  
✅ **ServiceStation Class**: Correct interface (`__init__`, `serve`)  
✅ **BuffetSimulation Class**: All 5 methods implemented correctly  
✅ **Parameter Mapping**: All parameters (λ, µ, c, δ) correctly mapped  

---

## How to Run

```bash
python Simu.py
```

The simulation will:
1. Display Workload 1 results
2. Pause for user input
3. Display Workload 2 results
4. Show completion message

---

## Dependencies

- `simpy`: Discrete-event simulation framework
- `random`: Random number generation
- `statistics`: Statistical calculations
- `time`: Real-world execution timing

---

## Notes

- **Random Seed**: Set to 42 for reproducible results
- **Generator Functions**: Critical for SimPy - all process methods must use `yield`
- **Resource Management**: `with` statement ensures servers are properly released
- **Parallel Processes**: Multiple customers processed simultaneously by SimPy
- **Time Units**: All times in minutes

---

*This implementation fully complies with the Phase 1 design specifications for the System Performance Evaluation project.*
