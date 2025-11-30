Here is the **English version** of the README file, ready to be copied into your project. It includes clear instructions, theoretical context, and a step-by-step input guide.

-----

# Buffet & Queueing System Simulation

This project is a discrete-event simulation built using Python's **SimPy** library. It models the complex flow of a Buffet restaurant to analyze service efficiency, bottlenecks, and customer behavior under different constraints.

## 1\. Prerequisites & Installation

To run this simulation, you must have Python installed and the `simpy` library.

**Install the library:**

```bash
pip install simpy
```

**Run the simulation:**

```bash
python <your_file_name>.py
```

-----

## 2\. Theoretical Background

This simulation is based on **Queueing Theory**, specifically the **M/M/c** model. Understanding these terms will help you input the correct data:

  * **M/M/c Model:**
      * **M (Markov):** Arrival times are random (Poisson process / Exponential distribution).
      * **M (Markov):** Service times are random (Exponential distribution).
      * **c (Servers):** The number of service channels (e.g., number of chefs at a station, or number of tables in the dining area).
  * **$\lambda$ (Lambda - Arrival Rate):** How many customers arrive per minute.
  * **$\mu$ (Mu - Service Rate):** How fast a single server can process one customer (1 / Mean Service Time).
  * **Balking:** A customer arrives, sees the queue is full (exceeds `queue_capacity`), and leaves immediately.
  * **Reneging:** A customer joins the queue but leaves after waiting too long (defined as \> 20 minutes in the Waiting Area).
  * **Re-queueing:** The behavior where a customer finishes eating and decides to go back to the food stations for more.

-----

## 3\. Simulation Modes

Upon starting the program, you will be asked to select one of two modes:

### MODE 1: Run Full Buffet Simulation

  * **Purpose:** Simulates the complete, realistic workflow of a buffet restaurant.
  * **Workflow Logic:**
    1.  **Arrival:** Customers arrive at the `Waiting` station. If the queue is full or they wait \> 20 mins, they leave.
    2.  **Capacity Check:** Customers wait in the lobby until a seat is available in the `Dining` area.
    3.  **Food Stations:** Customers proceed to `Appetizer` $\rightarrow$ `Main Course` $\rightarrow$ `Dessert` based on random demand.
    4.  **Dining:** Customers sit and eat.
    5.  **Loop:** After eating, they may leave or **Re-queue** to get more food if they haven't exceeded the time limit.
  * **Scenarios:** The simulation automatically runs two consecutive workloads:
      * *Workload 1:* Off-peak hours ($\lambda = 1.0$ cust/min).
      * *Workload 2:* Peak hours ($\lambda = 5.0$ cust/min).

### MODE 2: Test Single Station

  * **Purpose:** A unit test for a single standard M/M/c queue.
  * **Use Case:** Use this to verify mathematical correctness without the complex logic of the full restaurant (e.g., verifying that a specific number of servers can handle a specific arrival rate).

-----

## 4\. Input Guide

### For MODE 1 (Full Simulation)

You will need to configure parameters for **5 stations** in this order: **Waiting**, **Appetizer**, **Main Course**, **Dessert**, and **Dining**.

1.  **Simulation Time:** Total run time in minutes (e.g., `120`).
2.  **Station Configuration (Repeat for all 5 stations):**
      * `Number of servers`: The number of staff or resources (e.g., for Dining, this is the number of seats).
      * `Mean service time`: Average time to serve one person (minutes).
      * `Total queue capacity`: Max people allowed in line. **Press Enter** for an unlimited line.
3.  **Workload Configuration:**
      * `Requeue probability`: Chance a customer gets seconds (0.0 to 1.0). E.g., `0.3` is 30%.
      * `Max time for requeue eligibility`: Time limit (minutes). If a customer has stayed longer than this, they are not allowed to get seconds. Enter `0` for no limit.

### For MODE 2 (Single Station Test)

This mode only asks for parameters for one isolated queue:

1.  `Number of servers`: Number of service channels ($c$).
2.  `Mean service time`: Average time to serve one customer ($1/\mu$).
3.  `Arrival rate`: Customers per minute ($\lambda$).
4.  `Queue capacity`: Max queue size (Press Enter for unlimited).
5.  `Simulation time`: Duration of the test.

-----

## 5\. Interpreting Results

After the simulation finishes, check the output for:

  * **Overall Statistics:**
      * `Customers completed`: Total served successfully.
      * `Customers left...`: Lost business due to full queues (Balking) or long waits (Reneging).
      * `Re-queue events`: Indicates how much extra load "second rounds" added to the system.
  * **Station Metrics:**
      * `Average wait time`: Lower is better.
      * `Server utilization`:
          * **Near 100%:** The station is a bottleneck (understaffed).
          * **Very low:** The station is overstaffed.

-----

## Sample Configuration (For Quick Start)

If you want to run **Mode 1** quickly to see how it works, use these values:

  * **Sim Time:** `480` (8 hours)
  * **Waiting Station:** 1 server, 1 min service, capacity: `Enter` (unlimited)
  * **Appetizer:** 2 servers, 2 min service, capacity: `10`
  * **Main Course:** 3 servers, 5 min service, capacity: `15`
  * **Dessert:** 2 servers, 3 min service, capacity: `10`
  * **Dining:** 50 servers (seats), 45 min service (eating time), capacity: `Enter`
  * **Requeue Probability:** `0.4`
  * **Max time requeue:** `90`