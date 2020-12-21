from abc import abstractmethod, ABCMeta
from collections import deque
from bidict import bidict
import numpy as np
import re


class File:
    def __init__(self, input_file, heteroatom_list):
        self._file_name = input_file
        self._heteroatom_loc = []
        with open(self._file_name, 'r') as f:
            tag = '0 1'
            flag = False
            idx = 0
            for line in f:
                if not flag:
                    if tag in line:
                        flag = True
                else:
                    if line == '\n':
                        break
                    if line[1] in heteroatom_list:
                        self._heteroatom_loc.append(idx)
                idx += 1

    def generate_file(self, file_name, heteroatom_sequence):
        text = ''
        heteroatom_queue = deque(heteroatom_sequence)
        with open(self._file_name, 'r') as f:
            for idx, line in enumerate(f.readlines()):
                if idx == 2:
                    regex = r'bnb-\w*.chk'
                    idx = file_name.find('individual')
                    short_name = file_name[idx:]
                    line = re.sub(regex, short_name, line, 1)
                    line = line.replace('.gif', '.chk')
                if idx in self._heteroatom_loc:
                    line = line[0:1] + heteroatom_queue.popleft() + line[2:]
                text += line
        with open(file_name, 'w') as f:
            f.write(text)

    def get_sequence_len(self):
        return len(self._heteroatom_loc)


class Coder(metaclass=ABCMeta):
    def __init__(self, heteroatom_list):
        self.heteroatom_list = heteroatom_list

    @abstractmethod
    def encode(self, heteroatom_code):
        pass

    @abstractmethod
    def decode(self, int_code):
        pass

    @abstractmethod
    def generate_population(self, sequence_len, population_size):
        pass


class IntCoder(Coder):
    def __init__(self, heteroatom_list):
        super().__init__(heteroatom_list)
        self.dict = {}
        for i, v in enumerate(self.heteroatom_list):
            self.dict[v] = i
        self.dict = bidict(self.dict)

    def encode(self, heteroatom_code):
        int_code = ''
        heteroatom_list = list(heteroatom_code)
        for h in heteroatom_list:
            int_code += str(self.dict[h])
        return int_code

    def decode(self, int_code):
        heteroatom_code = ''
        int_list = [int(i) for i in list(int_code)]
        for i in int_list:
            heteroatom_code += self.dict.inv[i]
        return heteroatom_code

    def generate_population(self, sequence_len, population_size):
        initial_population = []
        for i in range(population_size):
            individual = np.random.randint(0, len(self.heteroatom_list), sequence_len)
            initial_population.append(individual)
        return initial_population

    def random_mutation(self, current_code):
        select_sequence = list(np.arange(current_code))
        select_sequence.append(np.arange(current_code, len(self.heteroatom_list)))
        idx = np.random.randint(0, len(select_sequence), 1)[0]
        return select_sequence[idx]


class Code:
    def __init__(self, input_file_freq, input_file_opt, heteroatom_list, code_mode):
        self.file_freq = File(input_file_freq, heteroatom_list)
        self.file_opt = File(input_file_opt, heteroatom_list)
        self.coder = IntCoder(heteroatom_list)

    def generate_file(self, epoch, individual, int_code):
        heteroatom_code = self.coder.decode(int_code)
        file_freq = 'generations/generation{}/individual_freq{}.gif'.format(epoch, individual)
        file_opt = 'generations/generation{}/individual_opt{}.gif'.format(epoch, individual)
        self.file_freq.generate_file(file_freq, heteroatom_code)
        self.file_opt.generate_file(file_opt, heteroatom_code)

    def get_sequence_len(self):
        return self.file_freq.get_sequence_len()

    def generate_population(self, population_size):
        return self.coder.generate_population(self.get_sequence_len(), population_size)

    def random_mutation(self, current_code):
        return self.coder.random_mutation(current_code)


if __name__ == '__main__':
    path = r'C:\Users\17998\Desktop\final\Optimal_materials_luminary\data\gaussian_data\bnb2\out'
    freq_file = path + r'\bnb-freq.txt'
    opt_file = path + r'\bnb-sopt-freq.txt'
    hetero_list = ['B', 'N']
    code = Code(freq_file, opt_file, hetero_list, 'binary')
    print(code.generate_population(2))
