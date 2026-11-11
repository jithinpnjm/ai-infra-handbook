#!/bin/bash
# code/part19/c04_slurm_train.sh
# 4 nodes x 8 GPUs. The paths under /shared are placeholders for your shared file system.
#SBATCH --job-name=c04-train
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --time=24:00:00
#SBATCH --signal=B:USR1@180
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/shared/logs/%x-%j.out

set -u
CODE=/shared/ai-infra-handbook/code/part19
CKPT=/shared/c04/ckpt
METRICS=/shared/c04/metrics
MAX_REQUEUES=5

# Watchdog settings (names from the PyTorch 2.15 ProcessGroupNCCL table; values are my choices).
export TORCH_NCCL_ENABLE_MONITORING=1
export TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=300
export TORCH_NCCL_TRACE_BUFFER_SIZE=2000
export TORCH_NCCL_DUMP_ON_TIMEOUT=1
export TORCH_NCCL_DEBUG_INFO_TEMP_FILE=/shared/c04/fr/${SLURM_JOB_ID}_rank_
export NCCL_DEBUG=WARN

HEAD=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
GOT_SIGNAL=0

# The batch shell cannot run a trap while a foreground command runs, so srun goes to the
# background and the shell waits. A signal sent to srun is forwarded to the tasks (srun man page).
on_usr1() {
    GOT_SIGNAL=1
    echo "[batch] SIGUSR1: asking torchrun to checkpoint and stop"
    kill -TERM "$SRUN_PID"
}
trap on_usr1 USR1

srun --kill-on-bad-exit=1 torchrun \
    --nnodes="$SLURM_NNODES" --nproc-per-node=8 --max-restarts=2 \
    --rdzv-id="$SLURM_JOB_ID" --rdzv-backend=c10d --rdzv-endpoint="$HEAD:29400" \
    "$CODE/c04_train.py" --ckpt-dir "$CKPT" --metrics-dir "$METRICS" \
    --steps 100000 --ckpt-every 500 --async-ckpt &
SRUN_PID=$!

wait "$SRUN_PID"
RC=$?
if [ "$GOT_SIGNAL" = 1 ]; then
    wait "$SRUN_PID"   # the first wait returned because of the trap; collect the real exit code
    RC=$?
    if [ "${SLURM_RESTART_COUNT:-0}" -lt "$MAX_REQUEUES" ]; then
        echo "[batch] requeueing job $SLURM_JOB_ID (restart count ${SLURM_RESTART_COUNT:-0})"
        scontrol requeue "$SLURM_JOB_ID"
        exit 0
    fi
    echo "[batch] restart limit reached, not requeueing"
fi
exit "$RC"
