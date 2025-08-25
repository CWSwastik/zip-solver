import time

VERSIONS = 3
START = 3

for test_version in range(START, VERSIONS + 1):
    start = time.time()
    __import__(f"zip_solver_v{test_version}")
    end = time.time()

    print(f"v{test_version}", end - start, "seconds")
