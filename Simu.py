import simpy
import random
import statistics
import time


class ServiceStation:
    def __init__(self, env, num_servers, mean_service_time, queue_capacity=float('inf')):
        self.env = env
        self.num_servers = num_servers
        self.mean_service_time = mean_service_time
        self.queue_capacity = queue_capacity
        
        # Single shared queue feeding c servers (M/M/c model)
        self.resource = simpy.Resource(env, capacity=num_servers)
        
        self.wait_times = []
        self.service_times = []
        self.queue_lengths = []
        self.customers_served = 0
        
        # Track which server served each customer (for statistics)
        self.server_customers_served = [0 for _ in range(num_servers)]
        self.next_server = 0  # Round-robin assignment for tracking
    
    def has_available_queue(self):
        """Check if queue has space available"""
        # In M/M/c model, check if total queue length is below capacity
        return len(self.resource.queue) < self.queue_capacity
    
    def get_current_queue_length(self):
        """Get current queue length (customers waiting, not being served)"""
        return len(self.resource.queue)
    
    def get_current_in_service(self):
        """Get number of customers currently being served"""
        return self.resource.count
        
    def serve(self, customer_id):
        arrival_time = self.env.now
        
        # Record queue length when customer arrives
        queue_length = len(self.resource.queue)
        self.queue_lengths.append(queue_length)
        
        # Request service from the shared resource pool
        with self.resource.request() as request:
            yield request
            
            # Customer got a server
            wait_time = self.env.now - arrival_time
            self.wait_times.append(wait_time)
            
            # Assign to server (round-robin for tracking purposes)
            server_index = self.next_server
            self.next_server = (self.next_server + 1) % self.num_servers
            
            service_time = random.expovariate(1.0 / self.mean_service_time)
            self.service_times.append(service_time)
            
            yield self.env.timeout(service_time)
            
            self.customers_served += 1
            self.server_customers_served[server_index] += 1


