from ch04_access_check import Cred, Node, check_access

ME = Cred(uid=1000, gid=1000)
SVC = Cred(uid=2000, gid=2000, groups={3000})


def d(name, mode=0o755, uid=0, gid=0, **kw):
    return Node(name, uid, gid, mode, is_dir=True, **kw)


def f(name, mode=0o644, uid=1000, gid=1000, **kw):
    return Node(name, uid, gid, mode, **kw)


def test_plain_read_allowed_by_other():
    ok, err, why = check_access([d("/"), d("data"), f("a", 0o644, uid=0, gid=0)], SVC, "r")
    assert ok and err is None


def test_directory_without_search_blocks_a_readable_file():
    # chmod 644 on the file does not help: the directory is the problem.
    path = [d("/"), d("secret", 0o600, uid=2000, gid=2000), f("a", 0o644, uid=2000, gid=2000)]
    ok, err, why = check_access(path, Cred(uid=2000, gid=2000), "r")
    assert (ok, err) == (False, "EACCES")
    assert "search" in why and "secret" in why


def test_owner_class_wins_even_when_group_has_more():
    # path_resolution(7): only the first matching class is used.
    node = f("a", 0o047, uid=2000, gid=3000)
    ok, err, _ = check_access([d("/"), node], SVC, "r")
    assert (ok, err) == (False, "EACCES")


def test_acl_mask_limits_named_user():
    # acl(5): named user and group entries are limited by the mask.
    acl = {"user": {2000: "rw-"}, "group_obj": "r--", "mask": "r--"}
    node = f("a", 0o640, uid=1000, gid=1000, acl=acl)
    ok, err, why = check_access([d("/"), node], SVC, "w")
    assert (ok, err) == (False, "EACCES")
    assert "mask" in why
    ok, _, _ = check_access([d("/"), node], SVC, "r")
    assert ok


def test_acl_named_user_allowed_when_mask_is_wide():
    acl = {"user": {2000: "rw-"}, "group_obj": "r--", "mask": "rw-"}
    node = f("a", 0o660, uid=1000, gid=1000, acl=acl)
    assert check_access([d("/"), node], SVC, "w")[0]


def test_acl_named_group_through_supplementary_group():
    acl = {"group_obj": "---", "group": {3000: "r--"}, "mask": "rwx"}
    node = f("a", 0o070, uid=1000, gid=1000, acl=acl)
    assert check_access([d("/"), node], SVC, "r")[0]
    assert not check_access([d("/"), node], SVC, "w")[0]


def test_read_only_mount_gives_erofs_even_for_root():
    root = Cred(uid=0, gid=0, dac_override=True)
    node = f("a", 0o777, uid=0, gid=0, mount_ro=True)
    assert check_access([d("/"), node], root, "w")[:2] == (False, "EROFS")
    assert check_access([d("/"), node], root, "r")[0]


def test_immutable_blocks_root_write():
    root = Cred(uid=0, gid=0, dac_override=True)
    node = f("a", 0o644, uid=0, gid=0, immutable=True)
    ok, err, why = check_access([d("/"), node], root, "w")
    assert (ok, err) == (False, "EPERM") and "immutable" in why


def test_noexec_mount_blocks_exec_even_with_mode_755():
    node = f("run.sh", 0o755, uid=1000, gid=1000, mount_noexec=True)
    ok, err, why = check_access([d("/"), node], ME, "rx", executing=True)
    assert (ok, err) == (False, "EACCES") and "noexec" in why
    assert check_access([d("/"), node], ME, "r")[0]


def test_root_needs_some_execute_bit():
    # path_resolution(7): CAP_DAC_OVERRIDE grants execute only if an x bit is set.
    root = Cred(uid=0, gid=0, dac_override=True)
    assert not check_access([d("/"), f("a", 0o644, uid=1, gid=1)], root, "x", executing=True)[0]
    assert check_access([d("/"), f("a", 0o744, uid=1, gid=1)], root, "x", executing=True)[0]


def test_root_without_dac_override_is_just_another_user():
    # A container that dropped CAP_DAC_OVERRIDE: uid 0 follows the mode bits.
    rootless = Cred(uid=0, gid=0, dac_override=False)
    node = f("a", 0o600, uid=1000, gid=1000)
    assert check_access([d("/"), node], rootless, "r")[:2] == (False, "EACCES")
