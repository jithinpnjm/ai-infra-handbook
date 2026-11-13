---
id: "c07-04"
title: "7.4 Redfish authentication, sessions and security"
sidebar_label: "7.4 Redfish authentication, sessions and security"
sidebar_position: 4
description: "How to log in to a Redfish service safely: HTTPS and certificates, Basic authentication versus sessions, tokens and timeouts, roles and privileges, creating service accounts, lockout, forced password change, and a 44-check lab that proves each rule on a mock service"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 7.4 Redfish authentication, sessions and security

| | |
|---|---|
| Level | Beginner to Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`auth_lab.py`: 44 checks pass against mock; **untested** on live BMC) |

## Why this matters for AI infrastructure

Picture a node that will not boot after a firmware update. The only way in is through its BMC, the baseboard management controller. That is the small computer on the server board that keeps working when the main operating system is off. A BMC can turn a server off, rewrite its firmware and change its settings. Whoever holds the BMC password controls the machine below the operating system, in the layer where your normal security tools cannot see. Now picture a fleet of 1,000 BMCs that all share one factory password. One leaked password puts the whole fleet at risk.

This chapter shows how Redfish decides who you are and what you may do. Redfish is the web-based API that modern BMCs speak. It also shows how to set up accounts and scripts so that your automation stays safe, even when a human makes a mistake at the end of a long shift.

## Prerequisites and outcomes

Start with 7.1 to 7.3, because this chapter builds on them. The chapter follows the order of a login. It starts with the encrypted connection, then looks at the two ways a script can prove its identity, then at roles and permissions, and then at the protections that slow down guessing. The lab at the end runs the rules against a mock service, so you can watch each one work before you trust it on hardware.

## 1. Start with the basics: encryption first

Picture a teammate who pastes a working script into a ticket. The first line of the script is `curl -k`, and it works, so nobody questions it. Six months later the same script runs in a data center where another tenant shares the network switch. The danger was there from the start, hidden behind a flag that looked harmless. This section explains where that danger comes from.

Every Redfish request can carry a password and a command across the network. Anyone who can watch that traffic could read them, so the traffic must be encrypted before anything else. TLS, which stands for Transport Layer Security, is the protocol that does the encrypting. HTTPS is plain HTTP wrapped in TLS. The spec says services shall support **TLS 1.2 or later**. They shall also offer only cipher suites marked "Recommended" by the IANA TLS registry. A cipher suite is the set of algorithms that the two sides agree on to scramble the traffic, and IANA (the Internet Assigned Numbers Authority) keeps the official list. Any request that uses HTTP Basic authentication must use HTTPS. Operations with sensitive data, such as a firmware update that includes a user name and password for a download server, should use HTTPS only.

Certificates come next. A certificate is the document a server shows to prove that it is who it claims to be. A BMC ships with a self-signed certificate, which means the BMC signed its own document and no outside authority vouches for it. Your computer has no reason to trust it, so your tools will complain. The quick fix is `curl -k`, which skips the check. That also removes the protection that stops someone on the network from pretending to be the BMC, because a fake BMC would get the same silent acceptance. Use `-k` only in a lab. For production, the spec says services shall support replacing the default certificate, and certificates must be X.509 v3. X.509 is the standard format for certificates, and version 3 is the one that carries the extra fields modern tools check.

Replacing the certificate is a standard action. The Redfish schema guide describes `CertificateService.ReplaceCertificate`. It takes three values: the new certificate text, its type (`PEM`, the text format that wraps a certificate between BEGIN and END lines), and a link to the certificate being replaced.

```json
{
  "CertificateUri": { "@odata.id": "/redfish/v1/Managers/BMC/NetworkProtocol/HTTPS/Certificates/1" },
  "CertificateString": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "CertificateType": "PEM"
}
```

You send this body with a POST to the action address on the `CertificateService`. The guide shows that address as `.../Actions/CertificateService.ReplaceCertificate`. There is also `GenerateCSR`. It asks the BMC to make a signing request, so the private key never leaves the BMC. Paths such as `/Managers/BMC/...` come from the guide's example and differ per platform, so discover them from the service root.

:::note A note on older NVIDIA-DevOps notes
Some older NVIDIA-DevOps notes show a plain `POST` of `CertificateString` to `.../NetworkProtocol/HTTPS/Certificates`. The schema guide's documented way to replace a certificate is the `ReplaceCertificate` action above. A plain POST to the collection may work on some BMCs, but that could not be confirmed, so prefer the action and test on one machine first.
:::

## 2. Two ways to log in

Every script you write for a BMC has to answer one question first: how should it prove who it is? Your first script usually starts with a single line that sends a user name and password. That is the quickest path, and it is also the one that sends the password most often. Redfish gives you two options, and the spec says a service must support both. A client that uses Basic must never be forced to create a session.

| | HTTP Basic | Redfish session |
|---|---|---|
| How | send user and password with **every** request | log in once, then send a token with every request |
| Header | `Authorization: Basic <base64 of user:password>` | `X-Auth-Token: <token>` |
| Password exposure | on every request | once, at login |
| Good for | a single quick command | scripts and tools |
| Can be turned off | yes, with `HTTPBasicAuth` in `AccountService` (`Enabled`, `Disabled` or `Unadvertised`) | no |

Read the table by asking two questions. How often does the password travel? Can an administrator switch the method off? Base64 is an encoding, and it is not encryption. Anyone who sees a Basic header can decode the password in a moment, which is why Basic is only allowed over HTTPS. If multi-factor authentication (MFA, a second proof such as a one-time code on top of the password) is enabled, the spec says services must refuse Basic for accounts that did not opt out. In that case, sessions become the only way in.

