import os
import numpy as np
import subprocess
import time
import HR


class Chemistry:
    def __init__(self, population_size, cal_mode='gaussian_dushin'):
        self._gaussian_setting()
        self._dushin_setting()
        self.ocra_setting()
        self._cal_mode = cal_mode
        self.population_size = population_size

    @staticmethod
    def _gaussian_setting():
        os.system('export g09root=/share/apps/g09.D01')
        os.system('export GAUSS_SCRDIR=/home/zhangst/wlzhong/gaussian/tmp')
        os.system('source $g09root/g09/bsd/g09.profile')

    @staticmethod
    def _dushin_setting():
        os.system('export PATH=$PATH:/home/zhangst/wlzhong/dushin')

    @staticmethod
    def ocra_setting():
        pass

    def cal_fitness(self, epoch) -> [(int, float)]:
        # dir_path = '/generations/generation{}'.format(epoch)
        os.chdir('generations/generation{}'.format(epoch))
        fitness = []
        if self._cal_mode == 'gaussian_dushin':
            self.to_log_message('using gaussian/dushin method')
            fitness = self.cal_by_gaussian_dushin()
            os.chdir('../..')
        # sort fitness according to its HR
        sorted(fitness, key=lambda item: item[1])
        return fitness

    def cal_by_gaussian_dushin(self):
        self.to_log_message('starting to calculate by gaussian')
        id_list = self._gaussian()
        self.to_log_message('ready to calculate by dushin')
        dushin_dir = self._dushin(id_list)
        fitness = dushin_dir.items()
        return fitness

    def _gaussian(self):
        shell_list = {}
        file_name = 'individual'
        for i in range(self.population_size):
            freq_cmd = 'g16 ' + file_name + '_freq{}.gif'.format(i)
            opt_cmd = 'g16 ' + file_name + '_opt{}.gif'.format(i)
            self.to_log_message('executing cmd:\n' + freq_cmd +
                                '\n' + opt_cmd)
            freq_shell = Shell(freq_cmd)
            opt_shell = Shell(opt_cmd)
            freq_shell.run_background()
            opt_shell.run_background()
            shell_list[i] = (freq_shell, opt_shell)
        return shell_list

    def _dushin(self, id_list: {}):
        dushin_dic = {}
        while id_list:
            done = False
            for i in list(id_list.keys()):
                if id_list[i][0].is_finished() and id_list[i][1].is_finished():
                    # os.chdir(dir_path)
                    self.to_log_message('individual {} is done by gaussian!'.format(i))
                    individual_freq = 'individual_freq{}.log'.format(i)
                    individual_opt = 'individual_opt{}.log'.format(i)
                    self.change_to_09(individual_freq)
                    self.change_to_09(individual_opt)
                    freq_shell = Shell('formchk individual_freq{}.chk'.format(i))
                    opt_shell = Shell('formchk individual_opt{}.chk'.format(i))
                    freq_shell.run_background()
                    opt_shell.run_background()
                    self.to_log_message('start to create fchk files')
                    self.write_dushin_dat(i)
                    self.to_log_message('start to write dushin.dat file')
                    while not freq_shell.is_finished() or not opt_shell.is_finished():
                        continue
                    self.to_log_message('fchk files created successfully')
                    os.system('dushin')
                    self.to_log_message('successfully calculated by dushin')
                    hr = self.cal_HR(i)
                    dushin_dic[i] = hr
                    del id_list[i]
                    done = True
            if done:
                self.to_log_message('finished some calculation of HR!')
            else:
                self.to_log_message('none of the individuals is finished by gaussian!\n'
                                    'the main program will check again 1 hour later')
                time.sleep(3600)
        return dushin_dic

    @staticmethod
    def write_dushin_dat(individual):
        with open('dushin.dat', 'w') as f:
            f.write('1 2\n')
            f.write('.\n\n')
            f.write('2 1 \'bnb_freq\' \'individual_freq{}.log\'\n'.format(individual))
            f.write('0 1 \'bnb_opt\' \'individual_opt{}.log\'\n'.format(individual))
        time.sleep(0.1)

    @staticmethod
    def to_log_message(message):
        log = r'../../log.txt'
        with open(log, 'a') as f:
            f.write('#######################\n')
            f.write(message + '\n')
        time.sleep(0.1)

    @staticmethod
    def change_to_09(file):
        with open(file, 'r+') as f:
            line = f.readline()
            new_line = line.replace('g16', 'g09')
            f.seek(0)
            f.write(new_line)

    @staticmethod
    def cal_HR(i):
        while not (os.path.isfile('dushin.out')):
            continue
        hr_list = HR.cal_HR('dushin.out')
        HR.save_HR(hr_list, 'HR_individual{}.txt'.format(i))
        return np.nanmean(hr_list)  # , np.nanvar(hr_list)

    def gaussian_amend(self):
        pass

    @staticmethod
    def _proc_finish(proc_id):
        status = subprocess.check_output(['ps', str(proc_id)], shell=False)
        return status == ''

    def cal_by_ocra(self, dir_path) -> []:
        pass


class Shell:
    def __init__(self, cmd):
        self.cmd = cmd
        self.ret_code = None
        self.ret_info = None
        self.err_info = None
        self._process = None

    def run_background(self):
        self._process = subprocess.Popen(self.cmd, shell=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def is_finished(self):
        ret_code = self._process.poll()
        if ret_code is None:
            return False
        else:
            return True


if __name__ == '__main__':
    chem = Chemistry(1)
    print(chem.cal_fitness(1))