class BuffetSimulation:
    def __init__(self):
        self.env = simpy.Environment()
        self.stations = {}
        self.customer_count = 0
        self.total_customers = 0
        self.completed_customers = 0
        self.requeue_count = 0
        self.customer_total_times = []
        self.waiting_area = []  # Queue for customers waiting to enter stations
        self.unmet_demand_returns = 0  # Count customers returning due to unmet demands
        self.customers_completed_dining = set()  # Track unique customers who finished dining
        self.customers_left_full_queue = 0  # Customers who left because waiting queue was full
        self.customers_left_excessive_wait = 0  # Customers who left after waiting > 20 minutes
        self.customers_in_service_stations = 0  # Track customers currently in service stations (not waiting/dining)
        self.customers_denied_requeue = 0  # Customers who left because they exceeded max time for requeue

    def setup_stations(self, station_configs):
        for config in station_configs:
            queue_capacity = config.get('queue_capacity', float('inf'))
            station = ServiceStation(
                self.env,
                config['num_servers'],
                config['mean_service_time'],
                queue_capacity
            )
            self.stations[config['name']] = station
            if queue_capacity != float('inf'):
                capacity_str = f"total queue capacity = {queue_capacity}, total capacity (queue + servers) = {queue_capacity + config['num_servers']}"
            else:
                capacity_str = "unlimited queue"
            print(f"Station '{config['name']}': {config['num_servers']} servers, "
                  f"service time = {config['mean_service_time']:.2f} min, {capacity_str}")
        print()
    
    def get_total_waiting_queue_length(self):
        """Get total number of customers in waiting station queue"""
        return len(self.stations['waiting'].resource.queue)
    
    def get_total_service_station_customers(self):
        """Get total customers in appetizer, main_course, and dessert stations"""
        total = 0
        for station_name in ['appetizer', 'main_course', 'dessert']:
            # Count customers in queue + being served
            station = self.stations[station_name]
            total += len(station.resource.queue) + station.resource.count
        return total
    
    def get_dining_total_capacity(self):
        """Get total capacity of dining station (queue + servers)"""
        station = self.stations['dining']
        # Total capacity = customers in queue + customers being served
        # In M/M/c: max queue size + number of servers
        if station.queue_capacity == float('inf'):
            return float('inf')
        return station.queue_capacity + station.num_servers
    
    def generate_service_requirement(self):
        """Generate service requirement in n/n/n format for appetizer/main_course/dessert"""
        while True:
            req = [
                random.choice([0, 1]),  # Appetizer
                random.choice([0, 1]),  # Main course
                random.choice([0, 1])   # Dessert
            ]
            # Ensure at least one station is required (not 0/0/0)
            if sum(req) > 0:
                return req
    
    def generate_arrivals(self, mean_arrival_time, requeue_prob):
        while True:
            yield self.env.timeout(random.expovariate(1.0 / mean_arrival_time))
            
            self.customer_count += 1
            self.total_customers += 1
            customer_id = f"Customer_{self.customer_count}"
            service_req = self.generate_service_requirement()
            
            # Check if waiting station has space
            waiting_capacity = self.stations['waiting'].num_servers * self.stations['waiting'].queue_capacity
            current_waiting = self.get_total_waiting_queue_length() + self.stations['waiting'].customers_served
            
            if not self.stations['waiting'].has_available_queue():
                # Waiting queue is full, customer leaves
                self.customers_left_full_queue += 1
            else:
                # Customer can enter
                self.env.process(self.customer_process(customer_id, requeue_prob, service_req))

    def customer_process(self, customer_id, requeue_prob, service_req, is_requeue=False):
        start_time = self.env.now
        waiting_start_time = self.env.now
        
        # Create a mutable copy of service requirements to track fulfillment
        current_demands = service_req.copy()
        
        # Customer enters waiting area first
        if is_requeue:
            # Requeued customers go to the front
            self.waiting_area.insert(0, (customer_id, current_demands, start_time))
        else:
            self.waiting_area.append((customer_id, current_demands, start_time))
        
        # Process through waiting station with timeout monitoring
        waiting_process = self.env.process(self.stations['waiting'].serve(customer_id))
        timeout_process = self.env.timeout(20)  # 20 minutes max wait
        
        # Wait for either service completion or timeout
        result = yield waiting_process | timeout_process
        
        # Check if customer waited too long
        if timeout_process in result:
            # Customer waited more than 20 minutes, leaves
            self.customers_left_excessive_wait += 1
            return
        
        # Check dining capacity constraint before leaving waiting
        dining_capacity = self.get_dining_total_capacity()
        while True:
            customers_in_service = self.get_total_service_station_customers()
            if customers_in_service < dining_capacity:
                break
            # Wait until capacity frees up
            yield self.env.timeout(0.1)
        
        # Define station order: appetizer -> main_course -> dessert
        station_order = ['appetizer', 'main_course', 'dessert']
        
        # Keep trying to fulfill demands until all are met
        while sum(current_demands) > 0:  # While there are unmet demands
            demand_met_this_round = False
            
            # Check each station in order
            for i, station_name in enumerate(station_order):
                if current_demands[i] == 1:  # Customer needs this station
                    # Check if station has available queue space
                    if self.stations[station_name].has_available_queue():
                        # Increment counter before entering service station
                        self.customers_in_service_stations += 1
                        # Proceed to station and get service
                        yield self.env.process(self.stations[station_name].serve(customer_id))
                        # Decrement counter after leaving service station
                        self.customers_in_service_stations -= 1
                        # Mark this demand as fulfilled
                        current_demands[i] = 0
                        demand_met_this_round = True
                    # If queue is full, skip to next station
            
            # If no demands were met this round, customer goes back to waiting
            if not demand_met_this_round and sum(current_demands) > 0:
                # Customer returns to waiting area (back of queue)
                self.waiting_area.append((customer_id, current_demands, start_time))
                
                # Process through waiting station again with timeout
                waiting_process = self.env.process(self.stations['waiting'].serve(customer_id))
                timeout_process = self.env.timeout(20)
                result = yield waiting_process | timeout_process
                
                if timeout_process in result:
                    self.customers_left_excessive_wait += 1
                    return
        
        # All food station demands are met, now go to dining station
        while not self.stations['dining'].has_available_queue():
            yield self.env.timeout(0.1)  # Wait for space
        
        yield self.env.process(self.stations['dining'].serve(customer_id))
        
        # Track unique customer who completed dining (extract base ID without _requeue suffix)
        base_customer_id = customer_id.split('_requeue')[0].split('_unmet')[0]
        self.customers_completed_dining.add(base_customer_id)
        
        # Calculate total time in system so far
        time_in_system = self.env.now - start_time
        
        # After dining, check if there are still unmet demands (shouldn't happen, but check)
        if sum(current_demands) > 0:
            # Customer has unmet demands, return to waiting queue
            self.unmet_demand_returns += 1
            self.waiting_area.append((customer_id, current_demands, start_time))
            yield self.env.process(self.customer_process(customer_id + "_unmet", requeue_prob, current_demands, is_requeue=False))
        # Check requeue probability for getting more food
        elif random.random() < requeue_prob:
            # Check if customer's total time exceeds the max requeue time limit
            # If max_time_for_requeue is 0, it means unlimited time (no time restriction)
            if self.max_time_for_requeue > 0 and time_in_system > self.max_time_for_requeue:
                # Customer exceeded time limit, not allowed to requeue, must leave
                self.customers_denied_requeue += 1
                self.customer_total_times.append(time_in_system)
                self.completed_customers += 1
            else:
                # Customer is within time limit (or no limit), allow requeue
                self.requeue_count += 1
                # Generate new service requirement for requeue
                new_service_req = self.generate_service_requirement()
                self.env.process(self.customer_process(customer_id + "_requeue", requeue_prob, new_service_req, is_requeue=True))
        else:
            # Customer leaves the system
            self.customer_total_times.append(time_in_system)
            self.completed_customers += 1
    
    def run_simulation(self, until_time, mean_arrival_time, requeue_prob, arrival_rate, station_configs, max_time_for_requeue):
        self.setup_stations(station_configs)
        self.max_time_for_requeue = max_time_for_requeue
        
        self.env.process(self.generate_arrivals(mean_arrival_time, requeue_prob))
        
        print(f"=== Running Simulation for {until_time} minutes ===")
        print(f"λ = {arrival_rate} customers/min")
        print(f"Arrival interval = 1 / λ = {mean_arrival_time:.2f} minutes")
        print(f"Re-queue probability: {requeue_prob * 100:.1f}%")
        if max_time_for_requeue > 0:
            print(f"Max time for requeue eligibility: {max_time_for_requeue:.2f} minutes\n")
        else:
            print(f"Max time for requeue eligibility: Unlimited\n")
        
        start_real_time = time.time()
        self.env.run(until=until_time)
        end_real_time = time.time()
        
        print(f"Simulation completed in {end_real_time - start_real_time:.2f} seconds\n")
        
        self.print_results()
    
    def print_results(self):
        print("=" * 70)
        print("SIMULATION RESULTS")
        print("=" * 70)
        
        print(f"\n--- Overall Statistics ---")
        print(f"Total customers arrived: {self.total_customers}")
        print(f"Customers completed: {self.completed_customers}")
        customers_left = self.customers_left_full_queue + self.customers_left_excessive_wait
        print(f"Customers still in system: {self.total_customers - self.completed_customers - customers_left}")
        print(f"Unique customers who completed dining: {len(self.customers_completed_dining)}")
        print(f"Re-queue events (after dining): {self.requeue_count}")
        print(f"Number of customers who requeued: {self.requeue_count}")
        print(f"Returns to waiting (unmet demands): {self.unmet_demand_returns}")
        print(f"\n--- Customers Who Left ---")
        print(f"Left because waiting queue was full: {self.customers_left_full_queue}")
        print(f"Left because of excessive waiting (>20 min): {self.customers_left_excessive_wait}")
        print(f"Left because denied requeue (exceeded max time): {self.customers_denied_requeue}")
        print(f"Total customers who left: {customers_left}")
        
        if self.customer_total_times:
            avg_total_time = statistics.mean(self.customer_total_times)
            max_total_time = max(self.customer_total_times)
            min_total_time = min(self.customer_total_times)
            print(f"\nAverage time in system: {avg_total_time:.2f} minutes")
            print(f"Max time in system: {max_total_time:.2f} minutes")
            print(f"Min time in system: {min_total_time:.2f} minutes")
        
        print("\n" + "=" * 70)
        print("STATION-BY-STATION METRICS")
        print("=" * 70)

        for name, station in self.stations.items():
            print(f"\n--- {name} ---")
            print(f"Servers: {station.num_servers}")
            print(f"Customers served: {station.customers_served}")

            # WAIT TIME
            avg_wait = statistics.mean(station.wait_times) if station.wait_times else 0
            max_wait = max(station.wait_times) if station.wait_times else 0
            print(f"Average wait time: {avg_wait:.2f} minutes")
            print(f"Max wait time: {max_wait:.2f} minutes")

            # SERVICE TIME
            avg_service = statistics.mean(station.service_times) if station.service_times else 0
            print(f"Average service time: {avg_service:.2f} minutes")

            # QUEUE LENGTH (Overall)
            avg_queue = statistics.mean(station.queue_lengths) if station.queue_lengths else 0
            max_queue = max(station.queue_lengths) if station.queue_lengths else 0
            print(f"Average queue length: {avg_queue:.2f}")
            print(f"Max queue length: {max_queue}")
            
            # PER-SERVER STATISTICS (M/M/c model - servers share one queue)
            print(f"\n  Per-Server Breakdown (approximate distribution):")
            for i in range(station.num_servers):
                print(f"    Server {i+1}:")
                print(f"      Customers served: {station.server_customers_served[i]}")
            
            # Current queue status
            current_queue = len(station.resource.queue)
            current_in_service = station.resource.count
            print(f"\n  Current status (end of sim):")
            print(f"    Customers in queue: {current_queue}")
            print(f"    Customers being served: {current_in_service}")

            # UTILIZATION
            if station.service_times:
                total_service_time = sum(station.service_times)
                utilization = (total_service_time / (self.env.now * station.num_servers)) * 100
            else:
                utilization = 0
            print(f"\nServer utilization: {utilization:.2f}%")


