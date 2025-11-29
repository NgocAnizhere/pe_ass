import simpy
import random
import statistics
import time


class ServiceStation: 
    def __init__(self, env, num_servers, mean_service_time):
        self.env = env
        self.num_servers = num_servers
        self.mean_service_time = mean_service_time
        self.resource = simpy.Resource(env, capacity=num_servers)
        
        self.wait_times = []
        self.service_times = []
        self.queue_lengths = []
        self.customers_served = 0
        
    def serve(self, customer_id):
        arrival_time = self.env.now
        queue_length = len(self.resource.queue)
        self.queue_lengths.append(queue_length)
        
        with self.resource.request() as request:
            yield request
            
            wait_time = self.env.now - arrival_time
            self.wait_times.append(wait_time)
            
            service_time = random.expovariate(1.0 / self.mean_service_time)
            self.service_times.append(service_time)
            
            yield self.env.timeout(service_time)
            
            self.customers_served += 1


class BuffetSimulation:
    def __init__(self):
        self.env = simpy.Environment()
        self.stations = {}
        self.customer_count = 0
        self.total_customers = 0
        self.completed_customers = 0
        self.requeue_count = 0
        self.customer_total_times = []

    def setup_stations(self, station_configs):
        for config in station_configs:
            station = ServiceStation(
                self.env,
                config['num_servers'],
                config['mean_service_time']
            )
            self.stations[config['name']] = station
            print(f"Station '{config['name']}': {config['num_servers']} servers, "
                  f"service time = {config['mean_service_time']:.2f} min")
        print()
    
    def generate_arrivals(self, mean_arrival_time, requeue_prob):
        while True:
            yield self.env.timeout(random.expovariate(1.0 / mean_arrival_time))
            
            self.customer_count += 1
            self.total_customers += 1
            customer_id = f"Customer_{self.customer_count}"
            
            self.env.process(self.customer_process(customer_id, requeue_prob))

    def customer_process(self, customer_id, requeue_prob):
        start_time = self.env.now
        
        # first station
        yield self.env.process(self.stations['waiting'].serve(customer_id))
        
        while True:
            yield self.env.process(self.stations['appetizer'].serve(customer_id))
            yield self.env.process(self.stations['main_course'].serve(customer_id))
            yield self.env.process(self.stations['dessert'].serve(customer_id))
            yield self.env.process(self.stations['dining'].serve(customer_id))
            
            if random.random() < requeue_prob:
                self.requeue_count += 1
                continue
            break
        
        self.customer_total_times.append(self.env.now - start_time)
        self.completed_customers += 1
    
    def run_simulation(self, until_time, mean_arrival_time, requeue_prob, arrival_rate, station_configs):
        self.setup_stations(station_configs)
        
        self.env.process(self.generate_arrivals(mean_arrival_time, requeue_prob))
        
        print(f"=== Running Simulation for {until_time} minutes ===")
        print(f"λ = {arrival_rate} customers/min")
        print(f"Arrival interval = 1 / λ = {mean_arrival_time:.2f} minutes")
        print(f"Re-queue probability: {requeue_prob * 100:.1f}%\n")
        
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
        print(f"Customers still in system: {self.total_customers - self.completed_customers}")
        print(f"Re-queue events: {self.requeue_count}")
        
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

            # QUEUE LENGTH
            avg_queue = statistics.mean(station.queue_lengths) if station.queue_lengths else 0
            max_queue = max(station.queue_lengths) if station.queue_lengths else 0
            print(f"Average queue length: {avg_queue:.2f}")
            print(f"Max queue length: {max_queue}")

            # UTILIZATION
            if station.service_times:
                total_service_time = sum(station.service_times)
                utilization = (total_service_time / (self.env.now * station.num_servers)) * 100
            else:
                utilization = 0
            print(f"Server utilization: {utilization:.2f}%")


# -------------------------------------------
#          WORKLOAD INPUT SECTION
# -------------------------------------------

WORKLOAD1_ARRIVAL_RATE = 1.0
WORKLOAD2_ARRIVAL_RATE = 5.0


def input_station_config(station_name):
    print(f"\n--- Enter config for station: {station_name} ---")
    num_servers = int(input(f"Number of servers for {station_name}: "))
    mean_service_time = float(input(f"Mean service time for {station_name} (minutes): "))
    return {"name": station_name, "num_servers": num_servers, "mean_service_time": mean_service_time}


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


if __name__ == "__main__":
    random.seed(42)

    SIM_TIME = float(input("Enter SIMULATION TIME (minutes): "))

    # Input station ONCE
    station_configs = input_station_config_once()

    # --- WORKLOAD 1 ---
    requeue1 = input_requeue("Workload 1: Off-peak Hours")

    print("\n" + "#" * 70)
    print("# WORKLOAD 1 with λ =", WORKLOAD1_ARRIVAL_RATE)
    print("#" * 70)

    sim1 = BuffetSimulation()
    sim1.run_simulation(
        until_time=SIM_TIME,
        mean_arrival_time=1 / WORKLOAD1_ARRIVAL_RATE,
        requeue_prob=requeue1,
        arrival_rate=WORKLOAD1_ARRIVAL_RATE,
        station_configs=station_configs
    )

    input("\nPress Enter to continue to WORKLOAD 2...\n")

    # --- WORKLOAD 2 ---
    requeue2 = input_requeue("Workload 2: Peak Hours")

    print("\n" + "#" * 70)
    print("# WORKLOAD 2 with λ =", WORKLOAD2_ARRIVAL_RATE)
    print("#" * 70)

    sim2 = BuffetSimulation()
    sim2.run_simulation(
        until_time=SIM_TIME,
        mean_arrival_time=1 / WORKLOAD2_ARRIVAL_RATE,
        requeue_prob=requeue2,
        arrival_rate=WORKLOAD2_ARRIVAL_RATE,
        station_configs=station_configs
    )

    print("\nSimulation completed for all workloads!\n")
