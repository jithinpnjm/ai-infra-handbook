#!/usr/bin/env python3
"""Self-checking lab for chapter 7.9: find degraded PCIe links, slow network ports and failing drives through Redfish.

Part A uses the teaching mock (8 GPUs and 8 NICs on PCIe Gen5 x16, 400G ports, 2 NVMe drives) and injects faults.
Part B runs the same tool on two of DMTF's example trees (set REDFISH_PUBLICATIONS to a clone of DMTF/Redfish-Publications).
"""
import os, sys, threading
from redfish_mock import make_server
from redfish_crawl import Client
import rf_hardware as hw

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def serve(**kw):
    srv, st = make_server("dgx", 0, **kw)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, st, Client(f"http://127.0.0.1:{srv.server_address[1]}", "admin", "adminpass")


def flagged(c, group):
    rows = hw.analyse(hw.walk(c))
    return {name: f for name, _, _, f in rows[group] if f}


def main():
    srv, st, c = serve()
    R = "/redfish/v1/Chassis/Chassis_0/"
    rows = hw.analyse(hw.walk(c))
    check("healthy mock: 16 PCIe interfaces (8 GPU + 8 NIC), 8 ports, 2 drives", (len(rows["pcie"]), len(rows["port"]), len(rows["drive"])) == (16, 8, 2),
          (len(rows["pcie"]), len(rows["port"]), len(rows["drive"])))
    check("healthy mock: nothing is flagged", not any(f for g in rows.values() for *_, f in g))

    st.tree[R + "PCIeDevices/GPU_3"]["PCIeInterface"].update(PCIeType="Gen3", LanesInUse=8)
    f = flagged(c, "pcie")
    k = [n for n in f if n.endswith("GPU_3")]
    check("a GPU trained down to Gen3 x8 is flagged for both speed and width",
          k and "PCIe Gen3 of Gen5" in f[k[0]] and "link width x8 of x16" in f[k[0]], f)
    check("only that one device is flagged", len(f) == 1, f)

    p = R + "NetworkAdapters/NIC_2/Ports/1"
    st.tree[p].update(LinkStatus="LinkDown")
    f = flagged(c, "port")
    check("an enabled port that is LinkDown is flagged", any("LinkStatus=LinkDown" in x for v in f.values() for x in v), f)
    st.tree[p].update(LinkState="Disabled")
    check("a port that is administratively Disabled is not flagged", not flagged(c, "port"))
    st.tree[p].update(LinkState="Enabled", LinkStatus="LinkUp", CurrentSpeedGbps=200.0)
    f = flagged(c, "port")
    check("a 400G port running at 200G is flagged (cable or optics or negotiation)", any("speed 200 of 400 Gbps" in x for v in f.values() for x in v), f)
    st.tree[p].update(CurrentSpeedGbps=400.0, ActiveWidth=2)
    f = flagged(c, "port")
    check("a port with 2 of 4 lanes active is flagged", any("width x2 of x4" in x for v in f.values() for x in v), f)
    st.tree[p].update(ActiveWidth=4)

    d = "/redfish/v1/Chassis/Chassis_0/Drives/1"
    st.tree[d].update(FailurePredicted=True)
    f = flagged(c, "drive")
    check("a drive predicting failure is flagged", any("failure predicted" in x for v in f.values() for x in v), f)
    st.tree[d].update(FailurePredicted=False, PredictedMediaLifeLeftPercent=5)
    f = flagged(c, "drive")
    check("a drive with 5 percent life left is flagged", any("media life left 5%" in x for v in f.values() for x in v), f)
    st.tree[d].update(PredictedMediaLifeLeftPercent=97, NegotiatedSpeedGbs=8.0)
    f = flagged(c, "drive")
    check("a drive linked at 8 of 32 Gbps is flagged", any("drive link 8 of 32 Gbps" in x for v in f.values() for x in v), f)
    st.tree[d].update(NegotiatedSpeedGbs=32.0)
    st.tree[R + "PCIeDevices/NIC_1"]["Status"] = {"State": "Enabled", "Health": "Warning"}
    f = flagged(c, "pcie")
    check("a PCIe device with Health Warning is flagged", any("health=Warning" in x for v in f.values() for x in v), f)
    c.logout(); srv.shutdown()

    root = os.environ.get("REDFISH_PUBLICATIONS")
    if not root:
        print("SKIP  part B needs REDFISH_PUBLICATIONS")
    else:
        srv, st, c = serve(mockup=os.path.join(root, "mockups", "public-tower"))
        f = flagged(c, "pcie")
        check(f"DMTF tower example: {len(f)} PCIe devices run below their maximum link", len(f) >= 3, f)
        res = hw.walk(c)
        check("DMTF tower example: 10 PCIe interfaces, 18 ports, 18 drives are found", len(hw.analyse(res)["pcie"]) == 10 and len(hw.analyse(res)["port"]) == 18 and len(hw.analyse(res)["drive"]) == 18,
              {k: len(v) for k, v in hw.analyse(res).items()})
        c.logout(); srv.shutdown()
        srv, st, c = serve(mockup=os.path.join(root, "mockups", "public-smartnic"))
        res = hw.walk(c)
        mism = [r for r in res if r.get("@odata.id", "").rstrip("/") != r["_uri"]]
        check("DMTF SmartNIC example: resources whose own @odata.id differs from the address they were fetched from are detected", len(mism) >= 1, len(mism))
        c.logout(); srv.shutdown()

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
