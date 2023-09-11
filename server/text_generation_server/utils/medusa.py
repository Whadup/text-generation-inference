import torch
from text_generation_server.utils.layers import TensorParallelHead, FastLinear


class ResBlock(torch.nn.Module):
    def __init__(self, config, prefix, weights):
        super().__init__()
        self.linear = FastLinear.load(config, prefix=f"{prefix}.linear", weights=weights, bias=True)
        self.act = torch.nn.SiLU()

    def forward(self, x):
        return x + self.act(self.linear(x))


class MedusaModel(torch.nn.Module):
    def __init__(
        self,
        config,
        weights
    ):
        super().__init__()
        self.heads = torch.nn.ModuleList(
            [MedusaHead(config, prefix=f"{i}", weights=weights) for i in range(config["medusa_num_heads"])]
        )


class MedusaHead(torch.nn.Module):
    def __init__(self, config, prefix, weights):
        super().__init__()
        self.blocks = torch.nn.ModuleList([ResBlock(config, prefix=f"{prefix}.{i}", weights=weights) for i in range(config["medusa_num_layers"])])
        n = len(self.blocks)
        self.out = FastLinear.load(config, prefix=f"{prefix}.{n}", weights=weights, bias=False)

    def forward(self, x):
        for block in self.blocks:
            x = block(x)
        x = self.out(x)
        return x