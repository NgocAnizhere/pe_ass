# Self-Service Buffet Queueing System Simulation

**Course:** System Performance Evaluation (CO3007)  
**Group:** Iron Sentinel

This project is a discrete-event simulation built using Python's **SimPy** library. It models a self-service buffet restaurant system with an **Open Queueing Network with Feedback Loop**, representing customers who return for more food after dining.

---

## 1. Overview

### System Architecture

The simulation models a buffet restaurant with the following service flow:

1. **Arrival & Waiting** → Customers arrive and wait at the entrance
2. **Food Service** → Sequential service at three counters: **Appetizer → Main Course → Dessert**
3. **Dining** → Customers sit and consume their meal
4. **Feedback Decision** → After dining, customers either exit or re-queue for more food based on probability (δ)

### Key Features

- **M/M/c Queue Model** for each service station
- **Random Service Requirements** - Customers randomly need appetizer/main course/dessert (at least one required)
- **Feedback Loop** - Customers can return for more food with configurable probability
- **Capacity Constraints** - Queue limits and dining capacity management
- **Balking** - Customers leave if waiting queue is full
- **Reneging** - Customers leave if waiting time exceeds input waiting time (in minutes)
- **Time-Limited Re-queueing** - Customers cannot re-queue if they exceed maximum time in system

---

## 2. Prerequisites & Installation

### Requirements

- Python 3.7 or higher
- SimPy library

### Installation

```bash
pip install simpy
```

For Jupyter Notebook users, also install:

```bash
pip install ipykernel jupyter
```

---

## 3. System Components

### Service Stations (M/M/c Queues)

| Station Name    | Real-world Entity | Servers (c)  | Service Time Mean (1/µ) | Queue Capacity |
| :-------------- | :---------------- | :----------- | :---------------------- | :------------- |
| **Waiting**     | Entrance          | Configurable | 0.5-1.0 mins            | Limited        |
| **Appetizer**   | Food Counter 1    | Configurable | 1.0-3.0 mins            | Limited        |
| **Main Course** | Food Counter 2    | Configurable | 1.5-7.0 mins            | Limited        |
| **Dessert**     | Food Counter 3    | Configurable | 0.8-4.0 mins            | Limited        |
| **Dining**      | Tables/Seats      | Configurable | 15.0 mins               | Limited        |

### Workload Configurations

The simulation includes two pre-configured workloads:

- **Workload 1 (Off-peak):** λ = 1.0 customer/minute, 30% re-queue probability , unlimited time (depend on input)
- **Workload 2 (Peak Hours):** λ = 5.0 customers/minute, 20% re-queue probability , 45-minute time limit (depend on input)

---

## 4. Running the Simulation

### Option A: Python Script (Simu.py)

**Note:** The current implementation uses hardcoded configurations in `Implementation.ipynb`. To create a standalone `Simu.py`:

1. Extract the classes and main execution code from the notebook
2. Run the script:

```bash
python Simu.py
```

The simulation will automatically run both Workload 1 and Workload 2 scenarios.

### Option B: Jupyter Notebook (Implementation.ipynb)

**Recommended for interactive analysis and visualization**

#### Step 1: Start Jupyter Notebook

```bash
jupyter notebook
```

Or open `Implementation.ipynb` directly in VS Code.

#### Step 2: Execute Cells in Order

1. **Cell 1:** Install SimPy (if not already installed)

   ```python
   pip install simpy
   ```

2. **Cell 2:** Import required libraries

   ```python
   import simpy
   import random
   import statistics
   import time
   ```

3. **Cell 3:** ServiceStation class definition

   - Defines the M/M/c queue model for each service station

4. **Cell 4:** BuffetSimulation class definition

   - Main simulation controller with routing logic and data collection

5. **Cell 5 or 6:** Run simulation with pre-configured workloads
   - Cell 5: Original configuration (higher service times)
   - Cell 6: Optimized configuration (lower service times)

#### Step 3: Analyze Results

The output includes:

- Overall statistics (arrivals, completions, customers who left)
- Station-by-station metrics (wait times, utilization, queue lengths)
- Event log (chronological customer journey)
- Station timeline (snapshots at each minute)

---

## 5. Configuration Parameters

### Station Configuration

Each station requires:

- `name`: Station identifier (waiting, appetizer, main_course, dessert, dining)
- `num_servers`: Number of parallel servers/resources (c)
- `mean_service_time`: Average service time in minutes (1/µ)
- `queue_capacity`: Maximum queue size (customers waiting)

### Simulation Parameters

- `SIM_TIME`: Simulation duration in minutes (default: 60)
- `REQUEUE_PROB`: Probability customer returns for more food (0.0-1.0)
- `MAX_TIME_REQUEUE`: Maximum time limit for re-queue eligibility (0 = unlimited)
- `ARRIVAL_RATE`: Customer arrival rate λ (customers per minute)

