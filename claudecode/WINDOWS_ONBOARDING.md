# Windows Node Onboarding — Claude Code
# Written by Claude Code on akiendelllinux, 2026-03-10
# For: Claude Code instance running on a Windows cluster node (elevated shell)

---

## Hey, me — here's your situation

You are Claude Code running on one of Akien's Windows machines. This is the TheIgors
project repo. You were launched in an elevated (admin) shell specifically to sort SSH
access so Igor (the AI agent, running on akiendelllinux at 10.0.0.229) can reach this
machine to swap Ollama models and run cluster tasks.

You do NOT need to run Igor here. No venv, no .env, no DB. This machine is a cluster node.

---

## This Machine's Identity

Check `claudecode/../design_docs/` and `machines.json` (runtime, not in repo) for full
cluster info. The likely candidates for this box:

| Hostname     | IP          | Role       | SSH user        | Notes                          |
|--------------|-------------|------------|-----------------|--------------------------------|
| akiendell    | 10.0.0.99   | background | igor_wild_0001  | Akien's daily driver           |
| akienyoga9i  | 10.0.0.90   | realtime   | igor_wild_0001  | Bedroom/travel PC              |
| akienyogai7  | 10.0.0.71   | batch      | igor_wild_0001  | Living room TV PC              |

Run `hostname` in a shell to confirm which one this is.

---

## SSH Setup Goal

Igor (on akiendelllinux, 10.0.0.229) needs to SSH **into this Windows box** as user
`igor_wild_0001`. You are here to make that work.

The SSH key Igor uses (on the Linux side): `~/.ssh/igor_ed25519`
The public key to install on Windows: see below.

**Known issue**: `machines.json` references `~/.TheIgors/igor_id_rsa` — that path is
WRONG. The real key is `~/.ssh/igor_ed25519`. Keep this in mind if you're debugging.

---

## Igor's Public Key (to install in authorized_keys on Windows)

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGLwfMgY3SZpWzsl3tlUM3xT2lKUUF6b/18JzSw24pVk akien@akiendelllinux
```

---

## Step-by-Step SSH Setup (Windows, elevated shell)

### 1. Verify OpenSSH Server is installed and running

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
# If not installed:
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start and enable the service:
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

### 2. Check the firewall rule exists

```powershell
Get-NetFirewallRule -Name *ssh*
# If missing:
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

### 3. Verify the igor_wild_0001 user account exists

```powershell
Get-LocalUser -Name igor_wild_0001
# If missing, create it (ask Akien for the password or use a strong random one):
# New-LocalUser -Name igor_wild_0001 -Description "Igor SSH user" ...
```

### 4. Install the authorized key

For **admin users** on Windows, the authorized_keys file goes in a special location
(NOT the user's home directory — Windows OpenSSH has a quirk for admin accounts):

```powershell
# Check if igor_wild_0001 is in Administrators group:
Get-LocalGroupMember -Group Administrators

# If igor_wild_0001 IS an admin, the authorized_keys must go here:
$adminKeyPath = "C:\ProgramData\ssh\administrators_authorized_keys"
# If igor_wild_0001 is NOT an admin, use:
$adminKeyPath = "C:\Users\igor_wild_0001\.ssh\authorized_keys"

# Create the directory and file:
New-Item -ItemType Directory -Force -Path (Split-Path $adminKeyPath)
Add-Content $adminKeyPath "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGLwfMgY3SZpWzsl3tlUM3xT2lKUUF6b/18JzSw24pVk akien@akiendelllinux"

# Fix permissions (critical — OpenSSH will reject keys with wrong ACLs):
icacls $adminKeyPath /inheritance:r /grant "SYSTEM:F" /grant "Administrators:F"
# If using the admin path:
# icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "SYSTEM:F" /grant "Administrators:F"
```

### 5. Check sshd_config (important for admin keys)

```powershell
notepad C:\ProgramData\ssh\sshd_config
```

Look for this line — it must be present and NOT commented out for the
`administrators_authorized_keys` file to be used:

```
Match Group administrators
       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
```

If it's commented out, uncomment it, save, then restart sshd:
```powershell
Restart-Service sshd
```

### 6. Test from the Linux side

On akiendelllinux (10.0.0.229), ask Akien or run:
```bash
ssh -i ~/.ssh/igor_ed25519 igor_wild_0001@<this_machine_ip> "echo SSH OK"
```

---

## Also Check: machines.json key path

The runtime `machines.json` at `~/.TheIgors/local/machines.json` on Linux has:
```json
"ssh_key": "~/.TheIgors/igor_id_rsa"
```
That path is **wrong** — the actual key is `~/.ssh/igor_ed25519`. Once SSH is verified
working, flag this to Akien so Igor can correct the machines.json entry.

---

## What NOT to do here

- Don't try to run Igor — no .env, no DB, no venv on this box yet
- Don't commit anything sensitive (no keys, no passwords)
- Don't install the venv unless Akien asks — that's a separate setup task
- Don't edit brainstem/ or memory/models.py without Akien's explicit go-ahead

---

## Key files in this repo (for orientation)

- `CLAUDE.md` — project conventions and inertia levels
- `claudecode/CONTEXT.md` — fuller architecture context
- `design_docs/` — architecture decisions (CSB format)
- `wild_igor/igor/` — Igor's source code
- `machines.json` is runtime data at `~/.TheIgors/local/machines.json` (not in repo)

---

## Linux box context

- akiendelllinux: 10.0.0.229, Igor's main loop machine
- SSH key on Linux: `~/.ssh/igor_ed25519` (ed25519, NOT RSA)
- Igor's runtime: `~/.TheIgors/igor_wild_0001/`
- Repo source: `~/TheIgors/`

---

## If you get stuck

Ask Akien. He's the human. You can also check the GitHub discussions for session notes:
https://github.com/akienm/TheIgors/discussions/62

Good luck, me.
