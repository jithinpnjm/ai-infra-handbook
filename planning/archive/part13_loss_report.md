# Part 13: what the 2026-10-26 rewrite dropped (restore list)

Originals are in planning/archive/part13_pre_rewrite/ (recovered from the OpenCode session history, because they were never committed). Generated with tools/loss_check.py. Number differences caused only by formatting (50.0 vs 50, 1,200 vs 1.2 GB/s) are normalized; cross-reference numbers such as 13.1 still show up and can be ignored.

## 01-the-ai-data-path-from-storage-to-gpu.md
```text
words 10552 -> 11048 (+5%) | table rows 62 -> 62 | code blocks 17 -> 21 | questions 20 -> 20 | headings 55 -> 54
technical terms lost: 13 of 204 | numbers lost: 5 of 171 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['100s', '26/26', '750K', 'CQEs', 'HDDs', 'RWO', 'SGLs', 'SQEs', 'a3-highgpu-8g', 'cuFileWriteAsync', 'g2-standard-48', 'torch.Tensor', 'torch.cuda.Event']
LOST NUMBERS: ['0.576', '31', '140', '750', '10000000']
LOST SOURCE FILES: []
```

## 02-local-nvme-and-data-staging.md
```text
words 11578 -> 10730 (-7%) | table rows 44 -> 54 | code blocks 18 -> 20 | questions 20 -> 20 | headings 50 -> 50
technical terms lost: 40 of 132 | numbers lost: 10 of 171 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['.tar', '/beegfs', '/lustre', '/proc/mounts', '/raid/.../manifest.json', '/raid/cache/train-0042.tar', '/raid/ckpt-epoch-N.pt', '/raid/tmp', '/shared-storage', '/shared-storage/checkpoints/ckpt-epoch-N.pt', '/shared-storage/dataset/train-0042.tar', '/sys/block/md0/queue/read_ahead_kb', '/sys/block/nvme0n1/queue/read_ahead_kb', '/sys/block/nvme0n1/queue/scheduler', '/sys/block/nvmeXn1/queue/nr_requests', '/sys/block/nvmeXn1/queue/read_ahead_kb', '400G', '9/10', 'A100', 'CQE', 'CRITICAL_REPLACE_DRIVE', 'H2D', 'LZ4', 'P/E', 'PIX', 'PRP', 'SGL', 'SQE', 'TFRecord', 'UPI', 'available_spare_threshold', 'cuFileRead', 'ext4', 'fstrim.timer', 'nr_requests=1023', 'nr_requests=128', 'nvidia-fs', 'nvidia.dali.pipeline.Pipeline', 'pure_random_o_direct', 'torch.cuda.Event']
LOST NUMBERS: ['15.3', '0042', '99.8', '156', '225', '255', '400', '1750', '2000', '1000000']
LOST SOURCE FILES: []
```

## 03-gpudirect-storage-architecture.md
```text
words 10836 -> 11140 (+3%) | table rows 55 -> 56 | code blocks 23 -> 26 | questions 20 -> 20 | headings 76 -> 78
technical terms lost: 9 of 183 | numbers lost: 2 of 155 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['DEFERRED', 'DONE', 'GEMM', 'NVMe/TCP', 'SMs', 'SQEs', 'TorchVision', 'planning/gem_books/DEFERRED.md', 'state_dict']
LOST NUMBERS: ['3.0', '2000']
LOST SOURCE FILES: []
```

## 04-lustre-for-ai.md
```text
words 11477 -> 12408 (+8%) | table rows 50 -> 50 | code blocks 14 -> 26 | questions 20 -> 20 | headings 58 -> 57
technical terms lost: 7 of 144 | numbers lost: 5 of 185 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['ConnectX-7', 'ConnectX-8', 'HBM', 'UDSP', 'rank_0001.distcp', 'site-packages', 'tx_queued']
LOST NUMBERS: ['0.5', '0001', '70', '75', '2304']
LOST SOURCE FILES: []
```

