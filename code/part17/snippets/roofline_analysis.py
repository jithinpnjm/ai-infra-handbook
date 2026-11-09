import torch
import torch.profiler

model = torch.nn.Transformer(d_model=512, nhead=8, num_layers=6).cuda()

with torch.profiler.profile(
    activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
    record_shapes=True,
) as prof:
    for _ in range(10):
        x = torch.randn(32, 128, 512).cuda()
        model(x)

# Export the profile
prof.export_chrome_trace("/profiles/transformer.json")

# Compute the roofline
flops = 4 * 32 * 128 * 128 * 512 * 6 * 12  # FLOPs for the forward pass
bytes = 32 * 128 * 512 * 4 * 6  # Bytes for activations and weights
intensity = flops / bytes
ridge = 989e12 / 3350e9  # H100 ridge point
print(f"Arithmetic intensity: {intensity:.0f} FLOP/byte")
print(f"H100 ridge point: {ridge:.0f} FLOP/byte")
print(f"Bottleneck: {'compute' if intensity > ridge else 'memory'}")
