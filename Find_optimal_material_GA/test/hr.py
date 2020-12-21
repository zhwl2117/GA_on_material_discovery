import numpy as np


np.seterr(divide='ignore', invalid='ignore')
a = np.array([1, 0, 3])
b = np.array([1, 0, 1])
c = a / b
print(np.nanmean(c), np.nanvar(c))
