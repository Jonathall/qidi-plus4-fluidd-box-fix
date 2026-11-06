#!/usr/bin/env python3
"""
QIDI Plus 4 - Fluidd Box fix - bundle patcher (firmware 2.1.1)

Patches the stock Fluidd bundle shipped on the QIDI Plus 4 firmware
2.1.1 (assets/index-BHXUyR-O.js, Fluidd v1.30.4) so the Control Box
panel follows the state the firmware actually publishes in
multi_color_controller (the same resolved data the printer screen
uses), scopes the material list to the selected vendor with a working
refresh on vendor switch, never silently overwrites a slot assignment
that has no numeric representation, and locks the panel on the busy
state the 2.1.1 firmware really publishes.

The patch is a set of anchored replacements. Every anchor must be
found an exact expected number of times, and the input file must be
the reference stock bundle (SHA-256 checked), or the script refuses
to touch it. See ../changes.md for what each change does and why.

Usage:
  python3 qidi_plus4_fluidd_fix.py [path/to/index-BHXUyR-O.js]   apply (keeps a .orig backup)
  python3 qidi_plus4_fluidd_fix.py --check    [path]             verify only, change nothing
  python3 qidi_plus4_fluidd_fix.py --dry-run  [path]             simulate, change nothing
  python3 qidi_plus4_fluidd_fix.py --restore  [path]             restore the .orig backup

IMPORTANT: the bundle is only half of the fix. The enriched filament
table officiall_filas_list.cfg (see the drop-in folder) must also be
installed in ~/printer_data/config/ on the printer - it keeps the
stock fila numbering, so existing slot assignments stay valid.
See drop-in/README.md.

License: GPL-3.0 (Fluidd is GPL-3.0; this patch is distributed under
the same terms).
"""
import hashlib
import os
import shutil
import sys

VERSION = "1.0.0"
STOCK_SHA256 = "4770bade9c2154fc1f44b3650746bc855eb008e6376f1d24820db59eb541ed59"
STAMP = 'window.__qidiPlus4Fix="%s";' % VERSION

