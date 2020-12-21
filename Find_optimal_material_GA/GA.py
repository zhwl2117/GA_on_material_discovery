import os
import numpy as np
import time
from math import modf
from data_process import Code
from chemistry import Chemistry


class GenePopulation:
    def __init__(self, file_name_preq, file_name_opt, heteroatom_list, epochs, percents, population_size=4,
                 code_mode='binary'):
        self.population_size = population_size
        self.code = Code(file_name_preq, file_name_opt, heteroatom_list, code_mode)
        self.epochs = epochs
        self.percents = percents
        self.percents = self.distribute()
        self.population = self.code.generate_population(self.population_size)
        self.current_epoch = 0
        self.heteroatom_list = heteroatom_list
        self.chemistry = Chemistry(self.population_size)
        self._write_file()
        self._write_head_lines()

    def _write_file(self):
        os.makedirs('generations/generation{}'.format(self.current_epoch))
        for i, v in enumerate(self.population):
            self.code.generate_file(self.current_epoch, i, v)
        time.sleep(0.1)

    def _write_head_lines(self):
        with open('log.txt', 'w') as f:
            f.write('***********************************************\n')
            f.write('Genetic Algorithm in search of optimal material\n')
            f.write('***********************************************\n')
            f.write('initial population size: {}, maximum epoch: {}\n'.format(self.population_size, self.epochs))
            f.write('***********************************************\n')
            f.write('heteroatom_list: {}\n'.format(self.heteroatom_list))
            f.write('***********************************************\n')
            f.write('population distribution percent:\n fit: {}; switch: {}; mutate: {}; random: {}\n'.
                    format(self.percents[0], self.percents[1], self.percents[2], self.percents[3]))
            f.write('***********************************************\n')
        time.sleep(0.1)

    def _write_fitness(self, cal_results):
        with open('log.txt', 'a') as f:
            f.write('***********************************************\n')
            f.writelines(['\n', 'epoch: {}\n'.format(self.current_epoch)])
            for i, result in enumerate(cal_results):
                f.write('No.{}  individual {}, fitness {}\n'.format(i, result[0], result[1]))
            f.write('***********************************************\n')
        time.sleep(0.1)

    def cal_fitness(self, percent):
        self.write_message('starting to cal fitness')
        cal_results = self.chemistry.cal_fitness(self.current_epoch)
        self._write_fitness(cal_results)
        new_population = []
        for i in range(int(percent), 0, -1):
            idx = list(cal_results.items())[0]
            new_population.append(self.population[idx])
        self.population = new_population

    def switch(self, percent):
        self.write_message('starting to switch')
        new_population_list = []
        for i in range(int(percent)):
            random_idx = np.random.randint(0, len(self.population), 2)
            rand_point = np.random.randint(0, self.code.get_sequence_len(), 1)
            new_individual = self.population[random_idx[0]]
            new_individual[rand_point[0]:] = self.population[random_idx[1]][rand_point[0]:]
            new_population_list.append(new_individual)
        self.population.extend(new_population_list)

    def mutate(self, percent):
        self.write_message('starting to mutate')
        new_population_list = []
        for i in range(int(percent)):
            new_individual = self.population[
                np.random.randint(0, len(self.population), 1)[0]]
            mutate_idx = np.random.randint(0, self.code.get_sequence_len(), 1)
            new_individual[mutate_idx[0]] = self.code.random_mutation(new_individual[mutate_idx[0]])
            new_population_list.append(new_individual)
        self.population.extend(new_population_list)

    def random(self, percent):
        self.write_message('starting to random')
        new_population = self.code.generate_population(int(percent))
        self.population.extend(new_population)

    def iterate(self):
        while self.current_epoch <= self.epochs:
            self.cal_fitness(self.percents[0])
            self.switch(self.percents[1])
            self.mutate(self.percents[2])
            self.random(self.percents[3])
            self.current_epoch += 1
            self._write_file()

    @staticmethod
    def write_message(message):
        with open('log.txt', 'a') as f:
            f.write('***********************************************\n')
            f.write(message + '\n')
        time.sleep(0.1)

    def distribute(self):
        leftover = 0.0
        distributed_total = []
        for weight in self.percents:
            weight = float(weight)
            leftover, weighted_value = modf(weight * self.population_size + leftover)
            distributed_total.append(weighted_value)
        distributed_total[-1] = round(distributed_total[-1] + leftover)  # mitigate round off errors
        distributed_total[0], distributed_total[-1] = distributed_total[-1], distributed_total[0]
        return distributed_total
