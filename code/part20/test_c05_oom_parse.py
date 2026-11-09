from c05_oom_parse import parse, explain, top_tasks

# Built by filling the printk format strings in mm/oom_kill.c and mm/memcontrol.c
# (Linux v6.6). Numbers are invented for the test. This is NOT a captured log.
CGROUP_LOG = """\
[ 4021.118201] python invoked oom-killer: gfp_mask=0xcc0(GFP_KERNEL), order=0, oom_score_adj=0
[ 4021.118700] Tasks state (memory values in pages):
[ 4021.118702] [  pid  ]   uid  tgid total_vm      rss pgtables_bytes swapents oom_score_adj name
[ 4021.118710] [   2210]     0  2210      256       12    28672        0          0 pause
[ 4021.118715] [   2301]     0  2301    90112    26000   311296        0          0 python
[ 4021.118720] [   2330]     0  2330     1200      300    40960        0          0 sh
[ 4021.118790] oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=abc,mems_allowed=0,oom_memcg=/kubepods/pod1/abc,task_memcg=/kubepods/pod1/abc,task=python,pid=2301,uid=0
[ 4021.118800] Memory cgroup out of memory: Killed process 2301 (python) total-vm:360448kB, anon-rss:102400kB, file-rss:2048kB, shmem-rss:0kB, UID:0 pgtables:304kB oom_score_adj:0
"""

NODE_LOG = """\
java invoked oom-killer: gfp_mask=0x100cca(GFP_HIGHUSER_MOVABLE), order=0, oom_score_adj=0
oom-kill:constraint=CONSTRAINT_NONE,nodemask=(null),cpuset=/,mems_allowed=0-1,global_oom,task_memcg=/system.slice/app.service,task=java,pid=881,uid=1000
Out of memory: Killed process 881 (java) total-vm:9437184kB, anon-rss:8388608kB, file-rss:4096kB, shmem-rss:0kB, UID:1000 pgtables:20480kB oom_score_adj:0
"""


def test_cgroup_oom_fields():
    info = parse(CGROUP_LOG)
    assert info["trigger"] == "python"
    assert info["constraint"] == "CONSTRAINT_MEMCG"
    assert info["oom_memcg"] == "/kubepods/pod1/abc"
    assert info["victim_pid"] == 2301
    assert info["anon_rss_kb"] == 102400
    assert info["kind"] == "Memory cgroup out of memory"
    assert info["victim_adj"] == 0


def test_node_oom_is_global():
    info = parse(NODE_LOG)
    assert info["constraint"] == "CONSTRAINT_NONE"
    assert info["oom_memcg"] is None
    assert info["kind"] == "Out of memory"
    assert "whole-node memory" in explain(info)


def test_explain_cgroup_wording():
    assert "container/cgroup limit" in explain(parse(CGROUP_LOG))
    assert "anon-rss 100 MiB" in explain(parse(CGROUP_LOG))


def test_task_table_sorted_by_rss():
    tasks = top_tasks(parse(CGROUP_LOG), 2)
    assert [t["name"] for t in tasks] == ["python", "sh"]
    assert len(parse(CGROUP_LOG)["tasks"]) == 3


def test_no_oom_text():
    assert explain(parse("nothing here\n")) == "no 'Killed process' line found"
