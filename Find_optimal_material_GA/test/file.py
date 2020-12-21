import time


with open('../test.txt', 'w') as f:
    start_time = time.time()
    for _ in range(1000):
        f.write('Hello g09!\n')
    end_time = time.time()
    elapse = end_time - start_time
    print(elapse)

with open('../test.txt', 'r+') as f:
    line = f.readline()
    idx = line.rfind('g09')
    new_line = line.replace('g09', 'g16')
    f.seek(0)
    f.write(new_line)
