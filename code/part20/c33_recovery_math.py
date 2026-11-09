"""Recovery arithmetic for chapter 20.33. Standard library only."""


def downtime_minutes(availability, days=30):
    """Allowed downtime in minutes for an availability target over a period."""
    return (1.0 - availability) * days * 24 * 60


def serial_availability(*parts):
    """All parts must work: multiply the availabilities."""
    result = 1.0
    for p in parts:
        result *= p
    return result


def parallel_availability(*parts):
    """Any one part is enough, assuming independent failures."""
    miss = 1.0
    for p in parts:
        miss *= 1.0 - p
    return 1.0 - miss


def lost_work_minutes(checkpoint_interval_min):
    """Return (worst case, average) minutes of training lost on a crash."""
    return checkpoint_interval_min, checkpoint_interval_min / 2.0


def lost_gpu_hours(gpus, minutes):
    return gpus * minutes / 60.0


def transfer_seconds(size_gb, gb_per_s):
    """Time to read a checkpoint or model weights at a sustained rate."""
    return size_gb / gb_per_s


def quorum(members):
    """Votes an etcd style consensus group needs to commit a write."""
    return members // 2 + 1


def tolerated_failures(members):
    return members - quorum(members)


if __name__ == "__main__":
    print("99.9% month:", round(downtime_minutes(0.999), 1), "min")
    print("99.99% month:", round(downtime_minutes(0.9999), 2), "min")
    both = serial_availability(0.999, 0.999)
    print("two 99.9% in series:", round(both, 6), round(downtime_minutes(both), 1), "min")
    two = parallel_availability(0.999, 0.999)
    print("two 99.9% independent in parallel:", round(two, 6),
          round(downtime_minutes(two), 3), "min")
    worst, mean = lost_work_minutes(30)
    print("30 min checkpoints, 512 GPUs: worst", lost_gpu_hours(512, worst),
          "GPU-h, mean", lost_gpu_hours(512, mean), "GPU-h")
    params_b = 70
    ckpt_gb = params_b * 16
    print("70B checkpoint at 16 B/param:", ckpt_gb, "GB;",
          "restore at 5 GB/s:", round(transfer_seconds(ckpt_gb, 5), 1), "s")
    print("weights 140 GB at 2 GB/s:", transfer_seconds(140, 2), "s")
    for n in (1, 3, 5):
        print("etcd members", n, "quorum", quorum(n), "tolerates", tolerated_failures(n))
