"""Chapter 5.1 model: OCI image layer & `.wh.` whiteout size calculator,
Dockerfile layer cache-invalidation simulator (`KUR` Ch. 2), and NVIDIA host
driver (`libcuda.so`) vs container CUDA runtime (`libcudart.so`) compatibility
checker.

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 2
  ("Creating and Running Containers"):
  * Layer inheritance tree (Debian -> Ruby -> Rails), why layer ordering from
    least-frequently to most-frequently changing determines build-cache hits
    (`COPY package*.json` + `npm install` before `COPY . .`), `kuard` multi-stage
    build (`golang:1.17-alpine AS build` -> `FROM alpine` with `COPY --from=build`),
    why deleting a file in a subsequent layer hides the file without reducing
    image size, and `--memory 200m --memory-swap 1G --cpu-shares 1024`.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 3 ("Container Runtime"):
  * Open Container Initiative (OCI, June 2015), OCI Image Specification
    (Image Index -> Manifest -> Config + Layers), and OCI Runtime Specification
    (`rootfs/` + `config.json` bundle).
"""
from typing import Dict, List, Mapping, Sequence, Tuple


def simulate_oci_layer_sizes(layers: Sequence[Mapping[str, int]]) -> Dict[str, object]:
    """Model Section 2 & KUR Ch. 2 additive OCI image layers and overlayfs whiteouts:
    Each layer is `{filepath: size_bytes_or_negative_1_for_whiteout}`.
    - `visible_files` in the merged overlayfs view excludes deleted (`-1`) files.
    - `total_image_bytes` (sum of all layer tarballs shipped over the network)
      STILL includes bytes from earlier layers even if deleted in a later layer!
    """
    visible: Dict[str, int] = {}
    total_layer_bytes = 0
    for layer in layers:
        for path, size in layer.items():
            if size < 0:
                visible.pop(path, None)
            else:
                visible[path] = size
                total_layer_bytes += size
    return {
        "visible_bytes": sum(visible.values()),
        "total_image_bytes": total_layer_bytes,
        "wasted_whiteout_bytes": total_layer_bytes - sum(visible.values()),
    }


def simulate_dockerfile_cache_hits(
    steps: Sequence[Tuple[str, str]],
    previous_hashes: Sequence[Tuple[str, str]],
) -> List[bool]:
    """Model Section 3 & KUR Ch. 2 Dockerfile layer cache invalidation:
    Once ANY layer's input hash changes, that layer AND all subsequent layers
    in the stage suffer a cache miss (`False`).
    """
    hits: List[bool] = []
    cache_broken = False
    for idx, step in enumerate(steps):
        if not cache_broken and idx < len(previous_hashes) and step == previous_hashes[idx]:
            hits.append(True)
        else:
            cache_broken = True
            hits.append(False)
    return hits


MIN_DRIVER_FOR_CUDA: Mapping[str, int] = {
    "11.8": 520,
    "12.1": 530,
    "12.4": 550,
    "12.6": 560,
}


def check_cuda_driver_compatibility(
    host_driver_major: int,
    image_cuda_version: str,
    has_cuda_compat_pkg: bool = False,
) -> Tuple[bool, str]:
    """Model Section 6 GPU container compatibility rule: host `libcuda.so`
    driver major version must be >= minimum required by the image's `libcudart`
    (unless `cuda-compat` forward-compatibility libraries are active on a
    supported data-center driver).
    """
    req = MIN_DRIVER_FOR_CUDA[image_cuda_version]
    if host_driver_major >= req:
        return True, "compatible (host driver >= image CUDA requirement)"
    if has_cuda_compat_pkg and host_driver_major >= 535:
        return True, "compatible via cuda-compat forward-compatibility package"
    return False, f"CUDA driver version ({host_driver_major}) is insufficient for CUDA runtime version ({image_cuda_version}, needs >={req})"
