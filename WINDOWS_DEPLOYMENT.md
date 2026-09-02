# Windows deployment

This is the reproducible target procedure for the dedicated Windows 11 ARM VM.
It contains no tunnel token, private hostname receipt, or administrator secret.

## Platform gate

Use a Windows 11 ARM environment with Node 22.22.3 ARM64 and CPython 3.13.2
x86-64. The application itself requires no installed Rhino application or
remote CAD computation service.
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

Read `http://127.0.0.1:8000/api/healthz` locally and complete the artifact
round-trip tests before adding persistence. Configure Task Scheduler to run the
same command as the dedicated non-admin account at startup, with restart on
failure. Keep its working directory fixed to the repository checkout.

After placing the accepted source at `C:\ApartmentIntelligence\app`, run
`deploy\windows\install-apartment-intelligence-task.ps1` once from an elevated
PowerShell prompt. It creates or rotates a random password for the local
`ApartmentIntel` service account, grants read/execute access only to the app and
virtual environment plus modify access to ignored exports, and registers the
limited `Apartment Intelligence` startup task. The password exists only long
enough to register the task and is never printed or written to a repository file.

## Public ingress

Install `cloudflared` from Cloudflare's official signed Windows distribution.
Create a named tunnel whose Cloudflare-managed hostname maps to
`http://127.0.0.1:8000`. Because `senibina.com.sg` uses Vercel DNS, the verified
deployment uses the versioned `deploy/edge-proxy` route to preserve
`apartment.senibina.com.sg` while proxying to that tunnel hostname. Install the
tunnel as a Windows service and store its connector credential only in the
system-protected service configuration. Do not commit, print, or paste it into
repository files.

The app remains bound to loopback. Do not add port forwarding, public RDP,
admin endpoints, shared host disks, clipboard integration, or filesystem
browsing. Read back HTTPS, origin rejection, cookie flags, WebMCP discovery,
full export, and restart recovery from a clean browser profile before release.

## Uptime boundary

Disable Windows sleep, configure the VM to start automatically, and keep the
Mac powered. For unattended review, use an Amphetamine session covering the
review period with **Allow Display Sleep unchecked**. This permits the display
to sleep while preventing system sleep; it does not weaken password security.