The spec says clients **should** use sessions "for improved performance and security". The diagram below shows the whole life of a session, from login to logout. Follow it from the top. The client sends the password once, gets a token back, and reuses that token until the session ends.

### The session steps

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Redfish service
    C->>S: POST /redfish/v1/SessionService/Sessions with UserName and Password
    S-->>C: 201 Created, X-Auth-Token, Location (the session address), Session body
    Note over C: Keep the token secret and keep the Location
    C->>S: GET or PATCH or POST with header X-Auth-Token
    S-->>C: answers
    Note over S: Idle longer than SessionTimeout and the session is closed
    C->>S: DELETE the Location address when finished
    S-->>C: 204 No Content
```

Notice that the password travels once, at login, and the token travels with every request after that. Think of the token as a hotel key card. The card opens the door for you, but anyone who finds the card can open it too, so you guard it the same way you guard the password. To find the Sessions address, read it from the service root (`Links` / `Sessions`) or from `SessionService`. Both must be the same. The `POST` that creates a session must use HTTPS, and it needs no auth header. If a service runs both HTTP and HTTPS, the HTTP login should redirect you to HTTPS.

The answer **must** contain the `X-Auth-Token` header, the `Location` header and the full Session body. The body's `Password` is `null`, because services must never send passwords back. The session id is the last part of `Location`, and it is not the token. The id names the Session resource, so an administrator can list it or end it. The token is the secret that only the client which logged in holds. Keep those two apart in your head, because mixing them up is a common source of confusion when someone asks why they cannot end a session with a token they copied from a log.

Sessions do not expire at a fixed time on the clock. They time out when they go idle. While you keep sending requests inside the timeout, the token stays valid. A service can also set an absolute timeout through `AbsoluteSessionTimeout` in the schema guide, which ends the session after a fixed span no matter how busy it is. To log out, send a `DELETE` to the Session address. An administrator can end other users' sessions the same way. Services must not use HTTP cookies to authenticate requests, so the token travels only in its own header.

**Always log out.** A BMC is a small computer with limited memory, and the spec leaves the number of open sessions up to each implementation. Picture a script that logs in 5,000 times and never logs out. It may lock itself out of the BMC. In your code, put the logout in a `try/finally` so it always runs, even when an error interrupts the work in the middle.

## 3. Who may do what: roles and privileges

Imagine a new hire who needs to restart a stuck GPU node on Monday morning but must not create accounts. Knowing who you are is only half the job. Once the service has checked your login, it still has to decide what you may change, and it has to tell the restart apart from the account change. The spec handles this with three pieces. A **privilege** is a single permission, such as `Login`, `ConfigureComponents` or `ConfigureUsers`. A role is a named set of privileges. Each user account has exactly one role, stored in `RoleId`.

The spec requires three standard roles. Read the table row by row, and notice that each role contains everything the role below it has, plus more. That nesting is what makes the table easy to reason about. If you know what the top row can do, you know that the rows below it are smaller subsets.

| Role | Privileges |
|---|---|
| `Administrator` | Login, ConfigureManager, ConfigureUsers, ConfigureComponents, ConfigureSelf |
| `Operator` | Login, ConfigureComponents, ConfigureSelf |
| `ReadOnly` | Login, ConfigureSelf |

The privilege names say what they allow. `ConfigureManager` changes settings of the BMC itself, such as the network, protocols and certificates. `ConfigureUsers` creates, deletes and changes accounts. `ConfigureComponents` changes the computer and its parts, and runs actions such as a reset. `ConfigureSelf` changes your own account, for example your password. `Login` lets you read. So the new hire on Monday gets the Operator role, which can reset the node but cannot touch accounts.

Services may add optional roles, OEM roles and custom roles. OEM means the hardware vendor's own extra roles. The spec lists `SystemAdministrator`, `SystemOperator`, `StorageAdministrator` and `StorageBackupOperator` as optional examples. Standard roles cannot be modified, so if the three standard roles do not fit your team, you add a custom role beside them instead of editing them.

Each type of operation needs certain privileges, and a service should publish those rules as a **Privilege Registry**. The registry is a lookup table that says which privilege each kind of request needs. For example, `GET` on a Manager needs `Login`, and `PATCH` needs `ConfigureManager`. Some properties follow different rules from their parent. The `Password` property in an account needs `ConfigureSelf` or `ConfigureUsers`, while other fields need `ConfigureUsers`. That is how you can change your own password but not someone else's.

### 3.1 Privilege Registry overrides, logical AND/OR, and Restricted Roles (DSP0266 §13.4.2–13.4.3)

Picture a security officer who wants one role that only the officer can change, even though the normal administrators run the BMC every day. A single role table is not always precise enough for that. The Privilege Registry, defined in DSP0266 §13.4.3, can express finer rules. DSP0266 is the Redfish specification document itself, and the section numbers point into it. Each resource type, called an `Entity`, has a base `OperationMap`. That map lists the privileges needed for `GET`, `HEAD`, `PATCH`, `POST`, `PUT` and `DELETE`.

The map also has its own logic. Separate objects inside an operation's array mean logical OR, which means that any one of them is enough. For example, `[{"Privilege": ["ConfigureUsers"]}, {"Privilege": ["ConfigureSelf"]}]` means either `ConfigureUsers` or `ConfigureSelf` is enough. Several names inside the same `"Privilege"` array mean logical AND, which means that all of them are needed. So `[{"Privilege": ["ConfigureComponents", "OEMSysAdminPriv"]}]` requires both privileges. The spec covers this in §13.4.3.8.

Sometimes a property, a single URI or a resource's place in the tree needs a different privilege from the base `Entity`. The registry handles that with three override types, and they apply in a strict order (§13.4.3.4, Table 43). `PropertyOverrides` comes first. It can set a privilege for one property. For example, it can let `ConfigureSelf` or `ConfigureUsers` change the `Password` on `ManagerAccount`, while every other property on `ManagerAccount` still needs `ConfigureUsers`.

`ResourceURIOverrides` comes next. It targets specific URI instances, such as `/redfish/v1/Systems/VM6`. `SubordinateOverrides` has the lowest precedence. It changes the required privilege based on where a resource sits in the tree. DSP0266 §13.4.3.6 gives a classic case. An `EthernetInterface` under `ComputerSystem` needs `ConfigureComponents` to `PATCH`, so an `Operator` can configure a host NIC (network interface card). An `EthernetInterface` under `Manager` needs `ConfigureManager`, so only an `Administrator` can reconfigure the BMC's own out-of-band management NIC. Out-of-band means the management path that works separately from the host's operating system. Reading the same rule twice, once for the host and once for the BMC, shows why the position of a resource in the tree matters as much as its name.

Restricted roles guard against privilege escalation. Escalation means someone grants themselves more power than they were given. Suppose you want to stop a general `Administrator` from changing a dedicated security officer role. The service can mark that role `Restricted: true` and name an `AlternateRoleId` for normal use. It can also list `RestrictedPrivileges` and `RestrictedOemPrivileges` in `AccountService`. Services shall not let users create, delete or modify accounts assigned to a restricted role, except to toggle `Enabled`. They also must not assign restricted privileges to custom roles (§13.4.2.2). When you design a role for a new team, check the override rules first, because one role can behave differently on a host and on the BMC.

### 3.2 Client Certificate Authentication (mTLS) and OAuth 2.0 JWTs (DSP0266 §13.3.5 & §13.4.4)

Picture a company with hundreds of BMCs. It wants its single sign-on system to decide who can log in, instead of keeping a separate list of passwords on each box. Passwords and sessions are not the only options. DSP0266 also describes two mechanisms for enterprise and zero-trust fleets. Zero trust means that no request is believed just because it comes from inside the network. The first is mutual TLS, or mTLS, which uses client certificates (§13.3.5). Mutual means that both sides show a certificate, not only the server. When it is enabled under `AccountService.MultiFactorAuth.ClientCertificate`, the BMC asks for a client X.509 certificate during the TLS handshake, which is the first exchange when a connection opens. It checks that certificate against the trusted `CertificateCollection`. Then it checks revocation through the configured OCSP (Online Certificate Status Protocol) servers. OCSP is the way a server asks whether a certificate has been cancelled.

The boolean `RespondToUnauthenticatedClients` controls what happens on failure. If it is `true`, or unsupported, the TLS handshake completes. The BMC can then still serve unauthenticated resources such as `/redfish/v1/`, or return structured `401` JSON errors. If it is `false`, the BMC aborts the TLS handshake at once when a client certificate is invalid. The first setting is friendlier to debugging. The second is stricter, and it reveals less to a stranger who is probing the port.

The second mechanism is delegated authorization with OAuth 2.0 bearer JWTs (§13.4.4). OAuth 2.0 is a standard way for one system to grant access on behalf of a user, and a JWT (JSON Web Token) is a signed block of JSON that carries the grant. A Redfish service can act as an OAuth 2.0 resource server, configured through `AccountService.OAuth2`. A resource server is the service that holds the data and checks the tokens. It then accepts RFC 7519 JSON Web Tokens (JWTs) sent as `Authorization: Bearer <jwt>`. DSP0266 sets rules for these tokens in Tables 44 and 45. The JOSE header must name the signature algorithm in `alg`, such as `"RS256"`, and services shall not accept `alg: "none"`. The payload shall include `iss`, the issuer, `sub`, the subject, `aud`, the audience that matches the service, and `scope`. It may also carry `exp`, `nbf`, `iat` and `jti`. The `scope` claim is a space-delimited list. Each entry maps to a Redfish role, such as `Redfish.Role.<RoleId>`, or to one privilege, such as `Redfish.Privilege.<PrivilegeId>`. The example form is `"Redfish.Role.Operator"`.

**Least privilege for automation.** Least privilege means giving each account only the power its job needs. Do not share the `admin` account, because a shared account hides who did what. Create accounts by purpose, as the table below shows.

| Account | Role | Used by |
|---|---|---|
| `prom_scraper` | `ReadOnly` | monitoring that reads sensors |
| `fleet_ops` | `Operator` | restarts and power actions |
| `fw_update` | `Administrator` (the standard roles are broad, so check whether your BMC offers a narrower custom role) | firmware jobs only |
| a personal account | as needed | each person, so logs show who did what |

The lab in section 5 checks this rule. A `ReadOnly` user can read, but a change returns 403. An `Operator` can change a system, but creating an account returns 403.

## 4. Protections against guessing and stale passwords

Picture a junior engineer who mistypes a password a few times at the end of a long shift. Left alone, a BMC would let anyone keep guessing passwords, and it would let an old password stay valid forever. The Account Service has settings that slow down guessing and retire old credentials. The Account Service schema in the Resource Guide lists these settings. The table below shows the ones that matter most for your scripts. Each row is a switch or a limit that the administrator sets once, and then the BMC applies it to every login.

| Setting | Meaning |
|---|---|
| `AccountLockoutThreshold` | failed logins before the account locks |
| `AccountLockoutDuration` | seconds the account stays locked (0 means never lock) |
| `AccountLockoutCounterResetAfter`, `AccountLockoutCounterResetEnabled` | when the failure count is cleared |
| `AuthFailureLoggingThreshold` | failures before the service writes a log entry |
| `MinPasswordLength` | shortest allowed password |
| `HTTPBasicAuth` | is Basic allowed |
| `RequireChangePasswordAction` | passwords can only be changed with the `ChangePassword` action, not by `PATCH` |
| `PasswordExpirationDays` (in the account resource) | password lifetime |

The spec's rules explain how these settings behave in practice. Error messages must not leak information. An unknown user and a wrong password must look the same, and a locked account should look like a wrong password. The reason is simple. If the answers differ, an attacker can learn which user names exist, and which accounts are locked, just by trying them. The lab checks this. Passwords are write-only, too. Any response property that holds a password "shall be null".

Atomic password change is the next rule. Atomic here means the change either happens completely or does not happen at all. If `RequireChangePasswordAction` is true, the service rejects a `PATCH` of `Password`. You must use the `ChangePassword` action instead. That action asks for `SessionAccountPassword`, which is your current password, or the administrator's password when you change someone else's. This protects you from a stolen session token being used to lock you out by changing your password. The token alone is not enough, because the attacker also needs the password you are changing away from.

Password change required works differently. An account with `PasswordChangeRequired: true` can log in, for example with a factory-default password or after an administrator's reset. But the login answer includes a `PasswordChangeRequired` message, and every other request gets **403** until the password changes. While the flag is set, the account may read itself, change its own password by `PATCH` or `ChangePassword`, and delete its own sessions. Once the password changes, the flag becomes false. Changing an account can also close its sessions, so the user must log in again. Services should store passwords with a one-way hash, which is a scrambled form that cannot be turned back into the original password.

Time-based One-Time Password (TOTP) multi-factor authentication (DSP0266 §13.5.5) follows the same pattern. TOTP is a six-digit code that changes every short while, and both the BMC and the user's phone share the secret that makes the codes. When RFC 6238 TOTP MFA is enabled and an account has no TOTP secret key yet, a session login without `Token` succeeds. The answer carries `@Message.ExtendedInfo` with `GenerateSecretKeyRequired`. That bootstrap session is restricted, just like the password case. Normal resources return `403 Forbidden` with `GenerateSecretKeyRequired` until the user calls `POST .../Actions/ManagerAccount.GenerateSecretKey`. The user may also call `VerifyTimeBasedOneTimePassword`. Then the user closes the session and logs in again, with `"Token": "<6-digit-otp>"` in the session `POST` body.

A new DGX or BMC often arrives with a default password that must be changed. Your provisioning script has to handle the state where login works but nothing else does. Without that handling, the script fails in confusing ways. It sees a successful login, then a wall of 403 errors, and it may report the wrong problem. Handle the state on purpose, and the script tells you exactly what to do next.

## 5. The lab

Imagine you join a team that relies on these rules, and a colleague asks you to prove that the account behaviour works before anyone trusts it on the vendor's hardware. Reading about these rules is one thing. Watching a service enforce them is another, and the lab does exactly that. Run it from the chapter's code folder.

```bash
cd code/part07
python3 auth_lab.py
```

The script starts a mock service and moves a fake clock forward. A mock is a stand-in that copies the behaviour you want to test, here the Redfish rules, without needing real hardware. Because the clock is fake, a five-minute timeout and a 30-second lockout are tested in milliseconds. The lab runs 44 checks. Here is a selection of the output:

```text
PASS  login returns 201 with X-Auth-Token, Location and a Session body [13.3.4.2]
PASS  session body never shows the password (it is null) [13.2]
PASS  idle longer than SessionTimeout: session is gone, 401 [13.3.4.3]
PASS  unknown user and wrong password give the same 401 and message [13.3.2.3]
PASS  after 3 bad attempts the account is locked: even the right password gets 401
PASS  after AccountLockoutDuration the account works again
PASS  Operator cannot create accounts (needs ConfigureUsers): 403
PASS  ReadOnly cannot change components: 403
PASS  a user cannot promote themselves: 403
PASS  account with PasswordChangeRequired can log in and is told so (ExtendedInfo) [13.5.4]
PASS  ...but everything else is 403 PasswordChangeRequired [13.5.4]
PASS  PATCH own Password clears the flag [13.5.4]
PASS  ChangePassword with a wrong SessionAccountPassword is refused: 401 [13.5.3]
PASS  an admin password reset closes that user's open sessions [13.5.2]
PASS  administrator can disable HTTP Basic [13.3.3]
...
44 passed, 0 failed
```

Read the output as a set of promises. Each PASS line is one rule the service keeps, and the bracketed number points to the section of DSP0266 that states it. Read the file `auth_lab.py` after you run it. It doubles as a clear list of what a good Redfish login system does. If you ever build tooling for BMC accounts, these checks make a useful acceptance list.

While building the lab, one check failed for a reason worth remembering. The test sent a stale session token together with a Basic header. The service looked at the token first, found it expired, and answered 401 without trying Basic. That is real behaviour to remember: **a bad token is not rescued by a good password header.** Remove stale tokens when you log in again. These steps were not run on a live cluster or a live BMC, so the mock results show the rules and not the behaviour of any particular vendor.

## 6. Safe handling in your own scripts

Your script works on the lab BMC. Then it runs against the whole rack at night, and one wrong setting turns into a locked fleet. Most of the protections above depend on how your own scripts behave, and the service cannot save you from a script that ignores them. Keep these eight habits in every script that talks to a BMC.

Treat the list as a checklist that you run through before any script touches a production BMC. Most of the items are cheap to follow when you write the script, and very expensive to add after an incident. The first two items protect the secret itself, the middle three protect the session and the account, and the last three protect the fleet from your own mistakes. Read each habit as an answer to a specific way that a script can go wrong at scale.

1. **Use HTTPS and verify the certificate.** Install your own CA on the BMCs, as section 1 describes, and point tools at it with `curl --cacert ca.pem`. A CA, or certificate authority, is the trusted party that signs the BMC certificates. Use `-k` or `verify=False` only in a lab.
2. **Keep passwords off the command line.** *Supercomputers for Linux SysAdmins* warns about the same risk with `ipmitool -P`. Anything you type on a command line can end up in shell history or in the process list that other users can see. For `curl`, use `--netrc-file` or a `--config` file with mode 600, which means only the owner can read it. In Python, read the password from your secret store.
3. **Use sessions.** Log in once per machine, and log out in a `finally` block.
4. **Treat the token like a password.** Never print it in logs.
5. **Use one account per purpose.** Give each person a personal account, so logs show who did what.
6. **Check for `PasswordChangeRequired`** the first time you contact new hardware.
7. **Audit regularly.** Chapter 7.1 has a credential audit tool, and NVIDIA Base Command Manager (BCM) has `credentialsoverview`, which does the same job.
8. **Rate-limit your scripts.** Many failed logins can lock an account and block the real owner. Stop on the first 401, and do not retry hundreds of times.

### 6.1 Anatomy of a session-table exhaustion outage

Suppose a monitoring team writes a naive health scraper for a large GPU cluster. A scraper is a program that reads numbers from a system on a schedule. Every thirty seconds, a cron job opens a new Redfish session on each BMC. It reads the chassis sensors, prints the temperatures, and exits the Python process without calling `DELETE` on the session URI.

Each embedded BMC has a small, fixed table of active sessions in RAM. The Redfish specification leaves the maximum number of simultaneous open sessions up to the firmware implementation. While a session stays idle, the BMC must keep it until `SessionTimeout` expires. Take the default timeout of thirty minutes. If the scraper logs in twice a minute without logging out, the arithmetic is simple: two logins a minute for thirty minutes is sixty sessions. One script therefore consumes sixty session slots per BMC.

The table fills long before the thirty-minute idle timer reclaims the first orphaned token. From that point, every new login is rejected. That includes logins from your provisioning engine, your Slurm power-fencing scripts and your human operators. Power fencing is the step where the scheduler cuts power to a node that has gone bad. The node is still running and its hardware is healthy. Yet the out-of-band control plane has locked you out, and the team that needs it most cannot reach it.

Preventing this takes three habits in every client you write. First, wrap every session login in a `try/finally` block, so the `DELETE` runs even when an exception interrupts the script. Second, reuse one long-lived session across several reads to the same BMC, instead of logging in once per metric. Third, give your scraper its own dedicated `ReadOnly` account. An administrator can then inspect `/redfish/v1/SessionService/Sessions`, see which `UserName` owns the orphaned sessions, and end them one at a time with `DELETE`. Active maintenance sessions keep running.

### 6.2 How the Privilege Registry governs multi-team operations

In a mature AI data center, three teams touch the server fleet every day. The observability team scrapes temperatures, fan speeds and power consumption. The compute operations team drains and reboots wedged nodes when training jobs hang. The platform security and hardware engineering team rotates X.509 certificates, updates firmware and manages user accounts.

If all three share the factory `admin` account, one bug in a metrics scraper, or one leaked environment variable in a CI runner, gives full control over every BMC in the building. A CI runner is the build machine that runs automated jobs. The Privilege Registry lets you separate these duties, so that each team's mistake stays inside that team's power.

When the observability scraper uses a `ReadOnly` account, its role carries only `Login` and `ConfigureSelf`. The registry maps `GET` and `HEAD` across `ComputerSystem`, `Chassis`, `Sensor` and `Manager` to the `Login` privilege. Suppose someone changes the scraper to send a `POST` to `ComputerSystem.Reset`, or a `PATCH` to `Bios/Settings`. The BMC checks the `OperationMap` for those endpoints, sees that `ConfigureComponents` is required, and rejects the request with HTTP 403 Forbidden.

The compute operations team gets an `Operator` account. That role adds `ConfigureComponents` on top of `Login` and `ConfigureSelf`. An operator can reboot a hung GPU node, set a one-time PXE boot override, or adjust a chassis power cap. PXE is the network boot method, and a one-time override tells the node to boot from the network just once. But if an operator tries to create a backdoor user account under `/redfish/v1/AccountService/Accounts`, or to disable TLS certificate checks under `/redfish/v1/Managers/BMC/NetworkProtocol`, the registry blocks the call. Account changes need `ConfigureUsers`. BMC network changes need `ConfigureManager` through the `SubordinateOverrides` rule. Only the `Administrator` role holds those privileges.

Give each team the lowest role that covers its work, and keep `admin` out of automation.

### 6.3 Designing zero-touch factory password rotation on Day 0

A pallet of new GPU servers has just arrived on the data-center floor. Day 0 is the first day a machine is on the network, before anyone has configured it. Each BMC ships with either a well-known factory default password or a unique per-chassis password printed on the physical pull-tab. A pull-tab is the small card tucked into the chassis with the initial credentials. On hardened platforms, the factory account also sets `PasswordChangeRequired` to `true`.

If your Day-0 discovery pipeline assumes that a successful 201 Created from `/redfish/v1/SessionService/Sessions` means the node is ready for inventory and firmware checks, it fails on the very next step. As soon as the script sends `GET /redfish/v1/Systems`, the BMC returns 403 Forbidden with the `PasswordChangeRequired` message from the Base Message Registry. The login looked fine, so the failure seems to come from nowhere, which is why this state trips up so many scripts.

A resilient Day-0 workflow handles this state explicitly, right after the first session is up:

1. Read the 201 Created login body for `@Message.ExtendedInfo`. If any entry contains `PasswordChangeRequired`, take the bootstrap rotation branch before running any hardware discovery.
2. Check whether `RequireChangePasswordAction` is `true` in `AccountService`, either by following the account link or by querying `/redfish/v1/AccountService`.
3. If it is `true`, call the `ManagerAccount.ChangePassword` action with both `NewPassword` and `SessionAccountPassword` set to the factory password. If it is not, send a `PATCH` with the new password to the user's own `ManagerAccount` URI.
4. Read the `ManagerAccount` back to confirm that `PasswordChangeRequired` is now `false`. Then verify that `GET /redfish/v1/Systems` returns 200 OK.
5. Once the bootstrap account uses your vault-managed secret, create the dedicated `ReadOnly` and `Operator` service accounts. Then disable `HTTPBasicAuth` on `AccountService`, so all later automation uses session tokens only.

Build this state machine into your onboarding script before the first discovery call. Each step has one job, and each check tells the script whether it can move on.

### 6.4 External directory integration and certificate lifecycle

Local `ManagerAccount` resources work well for small clusters and for emergency break-glass access. Break-glass access is a last-resort account kept for the moment when every normal path fails. Human administrators should not, however, hold local accounts scattered across hundreds of BMCs. When an engineer leaves the team, access should be revoked in one central directory. It should not take a fleet-wide `DELETE` loop across every rack.

Redfish supports central directory integration through `ExternalAccountProvider` resources under `AccountService`. Those resources support LDAP, Active Directory, TACACS+ and OAuth 2.0. LDAP and Active Directory are the common directory services that store user accounts and their groups. TACACS+ is a protocol used on network gear for the same job. An administrator configures the directory server addresses, the TLS trust certificates, and `RemoteRoleMapping` rules. Those rules map enterprise directory groups straight to Redfish roles such as `Administrator`, `Operator` and `ReadOnly`. You then keep only one vault-escrowed local `Administrator` account on each BMC. Vault-escrowed means the password is stored in a secret vault and used only in an emergency. That account is for out-of-band break-glass recovery, for the case where the corporate directory or the management network is unreachable during a facility outage.

Decide which directory groups map to which roles before you roll out the first BMC. Once the mapping is in place, removing a person from the directory group is the change you make, and no loop has to visit every BMC.

## Exercises

Try these in order. Each one asks you to read, run or write something, so try it yourself before you look at the checkpoint answers below.

1. Run `python3 code/part07/auth_lab.py`, then read lines 56–70 of `code/part07/auth_lab.py`. Check that an unknown username (`nosuchuser`) gives a `401 Unauthorized` status. Check that a wrong password for a valid user (`admin`) gives the same status. Check that a correct password on a locked account (`viewer` after `3` failed attempts) also gives the same status and the same generic message (`DSP0266` §13.3.2.3). Ask yourself, or your team, why the three cases must look identical.
2. Use the table of required roles (`Administrator`, `Operator`, `ReadOnly`) and the Privilege Registry override rules (`ConfigureManager`, `ConfigureComponents`, `ConfigureUsers`) to decide which role each job needs. Start with a Prometheus `dcgm`/`redfish` telemetry scraper (`prom_scraper`). Then take a Slurm fencing or reboot script (`fleet_ops`). Finish with a BMC certificate rotation playbook. Explain each choice in one sentence, so you can defend it to your team.
3. Add a 45th check to `code/part07/auth_lab.py`. It should confirm that an `Operator` who sends `PATCH /redfish/v1/AccountService {"HTTPBasicAuth": "Disabled"}` gets `403 Forbidden`. Which privilege does that change need? Changing `AccountService` needs `ConfigureManager` or `ConfigureUsers`, and an `Operator` has neither.
4. Write a Python context manager called `redfish_session`, decorated with `@contextlib.contextmanager`. It takes `base_url`, `username` and `password`, posts to `/redfish/v1/SessionService/Sessions`, and yields `(token, session_uri)`. It must send `DELETE` to `session_uri` in a `finally:` block. Why does the logout need to run even when the caller's work raises an exception?
5. Trace lines 114–128 of `code/part07/auth_lab.py`, where the `factory` account has `PasswordChangeRequired: true`. Why does `GET /redfish/v1/Systems/System_0` return `403 Forbidden` right after login? Which three operations does DSP0266 §13.5.4 allow during that restricted session? How does `ChangePassword` with `SessionAccountPassword` prevent a session-hijacking lockout when `RequireChangePasswordAction: true`?
6. Run `python3 code/part07/tls_setup.py /tmp/lab_pki` and inspect the X.509 v3 extensions it generates. Look for `subjectAltName=IP:127.0.0.1,DNS:localhost`, `basicConstraints=CA:FALSE`, and `extendedKeyUsage=serverAuth`. Then explain why `CertificateService.GenerateCSR` followed by `CertificateService.ReplaceCertificate` is safer than generating private keys on a central workstation.

## 8. Interview angles

These questions come up most often in interviews for a role that touches BMCs. Each answer is short enough to say out loud, and each one points back to a section above where the reasoning is written out in full. If you can explain the why behind the answer, the short version comes easily.

- "Basic or session?" Choose a session. The password is sent once, tokens can be ended, and Basic can be switched off or needs MFA exceptions.
- "How do you give monitoring access to BMCs?" Create a `ReadOnly` account for each purpose, and reach the BMC over HTTPS with a trusted certificate.
- "What happens if a script logs in thousands of times without logging out?" It can exhaust the BMC's session limit. Always send a `DELETE` for the session.
- "How would you roll out password changes to a fleet?" Use the BMC manager, such as BCM's `bmcsettings`, or a Redfish `PATCH` or `ChangePassword`. Then check that every machine has the same credential fingerprint afterward.
- "Why does the login error for a locked account look like a wrong password?" So that attackers cannot learn which users exist or which accounts are locked.

## Checkpoint questions (20)

<details>
<summary>1. What minimum TLS version and cipher suite category does the Redfish Specification require (DSP0266 §13.1)?</summary>

Redfish services **shall** support **TLS 1.2 or later**. The spec follows the RFC 7525 advice, and TLS 1.1 is deprecated. Services shall only offer cipher suites marked **"Recommended"** in the IANA TLS Cipher Suites registry, such as `AES-GCM` suites.
</details>

<details>
<summary>2. Why is using `curl -k` (or `verify=False` in Python) unsafe in production, and what X.509 standard must BMC certificates follow?</summary>

`curl -k` turns off server certificate checking. An attacker on the network path can then run a man-in-the-middle (MitM) attack. That lets them read BMC credentials or inject power and firmware commands. Under DSP0266 §13.1.3, BMC certificates **shall** follow X.509 v3 (RFC 5280), and services must support replacing the default self-signed certificate.
</details>

<details>
<summary>3. What are the two standard actions on `CertificateService` for replacing a BMC certificate without exposing the private key on the network?</summary>

`CertificateService.GenerateCSR` has the BMC create its keypair internally, so the private key never leaves the BMC. It returns a Certificate Signing Request (CSR) for your CA to sign. `CertificateService.ReplaceCertificate` then swaps the existing certificate at `CertificateUri` for your CA-signed PEM `CertificateString`, with `CertificateType: "PEM"`.
</details>

<details>
<summary>4. Compare HTTP Basic authentication and Redfish session authentication across headers, password exposure, and MFA compatibility.</summary>

Basic sends the base64-encoded `username:password` with every request, and only over HTTPS. You can disable it with `AccountService.HTTPBasicAuth`. The BMC **shall** reject Basic when MFA is required for the account (DSP0266 §13.3.3). A session sends `UserName` and `Password` once, to `POST /redfish/v1/SessionService/Sessions`. The BMC answers with a random `X-Auth-Token` for later requests. Sessions support MFA through the `Token` property, and you can end one with `DELETE`.
</details>

<details>
<summary>5. Why is Base64 encoding in an HTTP Basic header not a form of encryption, and in what order must a BMC process authentication headers relative to ETag headers (DSP0266 §13.3.2.2)?</summary>

Base64 is a reversible text encoding. Anyone can decode it at once, without a key, which is why Basic is forbidden over plain HTTP. Under DSP0266 §13.3.2.2, services **shall** process authentication headers before any other header that changes the response, such as `If-Match` or `If-None-Match`. They **shall not** use HTTP cookies for authentication.
</details>

<details>
<summary>6. What three items must a BMC return when `POST /redfish/v1/SessionService/Sessions` succeeds (`201 Created`)?</summary>

The BMC returns three things. First, the `X-Auth-Token` response header, which holds the secret token. Second, the `Location` header, which holds the URI of the new Session, such as `/redfish/v1/SessionService/Sessions/1`. Third, a JSON body with the full Session resource, where `"Password": null`.
</details>

<details>
<summary>7. What is the difference between the Session ID (`Id` in the `Location` URI) and the Session Authentication Token (`X-Auth-Token`)?</summary>

The Session ID, the `"1"` in the example, is the public identifier. Users and administrators use it to inspect or end (`DELETE`) the session at `/redfish/v1/SessionService/Sessions/<id>`. The `X-Auth-Token` is the cryptographic bearer secret. It comes back only once, in the login response, and only the client that created the session knows it.
</details>

<details>
<summary>8. Do Redfish sessions expire at a fixed wall-clock timestamp or via an idle timeout (DSP0266 §13.3.4.3)?</summary>

Redfish sessions use a sliding idle timeout, set by `SessionTimeout` in `SessionService`. Each authenticated request that arrives inside the timeout restarts the timer, so the token stays valid. The BMC can also enforce an optional `AbsoluteSessionTimeout`.
</details>

<details>
<summary>9. How do you log out of a Redfish session, and what happens to open Server-Sent Event (SSE) streams or firmware transfers started by that session (DSP0266 §13.3.4.4)?</summary>

Send an HTTP `DELETE` to the session's `Location` URI, `/redfish/v1/SessionService/Sessions/<id>`. The reply is `204 No Content`. Per DSP0266 §13.3.4.4, ending a session **shall not** abort connections that the session opened on its own. Those include active SSE streams and ongoing `UpdateService` image transfers.
</details>

<details>
<summary>10. Why must automation scripts always close their Redfish sessions in a `finally` block?</summary>

Embedded BMCs have a finite session table. A script that runs every minute and leaks sessions without calling `DELETE` will eventually use every slot. Then the BMC refuses new logins, or answers with `503 Service Unavailable`, until `SessionTimeout` expires.
</details>

<details>
<summary>11. What is the difference between a Privilege and a Role in Redfish, and how many roles can a `ManagerAccount` have?</summary>

A **Privilege** is one atomic permission: `Login`, `ConfigureManager`, `ConfigureUsers`, `ConfigureComponents` or `ConfigureSelf`. A **Role** is a named collection of privileges, held in `AssignedPrivileges` and `OemPrivileges`. Each `ManagerAccount` has **exactly one** role, set by its `RoleId` property (DSP0266 §13.4.2).
</details>

<details>
<summary>12. Name the three required standard roles in Redfish (DSP0266 Table 41) and the exact privileges assigned to each.</summary>

`Administrator` has `Login`, `ConfigureManager`, `ConfigureUsers`, `ConfigureComponents` and `ConfigureSelf`. `Operator` has `Login`, `ConfigureComponents` and `ConfigureSelf`. `ReadOnly` has `Login` and `ConfigureSelf`. These are the three required roles in DSP0266 Table 41.
</details>

<details>
<summary>13. What is the difference between `ConfigureManager`, `ConfigureComponents`, `ConfigureUsers`, and `ConfigureSelf`?</summary>

`ConfigureManager` changes the BMC itself, such as network settings, protocols, certificates and subscriptions. `ConfigureComponents` changes or resets managed computer systems, chassis, BIOS and storage components. `ConfigureUsers` creates, modifies, unlocks or deletes any account in `AccountService`. `ConfigureSelf` lets you read your own account and change your own password.
</details>

<details>
<summary>14. In the Privilege Registry (`DSP0266` §13.4.3.4), what are the three override types and their precedence order, and how do they explain why a user can change their own password or why an Operator can edit a host NIC but not the BMC NIC?</summary>

The precedence order is **`PropertyOverrides` → `ResourceURIOverrides` → `SubordinateOverrides`**. A `PropertyOverride` on `ManagerAccount` lets `ConfigureUsers` or `ConfigureSelf` PATCH the `Password` property. That is how any user can change their own password without holding `ConfigureUsers`. A `SubordinateOverride` on `EthernetInterface` needs `ConfigureManager` when the NIC sits under `Manager`, which is the BMC's OOB port. Under `ComputerSystem`, the same NIC needs `ConfigureComponents`. That is why an Operator can edit a host NIC but not the BMC NIC.
</details>

<details>
<summary>15. How do `AccountLockoutThreshold`, `AccountLockoutDuration`, and early administrator unlock work in `AccountService`?</summary>

After `AccountLockoutThreshold` consecutive failed logins, the BMC sets `Locked: true` on the `ManagerAccount`. It then rejects every login for `AccountLockoutDuration` seconds, even with the correct password. An administrator with `ConfigureUsers` can unlock the account early by sending `PATCH {"Locked": false}` to the account URI.
</details>

<details>
<summary>16. Why must a failed login for a nonexistent user, a wrong password, and a locked account all return the exact same HTTP 401 message (DSP0266 §13.3.2.3)?</summary>

If the BMC returned different messages, an attacker could learn which usernames exist and which accounts are locked. That is username enumeration and lockout-state reconnaissance. So all three cases return the same HTTP 401 message.
</details>

<details>
<summary>17. How does `PasswordChangeRequired: true` behave upon login, and which specific operations are permitted before the password is changed (DSP0266 §13.5.4)?</summary>

Login succeeds with `201 Created`, and `@Message.ExtendedInfo` includes a `PasswordChangeRequired` message. Every other authenticated request returns **`403 Forbidden`** with `PasswordChangeRequired`, except three things. You may `GET` your own `ManagerAccount`. You may change your password, either by `PATCH` on `Password` when `RequireChangePasswordAction` is `false`, or by `POST` to `ManagerAccount.ChangePassword` on your own account, which clears the flag to `false`. You may also `DELETE` your own Session, and `GET` the unauthenticated root resources.
</details>

<details>
<summary>18. What is `RequireChangePasswordAction` in `AccountService` (DSP0266 §13.5.3), and what security attack does `ManagerAccount.ChangePassword` prevent?</summary>

When `RequireChangePasswordAction` is `true`, the BMC rejects `PATCH` requests to `Password`. Callers must invoke the `ManagerAccount.ChangePassword` action instead, which needs both `NewPassword` and **`SessionAccountPassword`**. That is your current password, or the admin's password when resetting someone else's. An attacker who steals an active `X-Auth-Token` still cannot change the victim's password, because they do not know the current one.
</details>

<details>
<summary>19. Why are `Password` properties always `null` in `GET` responses (DSP0266 §13.2), and what happens to a user's open sessions when an administrator resets their password (§13.5.2)?</summary>

DSP0266 §13.2 requires sensitive properties such as `Password` to come back as `null` in responses. That way, no password hash or cleartext secret can be read back. When an account's properties or password change (§13.5.2), the BMC closes that account's open sessions, so old tokens stop working at once.
</details>

<details>
<summary>20. How does Redfish OAuth 2.0 JWT authorization represent roles and privileges in the token's `scope` claim, and which `alg` header value is strictly forbidden (DSP0266 §13.4.4)?</summary>

The JWT `scope` claim is a space-delimited list. Each entry is either `Redfish.Role.<RoleId>`, such as `Redfish.Role.Operator`, or `Redfish.Privilege.<PrivilegeId>`. The JOSE header must never use `alg: "none"`, because services **shall not** accept unsigned tokens (DSP0266 §13.4.4).
</details>

## Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** TLS and certificates (13.1), sensitive data (13.2), authentication: Basic, sessions, lifetime, logout, client certificates (13.3), authorization: privilege model, standard roles, restricted roles, operation-to-privilege map, OAuth 2.0 (13.4), and account service: password management, atomic change, forced change, TOTP (13.5). I read all of 13.1 to 13.5. I did not use OAuth 2.0 or TOTP details beyond mentioning that they exist.
- **Redfish Resource and Schema Guide DSP2046 (2024.4):** `AccountService` settings (lockout, `HTTPBasicAuth`, `MinPasswordLength`, `RequireChangePasswordAction`), `ManagerAccount` (`PasswordChangeRequired`, `Locked`, `ChangePassword`), `SessionService`, `CertificateService` (`ReplaceCertificate`, `GenerateCSR`).
- **Supercomputers for Linux SysAdmins**, chapter 10: advice to keep passwords off the command line and to separate the management network.
- **BCM 11 Administrator Manual**, section 3.7: central BMC credentials and `credentialsoverview`.
- **NVIDIA-DevOps notes (volume 10 chapter 1):** the `prom_scraper` read-only account idea and the certificate and protocol hardening commands. See the correction in section 1. The protocol-disabling commands are covered in chapter 7.15.
- **Run here:** `auth_lab.py` (44 checks). The mock simulates time, so no real timeout was waited on.
- **Not verified:** any real BMC's behaviour for lockout, session limits, password rules or certificate replacement. DGX-specific account handling is covered in chapter 7.13 and is also unverified.
