import redfish
c = redfish.redfish_client(base_url="https://127.0.0.1:18720", username="admin", password="adminpass", default_prefix="/redfish/v1")
c.login(auth="session")
r = c.get("/redfish/v1/Systems/System_0")
print(r.status, r.dict["PowerState"])
r = c.post("/redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset", body={"ResetType": "ForceOff"})
print(r.status)
print(c.get("/redfish/v1/Systems/System_0").dict["PowerState"])
c.logout()
