# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from GA import GenePopulation


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    freq_file = 'bnb_freq.txt'
    opt_file = 'bnb_opt.txt'
    hetoro_list = ['B', 'N']
    ga = GenePopulation(freq_file, opt_file, hetoro_list, 2, [.25, .25, .25, .25])
    ga.iterate()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
