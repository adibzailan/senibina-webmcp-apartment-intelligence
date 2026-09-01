# Windows deployment

This is the reproducible target procedure for the dedicated Windows 11 ARM VM.
It contains no tunnel token, private hostname receipt, or administrator secret.

## Platform gate

Use the fresh VM `SNBA - WebMCP - Apartment Intelligence` with 4 vCPU, 8 GB RAM,
and a 128 GB expanding disk. Install Node 22.22.3 and CPython 3.13.2 x86-64.
Before deploying the app, install the hash-pinned Python environment and prove
that Ladybug imports and rhino3dm 8.32.1 writes and reads a metre-unit file with
the five required layers. Stop for founder review if emulation, a wheel, or the
round trip fails.

## Build and run

From an unprivileged application account in a fresh checkout:

```powershell
py -3.13-64 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r server\requirements.txt
npm --prefix web ci --ignore-scripts
npm --prefix web run build
$env:PYTHONPATH = "server"
$env:EXPECTED_ORIGIN = "https://apartment.senibina.com.sg"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Read `http://127.0.0.1:8000/api/health` locally and complete the artifact
round-trip tests before adding persistence. Configure Task Scheduler to run the
same command as the dedicated non-admin account at startup, with restart on
failure. Keep its working directory fixed to the repository checkout.

## Public ingress

Install `cloudflared` from Cloudflare's official signed Windows distribution.
Create a remotely managed named tunnel whose only public route maps
`apartment.senibina.com.sg` to `http://127.0.0.1:8000`. Install the tunnel as the
official Windows service and store its token only in that service's protected
configuration. Do not commit, print, or paste the token into repository files.

The app remains bound to loopback. Do not add port forwarding, public RDP,
admin endpoints, shared host disks, clipboard integration, or filesystem
browsing. Read back HTTPS, origin rejection, cookie flags, WebMCP discovery,
full export, and restart recovery from a clean browser profile before release.

## Uptime boundary

Disable Windows sleep, configure the VM to start automatically, and keep the
Mac powered. For unattended review, use an Amphetamine session covering the
review period with **Allow Display Sleep unchecked**. This permits the display
to sleep while preventing system sleep; it does not weaken password security.