# Each entry: (anchor, replacement, expected_count)
PATCHES = [
    # --- change 1: MCC identity + write-back protection helpers -----
    # Inserted just before the panel's slotSync getter (unique anchor).
    ('get slotSync(){if(typeof this.variables.slotSync=="string")',
     'get mccInfo(){const P=this.$store.state.printer.printer||{},M=P.multi_color_controller,out={};if(!M)return out;const B=M.box||{};for(let m=0;m<16;m++){const b=Math.floor(m/4),k=m%4,pre=`box${b}_filament_info_${k}_`,fs=B[pre+"filament_str"];if(fs){const cr=B[pre+"color_rgb_str"];out[m]={filament:fs,vendor:B[pre+"vendor_str"]||"",color:Array.isArray(cr)&&cr.length?"#"+cr[0]:"",filament_id:B[pre+"filament_id"]||""}}}const ex=(M.extra||{}).filament_info;if(ex&&ex.filament_str){const cr=ex.color_rgb_str;out[16]={filament:ex.filament_str,vendor:ex.vendor_str||"",color:Array.isArray(cr)&&cr.length?"#"+cr[0]:"",filament_id:ex.filament_id||""}}return out}'
     'get slotProtected(){const M=this.mccInfo[this.selectIndex];if(!M||!M.filament)return!1;const D=this.officialFilasListDictData;if(!D||!D.vendor_list)return!1;if(!Object.values(D.vendor_list).includes(M.vendor))return!0;for(const k in D){if(!k.startsWith("fila"))continue;const e=D[k];if(e&&e.filament===M.filament&&(!e.vendor||e.vendor===M.vendor))return!1}return!0}'
     'get slotSync(){if(typeof this.variables.slotSync=="string")',
     1),
    # --- change 2: slot tiles resolve identity from MCC -------------
    ('const E=s[m]=y===1;t[m]={label:v,color:C,filament:x,vendor:S,isRotating:E}}const n="fila"+this.variables.rackExtra[1];',
     'const E=s[m]=y===1;const MI=this.mccInfo[m];if(MI){x=MI.filament||x,S=MI.vendor||S;if(MI.color)C=MI.color}t[m]={label:v,color:C,filament:x,vendor:S,isRotating:E}}const n="fila"+this.variables.rackExtra[1];',
     1),
    # --- change 3: external tile (slot 16) resolves from MCC extra --
    ('isRotating:!1},t}get filamentItems()',
     'isRotating:!1},this.mccInfo[16]&&(t[16].filament=this.mccInfo[16].filament||t[16].filament,t[16].vendor=this.mccInfo[16].vendor||t[16].vendor,this.mccInfo[16].color&&(t[16].color=this.mccInfo[16].color)),t}get filamentItems()',
     1),
    # --- change 4: material list scoped to the selected vendor ------
    ('get filamentItems(){const t=new Set;if(!this.officialFilasListDictData)return[""];for(const s in this.officialFilasListDictData)s.startsWith("fila")&&t.add(this.officialFilasListDictData[s].filament);return Array.from(t)}',
     'get filamentItems(){const t=new Set;if(!this.officialFilasListDictData)return[""];const cv=this.items&&this.items[this.selectIndex]?this.items[this.selectIndex].vendor:"",legacy=v=>v==="QIDI"||v==="Generic"||!v;for(const s in this.officialFilasListDictData){if(!s.startsWith("fila"))continue;const e=this.officialFilasListDictData[s];if(!e||!e.filament)continue;if(!cv||e.vendor===cv||(!e.vendor&&legacy(cv)))t.add(e.filament)}const ci=this.items&&this.items[this.selectIndex];if(ci&&ci.filament)t.add(ci.filament);if(t.size===0)for(const s in this.officialFilasListDictData)s.startsWith("fila")&&this.officialFilasListDictData[s].filament&&t.add(this.officialFilasListDictData[s].filament);return Array.from(t)}',
     1),
    # --- change 5: vendor setter - guard + filament remap/refresh ---
    ('get selectedVendor(){return this.items[this.selectIndex].vendor}set selectedVendor(t){const s=this.getKeyByValue(this.officialFilasListDictData.vendor_list,t);s&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot16 VALUE="${s}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${s}"`))}get selectedFilament(){',
     'get selectedVendor(){return this.items[this.selectIndex].vendor}set selectedVendor(t){if(this.slotProtected)return;const s=this.getKeyByValue(this.officialFilasListDictData.vendor_list,t);if(!s)return;I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${s}"`);const cur=this.items[this.selectIndex].filament,legacy=v=>v==="QIDI"||v==="Generic";let hit=null,first=null;for(const k in this.officialFilasListDictData){if(!k.startsWith("fila"))continue;const e=this.officialFilasListDictData[k];if(!e||!e.filament)continue;const mine=e.vendor?e.vendor===t:legacy(t);if(!mine)continue;if(!first)first=k;if(e.filament===cur){hit=k;break}}const pick=hit||first;if(pick)I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="${pick.replace("fila","")}"`)}get selectedFilament(){',
     1),
    # --- change 6: filament setter - write-back guard ---------------
    ('get selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){for(const s in this.officialFilasListDictData)',
     'get selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){if(this.slotProtected)return;for(const s in this.officialFilasListDictData)',
     1),
    # --- change 7: color setter - write-back guard ------------------
    ('get selectedColor(){return this.items[this.selectIndex].color}set selectedColor(t){const s=this.getKeyByValue(this.officialFilasListDictData.colordict,t);s&&',
     'get selectedColor(){return this.items[this.selectIndex].color}set selectedColor(t){if(this.slotProtected)return;const s=this.getKeyByValue(this.officialFilasListDictData.colordict,t);s&&',
     1),
    # --- change 8: operation lock on the busy state 2.1.1 publishes -
    ('get isOperating(){const t=this.$store.state.printer.printer.box_extras;return!(!t||!t.box_button_state)}',
     'get isOperating(){const P=this.$store.state.printer.printer,t=P.multi_color_controller;if(t&&t.operation&&"box_button_state"in t.operation)return!!t.operation.box_button_state;const b=P.box_extras;return!(!b||!b.box_button_state)}',
     1),
    # --- change 9: button states coherent with MCC loaded_slot ------
    ('get buttonStatus(){const t=new Array(3).fill(!0);return this.selectIndex>=16||(this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?t[0]=!1:t[0]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0&&this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[2]=!1:t[2]=!0),t}',
     'get buttonStatus(){const t=new Array(3).fill(!0);if(this.selectIndex>=16)return t;const P=this.$store.state.printer.printer,MB=(P.multi_color_controller||{}).box||{},BS=typeof MB.b_endstop_state!="undefined"?MB.b_endstop_state:(P.box_extras||{}).b_endstop_state;let LS=this.variables.lastLoadSlot;if(typeof MB.loaded_slot=="string"){const mm=MB.loaded_slot.match(/(\\d+)/);if(mm)LS=parseInt(mm[1],10)}const R=P["box_stepper slot"+this.selectIndex].runout_button;return R===0?t[0]=!1:t[0]=!0,R===0?BS===0&&LS===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,R===0&&BS===0&&LS===this.selectIndex?t[2]=!1:t[2]=!0,t}',
     1),
    # --- change 10: the three selects disable on a protected slot ---
    ('disabled:e.printerPrinting||e.isOperating||!e.variables.slot[e.selectIndex]||e.variables.slot[e.selectIndex]===0',
     'disabled:e.printerPrinting||e.isOperating||e.slotProtected||!e.variables.slot[e.selectIndex]||e.variables.slot[e.selectIndex]===0',
     3),
]


