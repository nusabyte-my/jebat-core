import time

def measure_execution_time(func):
    start_time = time.time()
    result = func()
    end_time = time.time()
    execution_time = end_time - start_time
    return execution_time

if __name__ == '__main__':
    def my_function():
        time.sleep(1)
    
    execution_time = measure_execution_time(my_function)
    print(f"Execution time: {execution_time} seconds")