### Example Configuration (Cell 6 - Optimized)

```python
STATION_CONFIGS = [
    {"name": "waiting", "num_servers": 10, "mean_service_time": 0.5, "queue_capacity": 10},
    {"name": "appetizer", "num_servers": 3, "mean_service_time": 1.0, "queue_capacity": 3},
    {"name": "main_course", "num_servers": 4, "mean_service_time": 1.5, "queue_capacity": 3},
    {"name": "dessert", "num_servers": 2, "mean_service_time": 0.8, "queue_capacity": 3},
    {"name": "dining", "num_servers": 10, "mean_service_time": 15.0, "queue_capacity": 3}
]
```

---

## 6. Theoretical Background

### M/M/c Queue Model

- **First M (Markov):** Interarrival times are exponentially distributed (Poisson arrivals)
- **Second M (Markov):** Service times are exponentially distributed
- **c:** Number of parallel servers

### Performance Metrics

- **λ (Lambda):** Arrival rate (customers/minute)
- **µ (Mu):** Service rate per server (1/mean_service_time)
- **ρ (Rho):** Server utilization = λ/(c×µ)
- **L_q:** Average queue length
- **W_q:** Average waiting time in queue
- **W:** Average total time in system

### Queueing Behaviors

- **Balking:** Customer leaves immediately if queue is full upon arrival
- **Reneging:** Customer abandons queue after waiting >20 minutes
- **Re-queueing:** Customer returns to system after completing service (feedback loop)

---

## 7. Interpreting Results

### Overall Statistics

- **Total customers arrived:** Number of new customer arrivals
- **Customers completed:** Successfully served customers who exited
- **Customers still in system:** Currently being processed
- **Unique customers who completed dining:** Distinct customers (excluding re-queues)
- **Re-queue events:** Number of times customers returned for more food
- **Customers who left:** Due to full queue or excessive wait

### Station Metrics

- **Average wait time:** Time spent waiting in queue (lower is better)
- **Max wait time:** Longest wait experienced
- **Average service time:** Actual processing time
- **Average queue length:** Average number waiting (indicator of congestion)
- **Max queue length:** Peak queue size
- **Server utilization:** Percentage of time servers are busy
  - **>90%:** Potential bottleneck, consider adding servers
  - **<50%:** May be overstaffed

### Event Log

Chronological record of all customer events:

- ARRIVED, ARRIVED_LEFT (balking)
- ENTER_WAITING, EXIT_WAITING, LEFT (reneging)
- ENTER_STATION, EXIT_STATION (at each food counter)
- RETURN_WAITING (unmet demands)
- REQUEUE (voluntary return for more food)
- DEPARTED (exit system)

### Station Timeline

Minute-by-minute snapshots showing:

- Queue length at each station
- Customers in service
- Total customers served

---

## 8. Troubleshooting

### Common Issues

**Issue:** Kernel dies with "No module named ipykernel_launcher"  
**Solution:** Install ipykernel: `pip install ipykernel`

**Issue:** "No module named simpy"  
**Solution:** Install SimPy: `pip install simpy`

**Issue:** Simulation runs but shows all zeros  
**Solution:** Check that you're running the correct cell (Cell 5 or 6) that includes the `if __name__ == "__main__":` block

**Issue:** Very long execution time  
**Solution:** Reduce `SIM_TIME` or `ARRIVAL_RATE` for faster testing (if the terminal in vsc don't show all, you can do it in the shell or the system terminal)

---

## 9. Team

| Student             | ID      | Role        |
| ------------------- | ------- | ----------- |
| Lê Ngọc An          | 2252007 | Development |
| Nguyễn Ngọc Duy     | 2252118 | Development |
| Trương Phú Cường    | 2252100 | Design      |
| Vũ Trịnh Thanh Bình | 2252085 | Design      |
| Cao Võ Hoài Phúc    | 2053332 | Evaluation  |
| Võ Hoàng Long       | 2053192 | Evaluation  |

---

## 10. References

- SimPy Documentation: https://simpy.readthedocs.io
- Queueing Theory: M/M/c models and performance analysis
- System Performance Evaluation course materials (CO3007)

---

## Sample Quick Start Configuration

For testing purposes, try these values:

- **Simulation Time:** 60 minutes
- **Workload:** Use pre-configured WORKLOAD1 or WORKLOAD2
- **Observe:** Station utilization and queue lengths to identify bottlenecks

### Tips for Analysis

1. **Identify Bottlenecks:** Look for stations with >90% utilization and long queues
2. **Balance Load:** Adjust number of servers or service times
3. **Monitor Re-queue Impact:** High re-queue rates significantly increase system load
4. **Check Customer Loss:** High balking/reneging indicates capacity issues
