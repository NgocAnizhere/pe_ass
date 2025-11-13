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
        self.station_names = {}
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
            self.station_names[config['name']] = config['name']
            print(f"Station '{config['name']}': {config['num_servers']} servers, "
                  f"service time = {config['mean_service_time']:.2f} min")
        print()
    
    def generate_arrivals(self, mean_arrival_time, station_configs, requeue_prob):
        while True:
            yield self.env.timeout(random.expovariate(1.0 / mean_arrival_time))
            
            self.customer_count += 1
            self.total_customers += 1
            customer_id = f"Customer_{self.customer_count}"
            
            self.env.process(self.customer_process(customer_id, self.stations, requeue_prob))

    def customer_process(self, customer_id, stations, requeue_prob):
        start_time = self.env.now
        first_visit = True
        
        if first_visit:
            yield self.env.process(stations['waiting'].serve(customer_id))
        
        while True:
            yield self.env.process(stations['appetizer'].serve(customer_id))
            yield self.env.process(stations['main_course'].serve(customer_id))
            yield self.env.process(stations['dessert'].serve(customer_id))
            
            yield self.env.process(stations['dining'].serve(customer_id))
            
            if random.random() < requeue_prob:
                self.requeue_count += 1
                first_visit = False
                continue
            else:
                break
        
        total_time = self.env.now - start_time
        self.customer_total_times.append(total_time)
        self.completed_customers += 1
    
    def run_simulation(self, until_time, mean_arrival_time, station_configs, requeue_prob):
        self.setup_stations(station_configs)
        
        self.env.process(self.generate_arrivals(mean_arrival_time, station_configs, requeue_prob))
        
        print(f"=== Running Simulation for {until_time} minutes ===")
        print(f"Arrival rate: 1 customer every {mean_arrival_time:.2f} minutes")
        print(f"Re-queue probability: {requeue_prob * 100:.1f}%\n")
        
        start_real_time = time.time()
        self.env.run(until=until_time)
        end_real_time = time.time()
        
        print(f"Simulation completed in {end_real_time - start_real_time:.2f} seconds\n")
        
        self.print_results()
    
    def print_results(self):
        """Prints comprehensive performance metrics for the simulation."""
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
        
        print(f"\n{'=' * 70}")
        print("STATION-BY-STATION METRICS")
        print("=" * 70)
        
        for name, station in self.stations.items():
            station_display_name = self.station_names.get(name, name)
            print(f"\n--- {station_display_name} ---")
            print(f"Servers: {station.num_servers}")
            print(f"Customers served: {station.customers_served}")
            
            if station.wait_times:
                avg_wait = statistics.mean(station.wait_times)
                max_wait = max(station.wait_times)
                print(f"Average wait time: {avg_wait:.2f} minutes")
                print(f"Max wait time: {max_wait:.2f} minutes")
            else:
                print(f"Average wait time: 0.00 minutes")
                print(f"Max wait time: 0.00 minutes")
            
            if station.service_times:
                avg_service = statistics.mean(station.service_times)
                print(f"Average service time: {avg_service:.2f} minutes")
            else:
                print(f"Average service time: 0.00 minutes")
            
            if station.queue_lengths:
                avg_queue = statistics.mean(station.queue_lengths)
                max_queue = max(station.queue_lengths)
                print(f"Average queue length: {avg_queue:.2f}")
                print(f"Max queue length: {max_queue}")
            
            if station.customers_served > 0 and station.service_times:
                total_service_time = sum(station.service_times)
                utilization = (total_service_time / (self.env.now * station.num_servers)) * 100
                print(f"Server utilization: {utilization:.2f}%")
        
        print(f"\n{'=' * 70}\n")


def get_workload_1_config():
    return {
        'name': 'Workload 1: Off-peak Hours',
        'mean_arrival_time': 1.0,
        'requeue_prob': 0.2,
        'station_configs': [
            {'name': 'waiting', 'num_servers': 2, 'mean_service_time': 0.5},
            {'name': 'appetizer', 'num_servers': 3, 'mean_service_time': 1.0},
            {'name': 'main_course', 'num_servers': 3, 'mean_service_time': 1.5},
            {'name': 'dessert', 'num_servers': 2, 'mean_service_time': 0.8},
            {'name': 'dining', 'num_servers': 20, 'mean_service_time': 15.0}
        ]
    }

def get_workload_2_config():
    return {
        'name': 'Workload 2: Peak Hours',
        'mean_arrival_time': 0.2,
        'requeue_prob': 0.15,
        'station_configs': [
            {'name': 'waiting', 'num_servers': 4, 'mean_service_time': 0.5},
            {'name': 'appetizer', 'num_servers': 5, 'mean_service_time': 1.0},
            {'name': 'main_course', 'num_servers': 5, 'mean_service_time': 1.5},
            {'name': 'dessert', 'num_servers': 4, 'mean_service_time': 0.8},
            {'name': 'dining', 'num_servers': 40, 'mean_service_time': 15.0}
        ]
    }


if __name__ == "__main__":
    random.seed(42)
    
    SIM_TIME = 480
    
    print("\n" + "=" * 70)
    print("BUFFET QUEUING SYSTEM SIMULATION")
    print("Self-service buffet system at multiple food counters")
    print("=" * 70 + "\n")
    
    print("\n" + "#" * 70)
    print("# WORKLOAD 1: OFF-PEAK HOURS")
    print("#" * 70 + "\n")
    
    workload1 = get_workload_1_config()
    sim1 = BuffetSimulation()
    sim1.run_simulation(
        until_time=SIM_TIME,
        mean_arrival_time=workload1['mean_arrival_time'],
        station_configs=workload1['station_configs'],
        requeue_prob=workload1['requeue_prob']
    )
    
    print("\n" + "=" * 70)
    input("Press Enter to continue to Workload 2...")
    print("=" * 70 + "\n")
    
    print("\n" + "#" * 70)
    print("# WORKLOAD 2: PEAK HOURS")
    print("#" * 70 + "\n")
    
    workload2 = get_workload_2_config()
    sim2 = BuffetSimulation()
    sim2.run_simulation(
        until_time=SIM_TIME,
        mean_arrival_time=workload2['mean_arrival_time'],
        station_configs=workload2['station_configs'],
        requeue_prob=workload2['requeue_prob']
    )
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE - All workloads tested")
    print("=" * 70 + "\n")