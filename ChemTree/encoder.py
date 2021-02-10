import torch
import torch.nn as nn
from collections import deque
from nnutils import create_var, GRU

MAX_NB = 8


class TreeEncoder(nn.Module):

    def __init__(self, vocab, hidden_size, embedding=None):
        super(TreeEncoder, self).__init__()
        self.hidden_size = hidden_size
        self.vocab_size = vocab.size()
        self.vocab = vocab

        # 词向量的嵌入，把每一个结点（模块）表示成一个向量
        if embedding is None:
            self.embedding = nn.Embedding(self.vocab_size, hidden_size)
        else:
            self.embedding = embedding

        self.W_z = nn.Linear(2 * hidden_size, hidden_size)
        self.W_r = nn.Linear(hidden_size, hidden_size, bias=False)
        self.U_r = nn.Linear(hidden_size, hidden_size)
        self.W_h = nn.Linear(2 * hidden_size, hidden_size)
        self.W = nn.Linear(2 * hidden_size, hidden_size)

    def forward(self, root_batch):
        orders = []  # orders: list(list), 每个子列表代表一个根层次遍历的结果
        for root in root_batch:
            # oder: list(list), 一个列表分为两部分，
            # 一个是自底向上的顺序，每个子列表中包含该层的结点及其父节点
            # 一个是自顶向下的顺序，每个子列表中包含该层的结点及其子节点
            order = get_prop_order(root)
            orders.append(order)

        h = {}
        max_depth = max([len(order) for order in orders])
        padding = create_var(torch.zeros(self.hidden_size), False)

        for t in range(max_depth):
            prop_list = []
            for order in orders:
                if len(order) > t:  # 确保这棵树有第t层
                    prop_list.extend(order[t])  # 第t层的层次列表加入到prop_list

            cur_x = []
            cur_h_nei = []
            for node_x, node_y in prop_list:
                x, y = node_x.idx, node_y.idx  # 结点编号
                cur_x.append(node_x.wid)  # 结点类型编号

                h_nei = []
                for node_z in node_x.neighbors:
                    z = node_z.idx
                    if z == y:
                        continue
                    # h_nei：结点x除y以外的邻居，即与其相邻的结点
                    h_nei.append(h[(z, x)])

                # 如果邻居数量达不到最大值，则用padding的变量填充
                pad_len = MAX_NB - len(h_nei)
                h_nei.extend([padding] * pad_len)
                cur_h_nei.extend(h_nei)

            cur_x = create_var(torch.LongTensor(cur_x))
            cur_x = self.embedding(cur_x)  # 从这里开始，标签转化为了向量, cur_x.size = (len(prop_list), hidden_size)
            cur_h_nei = torch.cat(cur_h_nei, dim=0).view(-1, MAX_NB, self.hidden_size)
            # cur_nei_h.size = (len(prop_list), MAX_NB, hidden_size)

            new_h = GRU(cur_x, cur_h_nei, self.W_z, self.W_r, self.U_r, self.W_h)
            for i, m in enumerate(prop_list):
                x, y = m[0].idx, m[1].idx
                h[(x, y)] = new_h[i]

        # node aggregate
        root_vecs = node_aggregate(root_batch, h, self.embedding, self.W)
        return h, root_vecs


# 从根开始进行层次遍历，每一层都是一个列表
def get_prop_order(root):
    queue = deque([root])
    visited = {root.idx}
    root.depth = 0
    order1, order2 = [], []
    while len(queue) > 0:
        x = queue.popleft()
        for y in x.neighbors:
            if y.idx not in visited:
                queue.append(y)
                visited.add(y.idx)
                y.depth = x.depth + 1
                if y.depth > len(order1):
                    order1.append([])
                    order2.append([])
                order1[y.depth - 1].append((x, y))
                order2[y.depth - 1].append((y, x))
    order = order2[::-1] + order1
    return order


def node_aggregate(nodes, h, embedding, W):
    x_idx = []
    h_nei = []
    hidden_size = embedding.embedding_dim
    padding = create_var(torch.zeros(hidden_size), False)

    for node_x in nodes:
        x_idx.append(node_x.wid)
        nei = [h[(node_y.idx, node_x.idx)] for node_y in node_x.neighbors]
        pad_len = MAX_NB - len(nei)
        nei.extend([padding] * pad_len)
        h_nei.extend(nei)

    h_nei = torch.cat(h_nei, dim=0).view(-1, MAX_NB, hidden_size)  # h_nei.size = (len(nodes), MAX_NB, hidden_size)
    sum_h_nei = h_nei.sum(dim=1)  # sum_h_nei.size = (len(nodes), hidden_size)
    x_vec = create_var(torch.LongTensor(x_idx))
    x_vec = embedding(x_vec)  # x_vec.size = (len(nodes), hidden_size)
    node_vec = torch.cat([x_vec, sum_h_nei], dim=1)  # node_vec.size = (len(nodes), 2*hidden_size)
    return nn.ReLU()(W(node_vec))