# -------------------------------------------
#          WORKLOAD INPUT SECTION
# -------------------------------------------

WORKLOAD1_ARRIVAL_RATE = 1.0
WORKLOAD2_ARRIVAL_RATE = 5.0


def input_station_config(station_name):
    print(f"\n--- Enter config for station: {station_name} ---")
    num_servers = int(input(f"Number of servers for {station_name}: "))
    mean_service_time = float(input(f"Mean service time for {station_name} (minutes): "))
    queue_capacity_input = input(f"Total queue capacity for {station_name} (press Enter for unlimited): ").strip()
    queue_capacity = float('inf') if queue_capacity_input == "" else int(queue_capacity_input)
    return {"name": station_name, "num_servers": num_servers, "mean_service_time": mean_service_time, "queue_capacity": queue_capacity}


def input_station_config_once():
    print("\n" + "=" * 70)
    print("ENTER STATION CONFIG (Used for BOTH Workloads)")
    print("=" * 70)

    station_list = ["waiting", "appetizer", "main_course", "dessert", "dining"]
    return [input_station_config(s) for s in station_list]


def input_requeue(name):
    print("\n" + "=" * 70)
    print(f"Config for {name}")
    print("=" * 70)
    return float(input("Requeue probability (0-1): "))


# -------------------------------------------
#          UNIT TEST FOR INDIVIDUAL STATION
# -------------------------------------------

