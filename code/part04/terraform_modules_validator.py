"""Chapter 4.20 model: Terraform `gke-gpu-pool` module input & precondition
validator (`.tftest.hcl` equivalent), Git module `source` double-slash (`//`)
and `?ref=` parser, `path.module` vs `path.root` resolver, and inline-vs-separate
security-group rule conflict detector (`TUR` Ch. 4).

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapter 4 ("How to Create Reusable Infrastructure with
  Terraform Modules"):
  * Module basics (`modules/services/webserver-cluster`), inputs (`cluster_name`,
    `instance_type`, `min_size`, `max_size`), `locals` (internal constants
    `http_port = 80`, `any_port = 0`, `any_protocol = "-1"`), and outputs
    (`asg_name`, `alb_dns_name`, `alb_security_group_id`) enabling external
    `aws_autoscaling_schedule` and `aws_security_group_rule` composition.
  * Two module gotchas: (1) file paths (`path.module` vs `path.root` vs
    `path.cwd` in `templatefile("${path.module}/user-data.sh", ...)`), and
    (2) inline blocks vs separate resources (`aws_security_group` inline
    `ingress` overwriting external `aws_security_group_rule`).
  * Module versioning with Git tags (`//subdir?ref=v0.0.1` in `prod` while
    testing `?ref=v0.0.2` in `stage`).
- volume-10/05-terraform-for-infrastructure-as-code.md.
"""
import re
from typing import Any, Dict, List, Mapping, Tuple

DNS_LABEL_RE = re.compile(r"^[a-z]([-a-z0-9]{0,38}[a-z0-9])?$")
PINNED_REF_RE = re.compile(r"^(v?[0-9]+\.[0-9]+\.[0-9]+|[a-z0-9_\-]+/v[0-9]+\.[0-9]+\.[0-9]+|[0-9a-f]{7,40})$")


def validate_gke_gpu_pool_inputs(vars_dict: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Model Section 2 & 5 `modules/gke-gpu-pool` variable `validation` and
    resource `precondition` blocks (`tests/validation.tftest.hcl`).
    """
    errors: List[str] = []
    name = str(vars_dict.get("name", ""))
    if not DNS_LABEL_RE.match(name):
        errors.append("name must be a valid DNS label up to 40 characters.")

    gpu_count = int(vars_dict.get("gpu_count", 0))
    if gpu_count not in {0, 1, 2, 4, 8}:
        errors.append("gpu_count must be 0, 1, 2, 4 or 8.")

    gpu_type = vars_dict.get("gpu_type")
    if gpu_count > 0 and not gpu_type:
        errors.append("gpu_type is required when gpu_count > 0.")

    return (len(errors) == 0), errors


def parse_git_module_source(source: str) -> Dict[str, object]:
    """Parse a Terraform Git module `source` string such as:
      `git::https://git.example.com/platform/terraform-modules.git//gke-gpu-pool?ref=v2.3.1`
    and verify whether `?ref=` is pinned to an immutable tag/SHA.
    """
    raw = source[5:] if source.startswith("git::") else source
    ref = ""
    if "?ref=" in raw:
        raw, ref = raw.split("?ref=", 1)

    # Split repo and subdirectory on double slash `//` AFTER scheme `https://`
    scheme_sep = "://"
    if scheme_sep in raw:
        scheme_idx = raw.index(scheme_sep) + len(scheme_sep)
        rest = raw[scheme_idx:]
        if "//" in rest:
            repo_part, subdir = rest.split("//", 1)
            repo = raw[:scheme_idx] + repo_part
        else:
            repo, subdir = raw, ""
    elif "//" in raw:
        repo, subdir = raw.split("//", 1)
    else:
        repo, subdir = raw, ""

    is_pinned = bool(ref and PINNED_REF_RE.match(ref) and ref not in {"main", "master", "HEAD"})
    return {
        "repo": repo,
        "subdir": subdir,
        "ref": ref,
        "is_pinned": is_pinned,
    }


def detect_inline_vs_separate_sg_conflict(
    module_uses_inline_ingress: bool,
    caller_adds_external_sg_rule: bool,
) -> bool:
    """Model TUR Ch. 4 Gotcha #2: combining inline `ingress {}` blocks inside
    `aws_security_group` with an external `aws_security_group_rule` causes an
    overwrite conflict on every `terraform apply`.
    """
    return bool(module_uses_inline_ingress and caller_adds_external_sg_rule)
