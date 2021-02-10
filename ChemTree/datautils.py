import torch
import re
from torch._six import container_abcs, string_classes, int_classes
from torch.utils.data import Dataset
from mol_tree import MolTree
import numpy as np

_use_shared_memory = False
r"""Whether to use shared memory in default_collate"""

np_str_obj_array_pattern = re.compile(r'[SaUO]')

error_msg_fmt = "batch must contain tensors, numbers, dicts or lists; found {}"

numpy_type_map = {
    'float64': torch.DoubleTensor,
    'float32': torch.FloatTensor,
    'float16': torch.HalfTensor,
    'int64': torch.LongTensor,
    'int32': torch.IntTensor,
    'int16': torch.ShortTensor,
    'int8': torch.CharTensor,
    'uint8': torch.ByteTensor,
}


def collate_fn(batch):
    """
     collate_fn (callable, optional): merges a list of samples to form a mini-batch.
     该函数参考touch的default_collate函数，也是DataLoader的默认的校对方法，当batch中含有None等数据时，
     默认的default_collate校队方法会出现错误
     一种的解决方法是：
     判断batch中image是否为None,如果为None，则在原来的batch中清除掉，这样就可以在迭代中避免出错了
    :param batch:
    :return:
    """
    r"""Puts each data field into a tensor with outer dimension batch size"""
    # 这里添加：判断image是否为None,如果为None，则在原来的batch中清除掉，这样就可以在迭代中避免出错了
    if isinstance(batch, list):
        batch = [mol for mol in batch if mol is not None]
    if batch == []:
        return (None, None)

    elem_type = type(batch[0])
    if isinstance(batch[0], torch.Tensor):
        out = None
        if _use_shared_memory:
            # If we're in a background process, concatenate directly into a
            # shared memory tensor to avoid an extra copy
            numel = sum([x.numel() for x in batch])
            storage = batch[0].storage()._new_shared(numel)
            out = batch[0].new(storage)
        return torch.stack(batch, 0, out=out)
    elif elem_type.__module__ == 'numpy' and elem_type.__name__ != 'str_' \
            and elem_type.__name__ != 'string_':
        elem = batch[0]
        if elem_type.__name__ == 'ndarray':
            # array of string classes and object
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError(error_msg_fmt.format(elem.dtype))

            return collate_fn([torch.from_numpy(b) for b in batch])
        if elem.shape == ():  # scalars
            py_type = float if elem.dtype.name.startswith('float') else int
            return numpy_type_map[elem.dtype.name](list(map(py_type, batch)))
    elif isinstance(batch[0], MolTree):
        return batch
    elif isinstance(batch[0], float):
        return torch.tensor(batch, dtype=torch.float64)
    elif isinstance(batch[0], int_classes):
        return torch.tensor(batch)
    elif isinstance(batch[0], string_classes):
        return batch
    elif isinstance(batch[0], container_abcs.Mapping):
        return {key: collate_fn([d[key] for d in batch]) for key in batch[0]}
    elif isinstance(batch[0], tuple) and hasattr(batch[0], '_fields'):  # namedtuple
        return type(batch[0])(*(collate_fn(samples) for samples in zip(*batch)))
    elif isinstance(batch[0], container_abcs.Sequence):
        transposed = zip(*batch)  # ok
        return [collate_fn(samples) for samples in transposed]

    raise TypeError((error_msg_fmt.format(type(batch[0]))))


class MoleculeDataset(Dataset):

    def __init__(self, data_file):
        with open(data_file) as f:
            self.data = [line.strip("\r\n ").split()[0] for line in f]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        smiles = self.data[item]
        mol_tree = MolTree(smiles)
        if mol_tree.mol is None:
            return None
        mol_tree.recover()
        mol_tree.assemble()
        return mol_tree


class PropDataset(Dataset):

    def __init__(self, data_file, prop_file):
        self.prop_data = np.loadtxt(prop_file)
        with open(data_file) as f:
            self.data = [line.strip("\r\n ").split()[0] for line in f]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        smiles = self.data[idx]
        mol_tree = MolTree(smiles)
        mol_tree.recover()
        mol_tree.assemble()
        return mol_tree, self.prop_data[idx]