def test_single_station():
    print("\n" + "=" * 70)
    print("SINGLE STATION TEST MODE")
    print("=" * 70)
    print("Test an individual M/M/c queue to verify queueing behavior\n")
    
    # Station parameters
    num_servers = int(input("Number of servers (c): "))
    mean_service_time = float(input("Mean service time (minutes): "))
    arrival_rate = float(input("Arrival rate λ (customers/min): "))
    queue_capacity_input = input("Queue capacity (press Enter for unlimited): ").strip()
    queue_capacity = float('inf') if queue_capacity_input == "" else int(queue_capacity_input)
    sim_time = float(input("Simulation time (minutes): "))
    
    # Create environment and station
    env = simpy.Environment()
    station = ServiceStation(env, num_servers, mean_service_time, queue_capacity)
    
    # Customer arrival process
    def customer_arrivals(env, station, arrival_rate):
        customer_id = 0
        while True:
            yield env.timeout(random.expovariate(arrival_rate))
            customer_id += 1
            if station.has_available_queue():
                env.process(station.serve(f"Customer_{customer_id}"))
            else:
                print(f"Customer_{customer_id} balked (queue full)")
    
    # Start process
    env.process(customer_arrivals(env, station, arrival_rate))
    
    # Run simulation
    print(f"\n=== Running Single Station Test for {sim_time} minutes ===")
    print(f"Servers (c): {num_servers}")
    print(f"Mean service time (μ): {mean_service_time} min")
    print(f"Arrival rate (λ): {arrival_rate} customers/min")
    print(f"Traffic intensity (ρ): {(arrival_rate * mean_service_time) / num_servers:.4f}")
    print(f"Queue capacity: {queue_capacity if queue_capacity != float('inf') else 'Unlimited'}\n")
    
    start_time = time.time()
    env.run(until=sim_time)
    end_time = time.time()
    
    # Print results
    print(f"\nSimulation completed in {end_time - start_time:.4f} seconds\n")
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Customers served: {station.customers_served}")
    
    if station.wait_times:
        print(f"\nWait Times:")
        print(f"  Average: {statistics.mean(station.wait_times):.4f} minutes")
        print(f"  Max: {max(station.wait_times):.4f} minutes")
        print(f"  Min: {min(station.wait_times):.4f} minutes")
    
    if station.service_times:
        print(f"\nService Times:")
        print(f"  Average: {statistics.mean(station.service_times):.4f} minutes")
        print(f"  Theoretical mean: {mean_service_time:.4f} minutes")
    
    if station.queue_lengths:
        print(f"\nQueue Lengths:")
        print(f"  Average: {statistics.mean(station.queue_lengths):.4f}")
        print(f"  Max: {max(station.queue_lengths)}")
    
    if station.service_times:
        total_service = sum(station.service_times)
        utilization = (total_service / (sim_time * num_servers)) * 100
        print(f"\nServer Utilization: {utilization:.2f}%")
        print(f"Theoretical Utilization (ρ): {((arrival_rate * mean_service_time) / num_servers * 100):.2f}%")
    
    print("\n" + "=" * 70 + "\n")


