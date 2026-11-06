# QIDI Plus 4 — Fluidd Box & Filament Panel Fix

A patch for the Fluidd web interface bundled with the **QIDI Plus 4**
(firmware 2.1.1), so the Control Box panel shows and edits what the
printer screen shows — and stops silently overwriting it.

> **Status — beta, bench-tested only.** Tested on a simulated bench reproducing the firmware 2.1.1 data contracts (upstream Klipper/Moonraker, simulated Box objects, emulated touchscreen client), including two-way Fluidd↔touchscreen synchronization tests. Not yet smoke-tested on a real Plus 4 — beta.
> Current build: 1.0.0.

## ⚠️ READ FIRST — Where the files go

**This fix replaces exactly TWO files. Everything else on the
printer stays exactly as it is.** Most failed installs of patches
like this one are a file copied to the wrong place — read this
before copying anything.

- ✅ **The bundle goes here, and only here:**
  `/home/mks/fluidd/assets/index-BHXUyR-O.js`
  This is the root Fluidd tree — the one its `index.html` and its
  service worker actually serve. Verify the file already there by
  SHA-256 **before** replacing it (it must be the stock hash in
  *Compatibility* below), and verify again **after** (it must be
  the patched hash).
- 🚫 **Do NOT touch `/home/mks/fluidd/Fluidd/`** (note the extra
  `Fluidd/` folder inside `fluidd/`). It holds an **old build that
  is not served**. Do not copy anything into it, do not modify
  anything in it, do not delete it — leave it exactly as it is.
  Copying the patched bundle there changes nothing at all, and the
  panel keeps behaving exactly like stock.
- 🚫 **Do not touch any other `index-*.js`.** Several older bundles
  can accumulate in `/home/mks/fluidd/assets/`. Exactly one file
  matters: the one named precisely **`index-BHXUyR-O.js`**. Leave
  every other file in that folder alone.
- ✅ **The filament table goes here, and only here:**
  `~/printer_data/config/officiall_filas_list.cfg`
  (on the printer this is
  `/home/mks/printer_data/config/officiall_filas_list.cfg`).

Two files, two exact locations, exact names. If a step below seems
to say otherwise, this box wins.

## The problem

On the Plus 4 the printer screen and Fluidd live in two different
identity worlds. The screen resolves each slot from a rich filament
catalogue (56 filaments, 6 vendors, QIDI filament IDs), and the
firmware publishes that resolved identity per slot in
`multi_color_controller`. The bundled Fluidd never reads it — it
resolves slots from a legacy numeric encoding in `save_variables`
against the printer's small stock table (50 entries, Generic +
QIDI only). Verified consequences:

- **Fluidd can display the wrong filament.** Whenever the two
  worlds disagree — typically a third-party filament set on the
  printer screen — the panel shows what the stale numeric values
  decode to, not the filament that is actually assigned.
- **Editing a slot in Fluidd can silently destroy the screen's
  assignment.** Edits write the numeric encoding back. A filament
  with no numeric representation (any third-party vendor on a stock
  machine) is silently replaced by whatever the numeric write
  resolves to — an unrelated edit, even just a color change,
  overwrites what was set on the screen.
- **The material list ignores the vendor.** The dropdown always
  lists every filament in the table, and switching a slot's vendor
  writes only the vendor: the filament stays the previous vendor's,
  so the list never follows the vendor you picked.

