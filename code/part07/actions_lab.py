#!/usr/bin/env python3
"""Self-checking lab for chapter 7.5: actions, tasks (202 + task monitor), event subscriptions, SSE.

All against the in-process mock with a simulated clock. Clause numbers refer to DSP0266 v1.21.0.
"""
import http.server, json, sys, threading, time, urllib.request
from redfish_mock import make_server
from protocol_lab import call

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


class Sink:
    """A tiny event receiver (what a monitoring system would run)."""
    def __init__(self):
        self.events = []
        outer = self
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                outer.events.append(json.loads(self.rfile.read(n)))
                self.send_response(204); self.end_headers()
            def log_message(self, *a):
                pass
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/events"


def main():
    srv, st = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    clock = [5000.0]
    st.now = lambda: clock[0]
    SYS = "/redfish/v1/Systems/System_0"

    # --- discover the action instead of hard-coding it
    s, h, b = call(base, "GET", SYS)
    act = b["Actions"]["#ComputerSystem.Reset"]
    target = act["target"]
    check("the resource advertises the action target and allowable values [7.11, 9.9.2]",
          target.endswith("/Actions/ComputerSystem.Reset") and "ForceRestart" in act["ResetType@Redfish.AllowableValues"])

    s, _, b = call(base, "POST", target, {})
    check("missing required parameter gives 400 [7.11]", s == 400, s)
    s, _, b = call(base, "POST", target, {"ResetType": "PowerCycleAndPray"})
    check("value not in the allowable list gives 400 [7.11]", s == 400, s)
    s, _, b = call(base, "PATCH", SYS, {"PowerState": "Off"})
    check("PATCH cannot change PowerState: 400, it is read-only (use the action) [7.6]", s == 400, s)
    s, _, _ = call(base, "POST", target, {"ResetType": "ForceOff"}, auth=("viewer", "viewpass"))
    check("ReadOnly cannot run the action: 403", s == 403, s)
    s, _, b = call(base, "POST", target, {"ResetType": "ForceOff"}, auth=("operator", "operpass"))
    check("Operator runs ForceOff: 200 with a Success message [7.11]",
          s == 200 and "Success" in b["error"]["code"], (s, b))
    s, _, b = call(base, "GET", SYS)
    check("GET afterwards shows PowerState Off", b["PowerState"] == "Off")
    s, _, b = call(base, "POST", target, {"ResetType": "ForceOff"})
    s, _, b = call(base, "POST", target, {"ResetType": "On"})
    check("On: 200 and the system is On", s == 200 and call(base, "GET", SYS)[2]["PowerState"] == "On", s)
    s, _, b = call(base, "POST", target, {"ResetType": "On"})
    check("action with no effect: 200 with the NoOperation message [7.11]", s == 200 and "NoOperation" in b["error"]["code"], b)

    # --- asynchronous action
    st.async_reset = True
    s, h, b = call(base, "POST", target, {"ResetType": "GracefulRestart"})
    check("slow action: 202 Accepted with a Location task monitor [12.2]", s == 202 and "/TaskMonitors/" in h.get("Location", ""), (s, h))
    check("202 carries Retry-After and a Task body", "Retry-After" in h and b["@odata.type"].startswith("#Task."))
    mon = h["Location"]
    s, h, b = call(base, "GET", mon)
    check("polling the monitor while running returns 202 [12.2]", s == 202 and b["TaskState"] == "Running", (s, b))
    clock[0] += 10
    s, h, b = call(base, "GET", mon)
    check("halfway: PercentComplete is about 50", s == 202 and 40 <= b["PercentComplete"] <= 60, b.get("PercentComplete"))
    clock[0] += 11
    s, h, b = call(base, "GET", mon)
    check("when done the monitor returns the original operation's result: 200 + Success [12.2]",
          s == 200 and "Success" in b["error"]["code"], (s, b))
    tid = mon.rsplit("/", 1)[1]
    s, _, b = call(base, "GET", f"/redfish/v1/TaskService/Tasks/{tid}")
    check("the Task resource now says Completed with EndTime", b["TaskState"] == "Completed" and "EndTime" in b, b)
    s, _, _ = call(base, "DELETE", mon)
    check("cancelling a finished task is refused: 409", s == 409, s)

    s, h, b = call(base, "POST", target, {"ResetType": "ForceRestart"})
    mon2 = h["Location"]
    clock[0] += 3
    s, _, _ = call(base, "DELETE", mon2)
    check("cancelling a running task: 204 [12.2]", s == 204, s)
    s, _, _ = call(base, "GET", mon2)
    check("monitor of a cancelled task answers 410 Gone [12.2]", s == 410, s)
    s, _, b = call(base, "GET", "/redfish/v1/TaskService/Tasks")
    check("TaskService lists the tasks", b["Members@odata.count"] == 2, b)
    st.async_reset = False

    # --- push events
    sink = Sink()
    s, _, _ = call(base, "POST", "/redfish/v1/EventService/Subscriptions", {"Destination": sink.url}, auth=("operator", "operpass"))
    check("Operator cannot create subscriptions in this mock (ConfigureManager): 403", s == 403, s)
    s, _, _ = call(base, "POST", "/redfish/v1/EventService/Subscriptions", {"Protocol": "Redfish"})
    check("subscription without Destination: 400 [12.1.2]", s == 400, s)
    s, h, b = call(base, "POST", "/redfish/v1/EventService/Subscriptions",
                   {"Destination": sink.url, "Context": "gpu-rack-7", "Protocol": "Redfish", "EventFormatType": "Event",
                    "RegistryPrefixes": ["ResourceEvent"]})
    check("subscribe: 201 Created + Location + EventDestination body [12.1.2]", s == 201 and "Location" in h and b["Context"] == "gpu-rack-7", (s, b))
    sub_uri = h["Location"]
    call(base, "POST", target, {"ResetType": "ForceOff"})
    time.sleep(0.3)
    check("an event is POSTed to the destination when the power state changes [12.1]", len(sink.events) == 1, sink.events)
    ev = sink.events[0]["Events"][0] if sink.events else {}
    check("event has Context, MessageId and OriginOfCondition",
          sink.events and sink.events[0]["Context"] == "gpu-rack-7" and ev["MessageId"].startswith("ResourceEvent.")
          and ev["OriginOfCondition"]["@odata.id"] == SYS, sink.events)
    n = len(sink.events)
    call(base, "POST", "/redfish/v1/EventService/Actions/EventService.SubmitTestEvent", {"MessageId": "Base.1.17.TestEvent"})
    time.sleep(0.2)
    check("a Base test event is filtered out because the subscription asked only for ResourceEvent [12.1.5]", len(sink.events) == n)
    s, _, _ = call(base, "DELETE", sub_uri)
    check("unsubscribe with DELETE: 204 [12.1.2]", s == 204, s)
    call(base, "POST", target, {"ResetType": "On"})
    time.sleep(0.2)
    check("after unsubscribing no more events arrive", len(sink.events) == n)
    s, _, _ = call(base, "GET", sub_uri)
    check("the removed subscription answers 404 [12.1.2]", s == 404, s)

    # --- delivery failures end a subscription (TerminateAfterRetries)
    s, h, b = call(base, "POST", "/redfish/v1/EventService/Subscriptions",
                   {"Destination": "http://127.0.0.1:1/nothing", "DeliveryRetryPolicy": "TerminateAfterRetries"})
    dead = h["Location"]
    for i in range(3):
        call(base, "POST", target, {"ResetType": "ForceOff" if i % 2 == 0 else "On"})
    s, _, _ = call(base, "GET", dead)
    check("after 3 failed deliveries the subscription is terminated (TerminateAfterRetries)", s == 404, s)

    # --- server-sent events
    call(base, "POST", target, {"ResetType": "On"})        # make sure the next ForceOff really changes the state
    lines = []
    def reader():
        r = urllib.request.Request(base + "/redfish/v1/EventService/SSE?$filter=MessageId%20eq%20'ResourceEvent.ResourceStatusChanged'&_max=3",
                                   headers={"Authorization": "Basic YWRtaW46YWRtaW5wYXNz", "Accept": "text/event-stream"})
        with urllib.request.urlopen(r, timeout=10) as resp:
            lines.append("CT:" + resp.headers.get("Content-Type", ""))
            for raw in resp:
                lines.append(raw.decode().rstrip("\n"))
    t = threading.Thread(target=reader, daemon=True); t.start()
    time.sleep(0.5)
    s, _, b = call(base, "GET", "/redfish/v1/EventService/Subscriptions")
    check("opening an SSE stream creates a subscription resource [12.5.2]", b["Members@odata.count"] == 1, b)
    call(base, "POST", target, {"ResetType": "ForceOff"})
    call(base, "POST", "/redfish/v1/EventService/Actions/EventService.SubmitTestEvent", {"MessageId": "Base.1.17.TestEvent"})
    t.join(6)
    check("SSE content type is text/event-stream [12.5.1]", any(l.startswith("CT:text/event-stream") for l in lines), lines[:2])
    check("the stream has an id: line and a data: line with the Event JSON [12.5.2]",
          any(l.startswith("id: ") for l in lines) and any(l.startswith("data: ") and "ResourceStatusChanged" in l for l in lines), lines)
    check("the filtered-out test event did not appear on the stream", not any("TestEvent" in l for l in lines))
    time.sleep(0.4)
    s, _, b = call(base, "GET", "/redfish/v1/EventService/Subscriptions")
    check("closing the stream removes its subscription [12.5.2]", b["Members@odata.count"] == 0, b)

    print(f"\n{ok_count} passed, {fail_count} failed")
    srv.shutdown()
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