# -------------------------------------------
#          MAIN EXECUTION
# -------------------------------------------

if __name__ == "__main__":
    random.seed(42)
    
    # Choose mode
    print("\n" + "=" * 70)
    print("BUFFET QUEUEING SIMULATION")
    print("=" * 70)
    print("1. Run Full Buffet Simulation (both workloads)")
    print("2. Test Single Station (M/M/c verification)")
    mode = input("\nSelect mode (1 or 2): ").strip()
    
    if mode == "2":
        # Run single station test
        test_single_station()
    else:
        # Run full simulation
        SIM_TIME = float(input("\nEnter SIMULATION TIME (minutes): "))

        # Input station ONCE
        station_configs = input_station_config_once()

        # --- WORKLOAD 1 ---
        requeue1 = input_requeue("Workload 1: Off-peak Hours")
        max_time_requeue1 = float(input("Max time for requeue eligibility (minutes): "))

        print("\n" + "#" * 70)
        print("# WORKLOAD 1 with λ =", WORKLOAD1_ARRIVAL_RATE)
        print("#" * 70)

        sim1 = BuffetSimulation()
        sim1.run_simulation(
            until_time=SIM_TIME,
            mean_arrival_time=1 / WORKLOAD1_ARRIVAL_RATE,
            requeue_prob=requeue1,
            arrival_rate=WORKLOAD1_ARRIVAL_RATE,
            station_configs=station_configs,
            max_time_for_requeue=max_time_requeue1
        )

        input("\nPress Enter to continue to WORKLOAD 2...\n")

        # --- WORKLOAD 2 ---
        requeue2 = input_requeue("Workload 2: Peak Hours")
        max_time_requeue2 = float(input("Max time for requeue eligibility (minutes): "))

        print("\n" + "#" * 70)
        print("# WORKLOAD 2 with λ =", WORKLOAD2_ARRIVAL_RATE)
        print("#" * 70)

        sim2 = BuffetSimulation()
        sim2.run_simulation(
            until_time=SIM_TIME,
            mean_arrival_time=1 / WORKLOAD2_ARRIVAL_RATE,
            requeue_prob=requeue2,
            arrival_rate=WORKLOAD2_ARRIVAL_RATE,
            station_configs=station_configs,
            max_time_for_requeue=max_time_requeue2
        )

        print("\nSimulation completed for all workloads!\n")
