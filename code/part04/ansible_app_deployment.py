"""Chapter 4.9 model: End-to-end application deployment release manager (pinned
version regex check, atomic `current` symlink switch, N-release retention pruning,
instant rollback), Gunicorn multiprocessing worker sizing (`cpu_count() * 2`),
and NGINX upstream + TLS config generator.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 6 & 7:
  * Chapter 6 ("Introducing Mezzanine: Our Test Application"): Development
    (`manage.py runserver 0.0.0.0:8000` + SQLite in foreground) vs Production
    architecture (NGINX reverse proxy handling TLS & `/static` -> Gunicorn WSGI
    over Unix domain socket `gunicorn.sock` managed by Supervisor/systemd ->
    PostgreSQL database + Memcached).
  * Chapter 7 ("Complex Playbooks"): `mezzanine.yml` complete deployment playbook
    (`vars:` + `vars_files: [secrets.yml]`, `apt` native C header packages
    `libpq-dev`/`libjpeg-dev`/`libssl-dev`, `git` checkout with SSH agent
    forwarding `ForwardAgent=yes` and `accept_hostkey: true`, `pip` virtualenv
    install, `postgresql_user` and `postgresql_db` with `become_user: postgres`,
    `encoding='UTF8'`, `lc_collate='en_US.UTF-8'`, `lc_ctype='en_US.UTF-8'`,
    `template='template0'`, `local_settings.py.j2` `ALLOWED_HOSTS`, `django_manage`
    `migrate` and `collectstatic`, `script: scripts/setsite.py` with `environment:`,
    `gunicorn.conf.py.j2` `workers = cpu_count() * 2`, `supervisor.conf.j2`,
    `openssl req` with `creates:` and `chdir:`, `cron` `*/5` `poll_twitter`, and
    `192.168.33.10.nip.io` wildcard DNS resolution).
"""
import re
from typing import Dict, List, Sequence, Tuple

PINNED_VERSION_RE = re.compile(r"^(v[0-9]+\.[0-9]+\.[0-9]+|[0-9a-f]{7,40})$")


def validate_pinned_version(version: str) -> bool:
    """Model Section 5 pre_tasks assertion requiring a semantic tag or commit SHA."""
    return bool(PINNED_VERSION_RE.match(version))


class AtomicReleaseDeployer:
    """Model Section 5 `/opt/fleetapp/releases/<version>` + `/opt/fleetapp/current`
    atomic symlink switcher, release pruner (`keep_releases`), and rollback.
    """

    def __init__(self, keep_releases: int = 5) -> None:
        self.keep_releases = keep_releases
        self.releases: List[str] = []  # ordered oldest -> newest
        self.current: str | None = None

    def deploy(self, version: str) -> Dict[str, object]:
        if not validate_pinned_version(version):
            raise ValueError(f"app_version {version!r} must be a tag or commit SHA, not a branch")
        if version in self.releases:
            self.releases.remove(version)
        self.releases.append(version)
        self.current = f"releases/{version}"

        pruned: List[str] = []
        while len(self.releases) > self.keep_releases:
            oldest = self.releases.pop(0)
            pruned.append(oldest)
        return {
            "current": self.current,
            "retained": list(self.releases),
            "pruned": pruned,
        }

    def rollback(self, target_version: str) -> str:
        if target_version not in self.releases:
            raise KeyError(f"release {target_version!r} not in retained releases {self.releases}")
        self.current = f"releases/{target_version}"
        return self.current


def render_gunicorn_conf(proj_path: str, proj_name: str, vcpus: int) -> str:
    """Model AUR Ch. 7 Example 7-21 templates/gunicorn.conf.py.j2."""
    workers = vcpus * 2
    return (
        f'bind = "unix:{proj_path}/gunicorn.sock"\n'
        f"workers = {workers}\n"
        f'proc_name = "{proj_name}"\n'
    )
