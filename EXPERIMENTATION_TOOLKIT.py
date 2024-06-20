# When changing the duration for testing, remember to delete previous data
import EVERYTHING_experiment as experiment
import random
import time
import random

def run_experiments(duration, num_rows, filename, num_rabbits, num_foxes, rabbit_range = (2, 100), fox_range = (2, 100)):
        # Generate each row using the generate() function
        for i in range(num_rows):
            num_rabbits = random.randint(rabbit_range[0], rabbit_range[1])
            num_foxes = random.randint(fox_range[0], fox_range[1])
            try:
                with open(filename, 'a') as file:
                    # Generate the row as a list of tuples
                    sim_start = time.time()
                    row = experiment.run_simulation(num_rabbits, num_foxes, duration)
                    sim_end = time.time()
                    # Format each tuple into a string "[x, y]"
                    formatted_row = [f"[{x}, {y}]" for x, y in row]
                    # Join all entries into a single string with commas and write to file
                    formatted_row_str = ', '.join(formatted_row)
                    file.write(f"\"{formatted_row_str}\"\n")

                    total_estimated_time = (sim_end - sim_start) * (num_rows - i) 
                    print(f"Progress: {i}th run. Estimated time left: {total_estimated_time/60:.2f} minutes")
            except:
                print("Error with this simulation!")

# Example use:
#run_experiments(200, 500, 'final_data.csv', 20, 3)



# Random data generator for testing the neural network
def generate_random_data(num_entries, num_rows, filename):
    # Open the file for writing
    with open(filename, 'w') as file:
        # Generate each row
        for i in range(num_rows):
            # Generate each entry in the row as a list of 3 integers following a simple pattern
            row = [
                f"[{random.randint(1, 69)}, {random.randint(5, 80)}]"
                for _ in range(num_entries)
            ]
            print(row)
            # Join all entries into a single string with commas and write to file
            formatted_row = ', '.join(row)
            file.write(f"\"{formatted_row}\"\n")

# Example usage:
# generate_random_data(20, 30, 'fake_data.csv')