import rdkit
import rdkit.Chem as Chem
from rdkit.Chem import Draw
import copy
from rdkit import RDLogger

from chemutils import get_clique_mol, tree_decomp, get_mol, get_smiles, set_atommap, enum_assemble, decode_stereo


def get_slots(smiles):
    """
    get atoms of a molecular from smiles
    :param smiles: molecular sequence
    :return: a list of atoms' proprieties: element type, formal charge, total hydrogen atoms in the molecular
    """
    mol = Chem.MolFromSmiles(smiles)
    return [(atom.GetSymbol(), atom.GetFormalCharge(), atom.GetTotalNumHs()) for atom in mol.GetAtoms()]


class Vocab(object):  # 应该是词汇库，但用法暂时不详，待后续补充

    def __init__(self, smiles_list):
        self.vocab = smiles_list
        self.vmap = {x: i for i, x in enumerate(self.vocab)}
        self.slots = [get_slots(smiles) for smiles in self.vocab]

    def get_index(self, smiles):
        return self.vmap[smiles]

    def get_smiles(self, idx):
        return self.vocab[idx]

    def get_slots(self, idx):
        return copy.deepcopy(self.slots[idx])

    def size(self):
        return len(self.vocab)


class MolTreeNode(object):
    """
    Converting a molecular to a tree. A tree node means one of the cliques
    """
    def __init__(self, smiles, clique=None):
        if clique is None:
            clique = []
        self.smiles = smiles
        self.mol = get_mol(self.smiles)

        self.clique = [x for x in clique]  # copy
        self.neighbors = []
        self.is_leaf = None
        self.nid = None
        self.label = None
        self.label_mol = None
        self.cands = None
        self.cand_mols = None
        self.idx = None
        self.wid = None

    def add_neighbor(self, nei_node):
        """
        Add a neighbor to the neighbors list
        :param nei_node: a neighbor clique tree node
        :return:
        """
        self.neighbors.append(nei_node)

    def recover(self, original_mol):
        clique = []
        clique.extend(self.clique)
        if not self.is_leaf:
            for cidx in self.clique:
                original_mol.GetAtomWithIdx(cidx).SetAtomMapNum(self.nid)  # SetAtomMapNum设置原子对应的编号，这里为叶节点编号

        for nei_node in self.neighbors:
            clique.extend(nei_node.clique)
            if nei_node.is_leaf:  # Leaf node, no need to mark
                continue
            for cidx in nei_node.clique:
                # allow singleton node override the atom mapping
                if cidx not in self.clique or len(nei_node.clique) == 1:
                    atom = original_mol.GetAtomWithIdx(cidx)
                    atom.SetAtomMapNum(nei_node.nid)

        clique = list(set(clique))
        label_mol = get_clique_mol(original_mol, clique)
        self.label = Chem.MolToSmiles(Chem.MolFromSmiles(get_smiles(label_mol)))
        self.label_mol = get_mol(self.label)

        for cidx in clique:
            original_mol.GetAtomWithIdx(cidx).SetAtomMapNum(0)

        return self.label

    def assemble(self):
        neighbors = [nei for nei in self.neighbors if nei.mol.GetNumAtoms() > 1]
        neighbors = sorted(neighbors, key=lambda x: x.mol.GetNumAtoms(), reverse=True)
        singletons = [nei for nei in self.neighbors if nei.mol.GetNumAtoms() == 1]
        neighbors = singletons + neighbors

        cands = enum_assemble(self, neighbors)
        if len(cands) > 0:
            self.cands, self.cand_mols, _ = zip(*cands)
            self.cands = list(self.cands)
            self.cand_mols = list(self.cand_mols)
        else:
            self.cands = []
            self.cand_mols = []


class MolTree(object):

    def __init__(self, smiles):
        self.smiles = smiles
        self.mol = get_mol(smiles)

        # Stereo Generation
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return
        self.smiles3D = Chem.MolToSmiles(mol, isomericSmiles=True)
        self.smiles2D = Chem.MolToSmiles(mol)
        self.stereo_cands = decode_stereo(self.smiles2D)

        cliques, edges = tree_decomp(self.mol)
        self.nodes = []
        root = 0
        for i, c in enumerate(cliques):
            cmol = get_clique_mol(self.mol, c)
            node = MolTreeNode(get_smiles(cmol), c)
            self.nodes.append(node)
            if min(c) == 0:
                root = i

        for x, y in edges:
            self.nodes[x].add_neighbor(self.nodes[y])
            self.nodes[y].add_neighbor(self.nodes[x])

        if root > 0:
            self.nodes[0], self.nodes[root] = self.nodes[root], self.nodes[0]

        for i, node in enumerate(self.nodes):
            node.nid = i + 1
            if len(node.neighbors) > 1:  # Leaf node mol is not marked
                set_atommap(node.mol, node.nid)
            node.is_leaf = (len(node.neighbors) == 1)

    def size(self):
        return len(self.nodes)

    def recover(self):
        for node in self.nodes:
            node.recover(self.mol)

    def assemble(self):
        for node in self.nodes:
            node.assemble()


if __name__ == "__main__":
    lg = RDLogger.logger()
    lg.setLevel(rdkit.RDLogger.CRITICAL)

    c_set = set()
    c_dic = {}
    fail_smiles = []
    with open('./data/oled_list.txt', 'r') as f:
        for i, line in enumerate(f.readlines()):
            smile = line.split()[0]
            # print(smile)
            mol_tree = MolTree(smile)
            if mol_tree.mol is None:
                print('fail to create mol tree: ', 'No.', str(i), smile)
                fail_smiles.append(smile)
                continue
            for cli in mol_tree.nodes:
                c_set.add(cli.smiles)
        for cli in c_set:
            print(cli)
            c_dic[cli] = Chem.MolFromSmiles(cli)
    print('corpus size: ',  str(len(c_set)))
    print('total fail smiles: ', str(len(fail_smiles)))
    '''
    img_path = r'./img/corpus_img/'
    for cli in list(c_dic.keys()):
        img = Draw.MolToImage(c_dic[cli],  molsPerRow=5, subImgSize=(300, 300))
        img.save(img_path + cli + '.png')
    '''
    txt_path = r'./data/oled_vocab.txt'
    with open(txt_path, 'w') as f:
        for cli in c_set:
            f.write(cli+'\r\n')
