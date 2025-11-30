
Buffet Queueing Simulation
This project is a discrete-event simulation built with Python and SimPy. It models the flow of customers through a buffet restaurant, tracking queue lengths, wait times, server utilization, and customer behaviors such as balking (leaving if the queue is full) or re-queuing (getting seconds).
Features
•	M/M/c Queue Model: Simulates stations with multiple servers and a single shared queue.
•	Complex Customer Logic:
o	Routing: Customers skip stations they don't want (Appetizer/Main/Dessert).
o	Balking: Customers leave if a station's queue is at capacity.
o	Reneging: Customers leave if they wait in the entry queue for more than 20 minutes.
o	Dining Capacity: Customers cannot leave the waiting area until a seat is available in the dining section.
o	Re-queuing: Customers may rejoin the food queues after eating if they are within the time limit.
•	Two Simulation Modes:
1.	Full Buffet Simulation: Runs consecutive workloads (Off-peak and Peak).
2.	Single Station Test: A unit test to verify the mathematical properties of a single M/M/c queue.
Prerequisites
•	Python 3.x
•	simpy library
Installation
1.	Save the simulation code into a file named buffet_sim.py.
2.	Install the required library using pip:
Bash
pip install simpy
How to Run
Open your terminal or command prompt, navigate to the directory where you saved the file, and run:
Bash
python buffet_sim.py
Usage Guide
When you run the script, you will be prompted to select a mode.
Mode 1: Full Buffet Simulation
This simulates the entire restaurant workflow. You will be asked to input configuration for 5 specific stations.
1. Simulation Setup:
•	Enter the total Simulation Time (in minutes).
2. Station Configuration:
The script will ask for the following parameters for 5 stations in this exact order: Waiting, Appetizer, Main Course, Dessert, and Dining.
For each station, you must provide:
•	Number of Servers: (e.g., How many chefs at the station, or how many tables in Dining).
•	Mean Service Time: (in minutes).
•	Queue Capacity: The max number of people allowed in line (Press Enter for unlimited).
3. Workload Configuration:
The simulation runs two phases automatically:
•	Workload 1 (Off-peak, $\lambda=1.0$): You will input the probability (0-1) that a customer gets seconds.
•	Workload 2 (Peak, $\lambda=5.0$): You will input the probability (0-1) that a customer gets seconds.
•	Max Time for Requeue: Limits re-queuing if the customer has been in the restaurant too long (enter 0 for no limit).
Mode 2: Single Station Test
This is a diagnostic tool to test a single queue (like a bank teller or a single food stall).
1.	Enter Number of Servers.
2.	Enter Mean Service Time.
3.	Enter Arrival Rate ($\lambda$).
4.	Enter Queue Capacity.
5.	Enter Simulation Time.
The script will output theoretical vs. actual utilization to verify the system is working correctly.
Simulation Flow Logic
1.	Arrival: Customer arrives at the Waiting station.
2.	Entry Check: If the waiting queue is full, they leave (Balk).
3.	Wait: They wait to be seated. If the wait > 20 mins, they leave (Reneg).
4.	Dining Capacity Check: Even if passed the waiting station, they hold until Dining capacity permits entry.
5.	Food Stations: Customer visits Appetizer -> Main -> Dessert based on random demand.
6.	Dining: Customer sits at the Dining station to eat.
7.	Re-queue Loop: Based on probability and time limits, the customer may return to the food stations (priority queue) or leave the system.
Interpreting Results
At the end of the simulation, the script prints a detailed report:
•	Overall Statistics: Total customers served, lost, and currently in the system.
•	Station Metrics:
o	Wait Time: How long customers stood in line.
o	Service Time: How long they spent getting food/eating.
o	Queue Length: Average and Max line sizes.
o	Utilization: Percentage of time the servers/tables were busy.
Troubleshooting
•	Input Errors: Ensure you enter integers for server counts and numbers/floats for times.
•	Zero Division: Do not enter 0 for Mean Service Time.
•	Infinite Loops: If you set very high arrival rates with very low service rates (servers too slow), the simulation might take longer to process all events, though until=until_time usually prevents this.

