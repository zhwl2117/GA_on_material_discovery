from math import modf


def distribute(total, distribution):
    leftover = 0.0
    distributed_total = []
    for weight in distribution:
        weight = float(weight)
        leftover, weighted_value = modf(weight * total + leftover)
        distributed_total.append(weighted_value)
    distributed_total[-1] = round(distributed_total[-1] + leftover)  # mitigate round off errors
    distributed_total[0], distributed_total[-1] = distributed_total[-1], distributed_total[0]
    return distributed_total


d = distribute(11, [.25, .25, .25, .25])
print(d)
