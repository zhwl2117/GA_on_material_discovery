import numpy as np
from pandas import DataFrame

path = r'C:\Users\17998\Desktop\final\Optimal_materials_luminary\data\gaussian_data' \
           r'\gav1\generation0\generation0\dushin3.out'


def cal_HR(dir_path):
    np.seterr(divide='ignore', invalid='ignore')
    flag = False
    tag = 'Displacement: in terms of nc of 1 THEN of nc of 2'
    HR_list = []
    with open(dir_path, 'r') as f:
        for line in f:
            if not flag:
                if tag in line:
                    flag = True
            else:
                if line == '\n':
                    continue
                freq_pos = line.rfind('freq=')
                if freq_pos == -1:
                    break
                q_pos = line.rfind('Q=')
                freq = np.array(float(line[freq_pos+5: q_pos].strip()))
                lam_pos = line.rfind('lam=')
                lam = np.array(float(line[lam_pos+4:].strip()))
                HR_list.append(np.array([freq, lam, 0]))
    HR_list = np.array(HR_list)
    return HR_list[:, 1] / 219474.6363 * 2625500 / 6.02214179e23 / (HR_list[:, 0] * 29979245800 * 6.6260696e-34)


def save_HR(HR_list, file_name):
    df = DataFrame(HR_list)
    df.to_csv(file_name, index=False)


if __name__ == '__main__':
    hr_list = cal_HR(path)
    file = r'C:\Users\17998\Desktop\final\Optimal_materials_luminary\data\gaussian_data' \
           r'\gav1\generation0\generation0\HR3.csv'
    save_HR(hr_list, file)