What is **not** broken on the Plus 4: the print-start dialog. Its
checks read sensor fields the Plus 4 firmware still publishes, so
the gate works as designed — this patch deliberately does not
touch it (nor the box commands, which are the firmware's own).

This patch repairs the bundled Fluidd in place — no replacement
UI, nothing to run on your PC.

## Compatibility

- **Printer:** QIDI Plus 4 with a QIDI Box.
- **Firmware:** 2.1.1 (the current online-update line).
- **Fluidd:** v1.30.4, bundle `assets/index-BHXUyR-O.js`.
- **The real compatibility check is the bundle itself.** Reference
  stock bundle SHA-256:
  `4770bade9c2154fc1f44b3650746bc855eb008e6376f1d24820db59eb541ed59`.
  The patcher script verifies this before touching anything, and
  path A below starts with the same check.
- Not for the X-Max 4 or for older Plus 4 firmware builds (the
  1.7.x line ships a different bundle) — do not cross-apply.

## What you need

Two files, **both are required**, whichever install path you
choose:

| File | Goes to (exact path) | Role |
| --- | --- | --- |
| `index-BHXUyR-O.js` (patched bundle) | `/home/mks/fluidd/assets/index-BHXUyR-O.js` | the repaired interface |
| `officiall_filas_list.cfg` | `~/printer_data/config/officiall_filas_list.cfg` | filament table built for the Plus 4's numbering: the 50 stock entries unchanged, plus vendor / filament-ID data and the remaining screen-catalogue filaments (82 entries, 6 vendors: Generic, QIDI, HATCHBOX, Polymaker, Bambu Lab, Overture) |

No experience with any of this is assumed. The next section
walks through connecting to the printer and moving files, click
by click; both install paths refer back to it.

## Connecting to the printer

You will connect to the printer from your computer with a
file-transfer program and copy two files onto it. Nothing here
can damage the printer: until the install paths tell you to
upload, you are only looking.

**Before you start**

- A computer on the **same network** as the printer — the same
  home Wi-Fi, or plugged into the same router.
- The printer **switched on and idle**: no print running, no
  filament load/unload in progress.
- About 15–20 minutes.
- The two files from this repo's `drop-in/` folder, saved
  somewhere you can find them again (for example your Downloads
  folder). If you downloaded this repo as a ZIP, unzip it first.

**Step 1 — Find the printer's IP address**

On the printer's touchscreen, open the settings page that shows
the network / Wi-Fi status: the printer's IP address is displayed
there. Write it down. It looks like four numbers separated by
dots — typically `192.168.1.` followed by one more number.

Alternative: log in to your router's administration page and look
at its list of connected devices; the printer appears there with
its address.

**Step 2 — Install a file-transfer program**

The printer accepts file transfers over **SFTP** — copying files
through SSH, on port 22. A free program handles it:

- **Windows:** WinSCP, from
  [winscp.net](https://winscp.net). Download it and install it
  with the default options. The steps below are written for
  WinSCP.
- **Mac:** Cyberduck, from [cyberduck.io](https://cyberduck.io).
  The fields to fill in are the same as in step 3; only the
  window layout differs.
- FileZilla ([filezilla-project.org](https://filezilla-project.org))
  also works, on both.

Such a program shows two panels side by side: your computer's
files on the left, the printer's files on the right. You copy a
file by dragging it from one side to the other.

**Step 3 — Log in to the printer**

Open WinSCP. A **Login** window appears, with a session form.
Fill it in:

| Field | Value |
| --- | --- |
| File protocol | `SFTP` |
| Host name | the printer's IP address (step 1) |
| Port number | `22` |
| User name | `mks` |
| Password | `makerbase` |

Click **Login**.

The first time, a warning appears saying the server's host key
is unknown (wording like *"The server's host key was not found
in the cache"* or *"Potential security breach"*). This is
**normal on a first connection**: your computer has simply never
met this printer before. Check that the address in the warning
is the IP address from step 1, then click **Yes** to accept the
key and continue.

> **About the login.** `mks` / `makerbase` are the Plus 4's
> factory-default SSH credentials — public and documented, the
> same on every Plus 4. If you have changed the password on your
> printer, use yours instead. These credentials give full access
> to the printer's files, so keep your printer on your own
> network.

You are in when the two panels appear: left = your computer,
right = the printer, starting in the `mks` home folder
(`/home/mks`).

(In Cyberduck: click **Open Connection**, choose **SFTP (SSH
File Transfer Protocol)** as the protocol, then the same server
= IP, port 22, username and password. An "unknown fingerprint"
prompt on first connection is the same host-key warning —
verify the IP and click **Allow** / **Continue**.)

**Step 4 — Go to the two folders (and only these two)**

Each panel has a path field above it showing the folder it is
currently displaying. On the **right** (printer) panel, click in
that path field, type the exact path, and press Enter.

You will only ever need these two folders on the printer:

- `/home/mks/fluidd/assets` — holds the bundle file;
- `/home/mks/printer_data/config` — holds the filament table.

That is the whole geography of this fix — the same two locations
as in the ⚠️ box at the top. Do not wander elsewhere on the
printer's disk; nothing else needs you.

**Step 5 — Back up a file (do this before every replacement)**

Never replace a file on the printer without keeping the original
under a backup name **in the same folder**. Two ways — pick one,
and use it for **both** files before uploading anything:

*Graphical (WinSCP):*

1. In the right panel, go to the file's folder (step 4).
2. Right-click the file → **Duplicate…**
3. In the dialog, the target is the same folder. Edit the file
   name at the end of the target path by **adding
   `.stock-backup`** — for example
   `index-BHXUyR-O.js` becomes
   `index-BHXUyR-O.js.stock-backup`.
4. Click **OK**. The backup now sits next to the original.

(In Cyberduck: right-click the file → **Duplicate File**, then
rename the copy the same way.)

*Terminal (still inside WinSCP):*

1. Menu **Commands → Open Terminal** (a black console window
   opens, connected to the printer).
2. Type each line below and press Enter after each. No message
   back means success.

```sh
cp /home/mks/fluidd/assets/index-BHXUyR-O.js /home/mks/fluidd/assets/index-BHXUyR-O.js.stock-backup
cp /home/mks/printer_data/config/officiall_filas_list.cfg /home/mks/printer_data/config/officiall_filas_list.cfg.stock-backup
```

3. Close the terminal window when done.

**Step 6 — Upload a file (the procedure the install paths use)**

1. In the **left** panel, go to the folder on your computer
   where the new file is (path field above the left panel, same
   as step 4).
2. **Check the file's name character by character.** Web
   browsers sometimes rename a downloaded file by adding a
   suffix like ` (1)`. If the name is not *exactly* the required
   one, right-click it → **Rename** and fix it **before**
   uploading. A file with the wrong name is simply ignored by
   the printer.
3. Drag the file from the left panel onto the right panel. A
   copy dialog appears — confirm it (**OK** / **Upload**).
4. Because a file with that name already exists on the printer,
   an overwrite confirmation appears — click **Yes**.
5. Wait until the transfer finishes (progress bar completes, no
   error message). The file on the right panel now shows today's
   date and the new size.

### Command-line alternative (ssh / scp)

If you are comfortable in a terminal, the same work without the
graphical program (first connection asks you to confirm the
printer's fingerprint — type `yes`; the password asked for is
`makerbase`):

```sh
IP=192.168.1.XXX   # the printer's IP address (step 1)

# 1. Back up both files on the printer
ssh mks@$IP 'cp /home/mks/fluidd/assets/index-BHXUyR-O.js /home/mks/fluidd/assets/index-BHXUyR-O.js.stock-backup'
ssh mks@$IP 'cp /home/mks/printer_data/config/officiall_filas_list.cfg /home/mks/printer_data/config/officiall_filas_list.cfg.stock-backup'

# 2. Upload the two files, exact names, exact places
scp drop-in/index-BHXUyR-O.js        mks@$IP:/home/mks/fluidd/assets/index-BHXUyR-O.js
scp drop-in/officiall_filas_list.cfg mks@$IP:/home/mks/printer_data/config/officiall_filas_list.cfg

# 3. Check what is actually on the printer now
ssh mks@$IP 'sha256sum /home/mks/fluidd/assets/index-BHXUyR-O.js'
```

## Install — path A: drop-in files (simplest)

1. **Connect to the printer** — follow *Connecting to the
   printer* above, steps 1–4. You should end up logged in, with
   the printer's folders on the right panel.
2. **Check your stock bundle first.** In the right panel, open
   `/home/mks/fluidd/assets/` (the root tree — see the ⚠️ box
   above; not the `Fluidd/` subfolder) and download
   `index-BHXUyR-O.js` to your computer: drag it from the right
   panel to the left one. Then verify its SHA-256 is
   `4770bade9c2154fc1f44b3650746bc855eb008e6376f1d24820db59eb541ed59`.
   (To get a file's SHA-256: on Windows, run
   `certutil -hashfile index-BHXUyR-O.js SHA256` in a terminal;
   on Mac, `shasum -a 256 index-BHXUyR-O.js`.) If it does not
   match, **stop** — your Fluidd build differs; use path B so
   the check can verify your build, or don't apply the fix.
3. **Back up both files** — follow step 5 of *Connecting to the
   printer*, for **each** of the two files, so that the printer
   holds `index-BHXUyR-O.js.stock-backup` (in
   `/home/mks/fluidd/assets/`) and
   `officiall_filas_list.cfg.stock-backup` (in
   `/home/mks/printer_data/config/`).
4. **Upload the bundle** — follow step 6 of *Connecting to the
   printer*: from this repo's `drop-in/` folder on your computer,
   upload `index-BHXUyR-O.js` into `/home/mks/fluidd/assets/` on
   the printer, under that exact name, and nowhere else.
5. **Upload the filament table** — same step 6 procedure, second
   file: in the right panel, first open the table's folder,
   `/home/mks/printer_data/config/`; then upload
   `officiall_filas_list.cfg` from `drop-in/` into it, under
   that exact name, overwriting the existing one.
6. **Restart Klipper** (the firmware re-reads the filament
   table): in Fluidd, use the **Restart Klipper** button in the
   status card at the top of the dashboard, and wait until the
   interface reports the printer ready again.
7. **Verify the install** (next section) — do not skip this.

## Install — path B: patcher script (verifiable)

`patcher/qidi_plus4_fluidd_fix.py` applies the same fix as 10
anchored replacements. It first verifies that the input is the
reference stock bundle (SHA-256 above) and that every anchor is
found an exact expected number of times; otherwise it refuses to
modify anything. On the reference stock bundle it produces the
drop-in file **byte for byte** (SHA-256
`223edbccdf2bdc79ec6deefd85f0126ae916bb75819059d0f13f81aa3a03c19b`).

```sh
# on your PC, against a downloaded copy of your bundle:
python3 qidi_plus4_fluidd_fix.py --check    index-BHXUyR-O.js   # verify, change nothing
python3 qidi_plus4_fluidd_fix.py --dry-run  index-BHXUyR-O.js   # simulate
python3 qidi_plus4_fluidd_fix.py            index-BHXUyR-O.js   # apply (writes index-BHXUyR-O.js.orig backup)
python3 qidi_plus4_fluidd_fix.py --restore  index-BHXUyR-O.js   # undo from the backup
```

Then connect to the printer as described in *Connecting to the
printer* (steps 1–4) and follow path A from step 3 onward —
backups of both files (step 5 of the connecting section), then
the uploads (step 6), restart and verification — using your
locally patched bundle instead of the one from `drop-in/`, and
the filament table (`drop-in/officiall_filas_list.cfg`) as
before: the bundle to
`/home/mks/fluidd/assets/index-BHXUyR-O.js` (root tree, exact
name; see the ⚠️ box), the table to
`/home/mks/printer_data/config/`. If your bundle is not the
reference stock build, the script stops and changes nothing.

## Verify the install

1. **Re-download the served file.** Fetch
   `/home/mks/fluidd/assets/index-BHXUyR-O.js` from the printer
   again (drag it back to your computer, as in path A step 2)
   and check its SHA-256 — same `certutil` / `shasum` commands
   as in path A step 2: it must now be
   `223edbccdf2bdc79ec6deefd85f0126ae916bb75819059d0f13f81aa3a03c19b`.
   If you still see the stock hash, the new file did not land in
   the served tree — re-check the ⚠️ box above.
2. **Hard-refresh** Fluidd in your browser (**Ctrl+F5**). Fluidd
   ships a service worker that can keep serving the previous
   bundle from cache; a verified install can look unchanged until
   you do this.
3. **Confirm in the browser console:** `window.__qidiPlus4Fix`
   must return `"1.0.0"`.

## What the fix does

- **Identity read from the firmware's own data.** Slot tiles and
  the edit panel resolve name, vendor and color from
  `multi_color_controller` — the same resolved identity the
  printer screen uses — falling back to the stock numeric
  resolution when the firmware publishes nothing for a slot.
- **Vendor-scoped material list, with refresh.** The material
  dropdown only lists the selected vendor's filaments (the current
  filament is always kept; an empty scope falls back to the full
  list, i.e. stock behavior with the stock table). Switching the
  vendor re-points the filament in the same step — same material
  name under the new vendor if it exists, otherwise that vendor's
  first table entry — so every vendor switch lands on a valid
  material and the list follows.
- **Write-back protection.** If a slot's current identity (set on
  the printer screen) has no valid representation in the filament
  table, the panel displays it but **refuses to edit it**: the
  vendor / filament / color controls are disabled and no write is
  emitted, instead of silently replacing it with a numeric
  fallback. To change such a slot, set a representable filament
  on the printer screen first.
- **Panel state from the structured objects.** The
  operation-in-progress lock and the Load / Unload button logic
  read the busy and loaded states from
  `multi_color_controller.operation` / `multi_color_controller.box`
  first (where the firmware's own components publish them),
  falling back to the legacy mirror. The button formulas and the
  commands themselves (`E_BOX` / `E_LOAD` / `E_UNLOAD`,
  `RFID_READ`) are the stock ones, unchanged.
- **A filament table built for the Plus 4.** The stock 50 entries
  keep their numbering, names and temperatures — existing slot
  assignments keep their meaning — and the rest of the screen
  catalogue is appended (`fila51`–`fila82`) with vendor and
  filament-ID data. (The Plus 5 fix's table enumerates the same
  catalogue differently and must **not** be used on a Plus 4.)

Details, change by change: [docs/changes.md](docs/changes.md).

## Tested / status

Exercised on a simulated bench that reproduces the firmware
2.1.1 data contracts — real upstream Klipper and Moonraker, Box
modules simulated at the object level, and the printer screen
emulated as a second Moonraker client — with the stock, the
existing community patch and this fix served side by side against
the same state:

- two-way synchronization Fluidd ↔ emulated screen (changes made
  on either side are followed live by the other, same resolved
  identity);
- vendor switching exercised from two starting filaments across
  all six vendors — every switch produces a coherent
  vendor + filament pair of writes, no empty/invalid value;
- load/unload cycles driven from the panel's real buttons, with
  the panel locked while the operation runs and consistent
  button/loaded states afterwards;
- print-start gate regression-checked (the gate code is
  byte-identical to stock; 6/6 scenarios pass);
- patcher: refuses a wrong-hash bundle and the already-patched
  bundle; two clean runs reproduce the drop-in file byte for byte.

Method, full results and limitations: [docs/testing.md](docs/testing.md).

**Not** covered: a real Plus 4. The bench reproduces the data
contracts, not the Box mechanics, the real screen application or
the printer's timing. Treat this as **beta** until a smoke test
on an actual machine.

## Differences from ThorSc's patch

An existing patch for the same target —
[ThorSc/qidi-max4-plus4-fluidd-box-patch](https://github.com/ThorSc/qidi-max4-plus4-fluidd-box-patch)
(GPL-3.0) — also repairs the panel display by reading
`multi_color_controller`, and it works when installed in the
served tree. This fix differs on the points his README documents
as his own limits:

- **Vendor filtering + refresh:** his material dropdown remains
  limited to vendor indexes 0/1 (Generic / QIDI); here the list is
  scoped to any selected vendor and a switch re-points the
  filament in the same step.
- **Write-back:** his patch reads the rich identity but still
  writes back in the numeric encoding, so editing a slot whose
  filament has no numeric representation overwrites the screen's
  assignment; here such a slot is displayed but protected from
  edits.
- **Filament table:** this fix ships a table numbered for the
  Plus 4, so all six screen-catalogue vendors are representable.
- **Commands:** his patch renames the box commands to
  `*_CONTROL` forms; this one keeps the firmware's stock `E_*`
  commands, which the 2.1.1 panel and firmware already agree on.

## Known limitations

- **Beta — no real-machine smoke test yet** (see *Tested /
  status* above).
- **Protected slots are read-only in Fluidd by design.** A slot
  whose screen-set filament is outside the shipped table can be
  viewed but not edited from the panel; set it on the printer
  screen.
- **RFID assignment flows:** untouched and untested.
- **Spoolman integration:** untested.
- **Multi-Box** (2+ Boxes): untested.
- **Firmware updates overwrite the bundle.** After any QIDI
  firmware update, reapply the fix (the patcher will refuse if
  the new bundle build is unsupported).

## Uninstall

Restore the two `.stock-backup` copies (or use the patcher's
`--restore` for the bundle) over the installed files, restart
Klipper and hard-refresh (Ctrl+F5). Nothing else on the printer
is modified.

## Related project

By the same author, for the sister printer:
[qidi-plus5-fluidd-box-fix](https://github.com/Jonathall/qidi-plus5-fluidd-box-fix)
— the same approach applied to the QIDI Plus 5, where the
firmware's data migration broke the panel further (including the
print-start gate).

## License

GPL-3.0 — see [LICENSE](LICENSE). Fluidd and QIDI's Klipper /
Moonraker editions are GPL-3.0; this patch is distributed under
the same terms.
