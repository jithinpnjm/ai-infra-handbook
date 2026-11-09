# Run with:  torchrun --nnodes=1:4 --nproc-per-node=8 --max-restarts=3 --rdzv-backend=c10d --rdzv-endpoint=$HEAD:29400 train_elastic.py
# torchrun is the elastic launcher; the training script itself only initialises the process group and resumes from a checkpoint.
# (An earlier draft called torch.distributed.elastic.agent.run(...), which is not how a training script is launched.)
import os, torch, torch.distributed as dist

MAX_STEPS = 10_000

def build_model(): return torch.nn.Linear(16, 1)
def build_optimiser(m): return torch.optim.SGD(m.parameters(), lr=0.01)

def load_latest_checkpoint(path="ckpt.pt"):
    return torch.load(path, map_location="cpu") if os.path.exists(path) else None

def save_checkpoint(state, path="ckpt.pt"):
    if dist.get_rank() == 0:
        torch.save(state, path + ".tmp"); os.replace(path + ".tmp", path)   # atomic: a crash never leaves a half file
    dist.barrier()

def train():
    dist.init_process_group(backend="nccl" if torch.cuda.is_available() else "gloo")
    model, opt = build_model(), build_optimiser(build_model())
    opt = build_optimiser(model)
    state = load_latest_checkpoint()
    start = 0
    if state:
        model.load_state_dict(state["model"]); opt.load_state_dict(state["optimiser"]); start = state["step"] + 1
    for step in range(start, MAX_STEPS):
        loss = model(torch.randn(8, 16)).pow(2).mean(); opt.zero_grad(); loss.backward(); opt.step()
        if step % 100 == 0:
            save_checkpoint({"model": model.state_dict(), "optimiser": opt.state_dict(), "step": step})

if __name__ == "__main__":
    train()