## 05-beegfs-weka-vast-and-object-storage.md
```text
words 10861 -> 11079 (+2%) | table rows 59 -> 59 | code blocks 16 -> 19 | questions 20 -> 20 | headings 70 -> 70
technical terms lost: 8 of 138 | numbers lost: 7 of 203 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['1/4', 'BAR1', 'GET/HEAD/LIST', 'ZFS', 'cuFileBufRegister', 'cuFileReadAsync', 'cuFileWrite', 'cuFileWriteAsync']
LOST NUMBERS: ['0.15', '0.8', '13.1', '13.3', '13.4', '1200', '2100']
LOST SOURCE FILES: []
```

## 06-data-loading-small-files-and-metadata.md
```text
words 11111 -> 10645 (-4%) | table rows 51 -> 51 | code blocks 25 -> 18 | questions 20 -> 20 | headings 48 -> 49
technical terms lost: 11 of 120 | numbers lost: 5 of 201 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['3FS', 'MMapIndexedDataset', 'RDMA', 'RandomResizedCrop', 'WekaFS', 'blk-mq', 'cuFileReadAsync', 'doc_id', 'libjpeg-turbo', 'mq-deadline', 'torchvision.transforms.v2']
LOST NUMBERS: ['8.0', '13.1', '13.3', '13.4', '13.5']
LOST SOURCE FILES: []
```

## 07-checkpoint-architecture-and-recovery.md
```text
words 12080 -> 11192 (-7%) | table rows 57 -> 57 | code blocks 22 -> 20 | questions 20 -> 20 | headings 47 -> 45
technical terms lost: 9 of 143 | numbers lost: 15 of 225 | gem books no longer cited: [] | source files no longer cited: 5
LOST TERMS: ['--numtargets=8', '.ckpt-step-N.tmp', 'DistributedDataParallel', 'FullyShardedDataParallel', 'MPIJob', 'PyTorchJob', 'auto_wrap_policy', 'labs/lab-01..04', 'verify_checkpoint_manifest_and_completeness']
LOST NUMBERS: ['4.4', '5.7', '6.0', '13.1', '13.5', '13.6', '039.94', '47', '85', '219.94', '519.97', '979.94', '8250', '10000', '288000']
LOST SOURCE FILES: ['chapter-01-why-distributed-training-exists.md', 'chapter-08-checkpoint-architecture-and-recovery.md', 'chapter-08-nccl-collectives-and-communication-paths.md', 'chapter-09-checkpointing-and-recovery.md', 'chapter-12-volume-13-summary.md']
```

## 08-capacity-performance-and-cost-planning.md
```text
words 12584 -> 11354 (-10%) | table rows 65 -> 65 | code blocks 15 -> 16 | questions 20 -> 20 | headings 44 -> 42
technical terms lost: 15 of 129 | numbers lost: 12 of 311 | gem books no longer cited: [] | source files no longer cited: 5
LOST TERMS: ['.idx', '.safetensors', '25.6K', '2x400GbE', '64x400GbE', 'Llama-70B', 'NGC', 'ResNet-50', 'TensorRT-LLM', 'XFS', 'beegfs-meta', 'closes/sec', 'int32', 'stats/sec', 'torch.distributed.checkpoint']
LOST NUMBERS: ['4.0', '13.1', '13.3', '13.4', '13.6', '13.7', '44', '66', '77', '1200000', '15360000', '61440000']
LOST SOURCE FILES: ['chapter-04-storage-infrastructure-for-ai-pipelines.md', 'chapter-10-capacity-performance-and-cost-planning.md', 'chapter-11-capacity-planning-and-forecasting.md', 'chapter-12-cost-optimization-and-resource-efficiency.md', 'chapter-12-volume-15-summary.md']
```

## 09-storage-troubleshooting.md
```text
words 12030 -> 12117 (+1%) | table rows 64 -> 64 | code blocks 14 -> 20 | questions 20 -> 20 | headings 42 -> 41
technical terms lost: 12 of 169 | numbers lost: 2 of 170 | gem books no longer cited: [] | source files no longer cited: 0
LOST TERMS: ['/beegfs', '50K/sec', 'DNodes', 'GPU-to-NIC', 'MDT', 'RTO', 'ZFS', 'beegfs-client', 'cuFileWrite', 'cuda:0', 'np.frombuffer', 'torch.frombuffer']
LOST NUMBERS: ['0.8', '75']
LOST SOURCE FILES: []
```
