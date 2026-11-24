import time
import torch
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

# Simulate 84 face images of 192x192x3 uint8
num_frames = 84
H, W = 192, 192
faces = [np.random.randint(0, 255, (H, W, 3), dtype=np.uint8) for _ in range(num_frames)]
batch_size = 8

# Baseline: per-batch numpy processing & transfer
def baseline(index):
    img_batch = []
    for i in range(batch_size):
        idx = (index + i) % num_frames
        img_batch.append(faces[idx])
    img_batch = np.asarray(img_batch)
    img_masked = img_batch.copy()
    img_masked[:, H//2:] = 0
    img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
    t = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
    return t

# Optimized: pre-cached GPU tensor stack
cached_tensors = []
for f in faces:
    f_masked = f.copy()
    f_masked[H//2:, :] = 0
    concat = np.concatenate((f_masked, f), axis=2) / 255.
    t = torch.FloatTensor(np.transpose(concat, (2, 0, 1))).to(device)
    cached_tensors.append(t)
cached_stack = torch.stack(cached_tensors)

def optimized(index):
    indices = [(index + i) % num_frames for i in range(batch_size)]
    return cached_stack[indices]

# Warmup
for i in range(10):
    baseline(i)
    optimized(i)
torch.cuda.synchronize()

# Benchmark 200 batches
N = 200

t0 = time.perf_counter()
for i in range(N):
    _ = baseline(i)
torch.cuda.synchronize()
t_baseline = time.perf_counter() - t0

t0 = time.perf_counter()
for i in range(N):
    _ = optimized(i)
torch.cuda.synchronize()
t_optimized = time.perf_counter() - t0

print(f"Baseline time for {N} batches: {t_baseline*1000:.2f} ms ({t_baseline/N*1000:.3f} ms/batch)")
print(f"Optimized time for {N} batches: {t_optimized*1000:.2f} ms ({t_optimized/N*1000:.3f} ms/batch)")
print(f"Speedup: {t_baseline / t_optimized:.1f}x faster batch preparation!")

# Verify exact numerical equivalence
t_base = baseline(0)
t_opt = optimized(0)
diff = (t_base - t_opt).abs().max().item()
print(f"Max absolute difference: {diff} (should be 0.0)")
