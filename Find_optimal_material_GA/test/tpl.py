

t = (1, 2.2)

print('No.{}, HR: {}'.format(t[0], t[1]))

d = {1: (1.5, 1.6), 2: (2.5, 2.6)}

while d:
    for i in list(d.keys()):
        del d[i]

print(d)