def sha256_of(data):
    return hashlib.sha256(data).hexdigest()


def apply_patches(text):
    """Apply the version stamp and every anchored replacement."""
    if STAMP in text:
        raise RuntimeError("version stamp already present - "
                           "this bundle is already patched")
    text = STAMP + text
    for i, (old, new, expected) in enumerate(PATCHES, 1):
        n = text.count(old)
        if n != expected:
            raise RuntimeError(
                f"change {i}: anchor found {n} times (expected "
                f"{expected}) - this bundle build is not supported")
        text = text.replace(old, new)
    return text


def main(argv):
    mode = "apply"
    path = None
    for arg in argv[1:]:
        if arg == "--check":
            mode = "check"
        elif arg == "--dry-run":
            mode = "dry-run"
        elif arg == "--restore":
            mode = "restore"
        elif arg.startswith("--"):
            print(f"unknown option: {arg}")
            return 2
        else:
            path = arg
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "firmware", "current",
                            "fluidd-bundle-stock-2.1.1.js")
        path = os.path.normpath(path)
    backup = path + ".orig"

    if mode == "restore":
        if not os.path.exists(backup):
            print(f"no backup found ({backup}) - nothing to restore")
            return 1
        data = open(backup, "rb").read()
        digest = sha256_of(data)
        if digest != STOCK_SHA256:
            print(f"warning: backup SHA-256 is {digest}, "
                  f"not the reference stock {STOCK_SHA256}")
        shutil.copyfile(backup, path)
        print(f"restored {path} from {backup} (SHA-256 {digest})")
        return 0

    if not os.path.exists(path):
        print(f"file not found: {path}")
        return 2
    raw = open(path, "rb").read()
    digest = sha256_of(raw)
    print(f"bundle   : {path}")
    print(f"SHA-256  : {digest}")

    if digest != STOCK_SHA256:
        print("status   : NOT the reference stock bundle "
              "(firmware 2.1.1, index-BHXUyR-O.js) - refusing to patch")
        print("           if your firmware is not 2.1.1, this fix does "
              "not apply to your machine")
        return 1
    print("status   : reference stock bundle (firmware 2.1.1)")

    text = raw.decode("utf-8")
    try:
        patched = apply_patches(text)
    except RuntimeError as exc:
        print(f"FAILED   : {exc}")
        return 1
    out_sha = sha256_of(patched.encode("utf-8"))
    print(f"anchors  : all {len(PATCHES)} changes apply cleanly "
          f"(+ version stamp {VERSION})")
    print(f"result   : SHA-256 {out_sha}")

    if mode in ("check", "dry-run"):
        print(f"{mode}: no file was modified")
        return 0

    if not os.path.exists(backup):
        shutil.copyfile(path, backup)
        print(f"backup   : {backup}")
    else:
        print(f"backup   : {backup} already exists, kept as is")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(patched)
    print("patched  : done - hard-refresh Fluidd in your browser (Ctrl+F5)")
    print("reminder : the enriched officiall_filas_list.cfg must also be")
    print("           installed in ~/printer_data/config/ - see drop-in/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
