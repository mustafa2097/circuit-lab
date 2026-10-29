# -*- coding: utf-8 -*-
"""Generate circuit JSON definitions for circuit-lab."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "circuits"
OUT.mkdir(parents=True, exist_ok=True)


def ports_lr(left="L", right="R"):
    return [{"id": left, "side": "left"}, {"id": right, "side": "right"}]


def comp(cid, typ, label, x, y, tx, ty, signal=None, monitors=None, preset=None, ports=None, nc=None):
    d = {
        "id": cid,
        "type": typ,
        "label": label,
        "ports": ports or ports_lr(),
        "trayPosition": {"x": x, "y": y},
        "targetPosition": {"x": tx, "y": ty},
    }
    if signal is not None:
        d["signal"] = signal
    if monitors is not None:
        d["monitors"] = monitors
    if preset is not None:
        d["preset"] = preset
    if nc is not None:
        d["normallyClosed"] = nc
    return d


def wire(wid, frm, to):
    return {"id": wid, "from": frm, "to": to}


def step(sid, title, detail, wire_id=None, frm=None, to=None, place=None):
    d = {"id": sid, "title": title, "detail": detail}
    if wire_id:
        d["wireId"] = wire_id
    if frm:
        d["from"] = frm
    if to:
        d["to"] = to
    if place:
        d["placeComponentId"] = place
    return d


def save(circuit):
    path = OUT / f"{circuit['id']}.json"
    path.write_text(json.dumps(circuit, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path.name)


# ---------- helpers for series ladder on one rung ----------
def series_rung(rail_l, rail_r, parts, y, base_x=80):
    """parts: list of (id, type, label, signal, monitors, preset)
    Returns components + wires for L1 - p1 - p2 - ... - coil - L2
    """
    comps = [
        comp(rail_l, "RAIL_L", "L1", 20, y - 40, 40, y - 40, ports=[{"id": "out", "side": "right"}]),
        comp(rail_r, "RAIL_R", "L2", 20, y + 80, 760, y - 40, ports=[{"id": "in", "side": "left"}]),
    ]
    wires = []
    x = base_x
    prev = f"{rail_l}.out"
    for i, p in enumerate(parts):
        cid, typ, label = p[0], p[1], p[2]
        signal = p[3] if len(p) > 3 else None
        monitors = p[4] if len(p) > 4 else None
        preset = p[5] if len(p) > 5 else None
        comps.append(comp(cid, typ, label, 40 + i * 30, 420 + (i % 5) * 70, x, y, signal=signal, monitors=monitors, preset=preset))
        wires.append(wire(f"w_{cid}_in", prev, f"{cid}.L" if typ not in ("TON", "TOF", "TP") else f"{cid}.IN"))
        if typ in ("TON", "TOF", "TP"):
            prev = f"{cid}.Q"
        else:
            prev = f"{cid}.R"
        x += 130
    wires.append(wire(f"w_to_{rail_r}", prev, f"{rail_r}.in"))
    return comps, wires


# ===================== PILOT 8 =====================

def c_start_stop_latched():
    # L1 -- start NO -- stop NC -- Y1 coil -- L2
    #           |__ Y1 NO __|
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 40, 40, 80, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 720, 80, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "start", 40, 360, 160, 60, signal="start"),
        comp("seal", "CONTACT_NO", "Y1", 40, 440, 160, 150, signal="Y1", monitors="Y1"),
        comp("stop", "PB_NC", "stop", 40, 520, 320, 100, signal="stop"),
        comp("Y1", "COIL", "Y1", 40, 600, 480, 100, signal="Y1"),
    ]
    wires = [
        wire("w1", "L1.out", "start.L"),
        wire("w2", "L1.out", "seal.L"),
        wire("w3", "start.R", "stop.L"),
        wire("w4", "seal.R", "stop.L"),
        wire("w5", "stop.R", "Y1.L"),
        wire("w6", "Y1.R", "L2.in"),
    ]
    steps = [
        step("s1", "ضع عمود L1", "ضع عمود التغذية L1 على يسار اللوحة.", place="L1"),
        step("s2", "ضع عمود L2", "ضع عمود L2 على يمين اللوحة.", place="L2"),
        step("s3", "ضع زر start", "ضع ضغطة start (NO) في المسار العلوي.", place="start"),
        step("s4", "اربط L1 إلى start", "صل مخرج L1 إلى يسار start.", "w1", "L1.out", "start.L"),
        step("s5", "ضع تلامس القفل Y1", "ضع تلامس NO لـ Y1 موازياً لـ start.", place="seal"),
        step("s6", "اربط L1 إلى تلامس Y1", "صل L1 إلى يسار تلامس Y1 (مسار القفل).", "w2", "L1.out", "seal.L"),
        step("s7", "ضع زر stop", "ضع ضغطة stop (NC) بعد التوازي.", place="stop"),
        step("s8", "اربط start إلى stop", "صل يمين start إلى يسار stop.", "w3", "start.R", "stop.L"),
        step("s9", "اربط تلامس Y1 إلى stop", "صل يمين تلامس Y1 إلى يسار stop.", "w4", "seal.R", "stop.L"),
        step("s10", "ضع ملف Y1", "ضع ملف الخرج Y1 في نهاية الرنج.", place="Y1"),
        step("s11", "اربط stop إلى Y1", "صل يمين stop إلى يسار ملف Y1.", "w5", "stop.R", "Y1.L"),
        step("s12", "اربط Y1 إلى L2", "صل يمين ملف Y1 إلى L2.", "w6", "Y1.R", "L2.in"),
    ]
    return {
        "id": "start-stop-latched",
        "title": "Start, Stop & Latched",
        "titleAr": "تشغيل / إيقاف مع قفل (Latch)",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 40",
        "purpose": "تشغيل خرج بزر لحظي والإبقاء عليه شغالاً حتى Stop",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "nc-hold", "default": False},
            ],
            "outputs": [{"id": "Y1", "label": "Y1", "kind": "coil"}],
            "tickMs": 50,
            "description": "اضغط Start فيشتغل Y1 ويُقفل. اضغط Stop فينطفئ.",
        },
    }


def c_latched_sr():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 40, 40, 80, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 720, 80, ports=[{"id": "in", "side": "left"}]),
        comp("set", "PB_NO", "Set", 40, 360, 180, 60, signal="set"),
        comp("rst", "PB_NO", "Reset", 40, 440, 180, 180, signal="reset"),
        comp("Y1", "COIL", "Y1 (S)", 40, 520, 400, 60, signal="Y1"),
        # Reset rung clears via NC path conceptually — model as second coil path using CONTACT
        # For S/R: Set energizes latch memory; Reset clears. We simulate with seal + reset NC on set path
        comp("seal", "CONTACT_NO", "Y1", 40, 600, 180, 120, monitors="Y1"),
        comp("rstnc", "CONTACT_NC", "Reset", 40, 680, 320, 90, monitors="reset"),
    ]
    # Classic: Set OR seal, then NOT reset, to Y1
    wires = [
        wire("w1", "L1.out", "set.L"),
        wire("w2", "L1.out", "seal.L"),
        wire("w3", "set.R", "rstnc.L"),
        wire("w4", "seal.R", "rstnc.L"),
        wire("w5", "rstnc.R", "Y1.L"),
        wire("w6", "Y1.R", "L2.in"),
        # Reset button shown but acts via monitors on rstnc — optional visual wire unused for power
        wire("w7", "L1.out", "rst.L"),
        wire("w8", "rst.R", "L2.in"),
    ]
    steps = [
        step("s1", "ضع الأعمدة", "ضع L1 و L2.", place="L1"),
        step("s2", "مسار Set", "اربط L1 → Set → تلامس Reset NC → Y1 → L2", "w1", "L1.out", "set.L"),
        step("s3", "مسار القفل", "اربط L1 → تلامس Y1 موازي لـ Set", "w2", "L1.out", "seal.L"),
        step("s4", "أكمل إلى الملف", "صل المسارين عبر NC الخاص بـ Reset إلى Y1 ثم L2", "w5", "rstnc.R", "Y1.L"),
        step("s5", "مسار زر Reset", "اربط زر Reset بين L1 و L2 كمدخل", "w7", "L1.out", "rst.L"),
    ]
    return {
        "id": "latched-circuit-using-set-reset",
        "title": "Latched Circuit using Set & Reset",
        "titleAr": "قفل باستخدام Set و Reset",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 41",
        "purpose": "قفل/إلغاء قفل الخرج بتعليماتي Set و Reset",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "set", "label": "Set", "kind": "momentary"},
                {"id": "reset", "label": "Reset", "kind": "momentary"},
            ],
            "outputs": [{"id": "Y1", "label": "Y1", "kind": "coil"}],
            "tickMs": 50,
            "description": "Set يشغّل ويقفل Y1. Reset يفك القفل.",
        },
    }


def c_interlock():
    # Two motors M1/M2 interlocked
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 40, 40, 40, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 220, 780, 40, ports=[{"id": "in", "side": "left"}]),
        comp("s1", "PB_NO", "Start1", 40, 360, 160, 40, signal="start1"),
        comp("stop", "PB_NC", "Stop", 40, 440, 300, 80, signal="stop"),
        comp("m2nc", "CONTACT_NC", "M2", 40, 520, 440, 80, monitors="M2"),
        comp("M1", "COIL", "M1", 40, 600, 580, 80, signal="M1"),
        comp("seal1", "CONTACT_NO", "M1", 160, 360, 160, 140, monitors="M1"),
        comp("s2", "PB_NO", "Start2", 160, 440, 160, 240, signal="start2"),
        comp("stop2", "PB_NC", "Stop", 160, 520, 300, 280, signal="stop"),
        comp("m1nc", "CONTACT_NC", "M1", 160, 600, 440, 280, monitors="M1"),
        comp("M2", "COIL", "M2", 160, 680, 580, 280, signal="M2"),
        comp("seal2", "CONTACT_NO", "M2", 280, 360, 160, 340, monitors="M2"),
    ]
    wires = [
        wire("a1", "L1.out", "s1.L"),
        wire("a2", "L1.out", "seal1.L"),
        wire("a3", "s1.R", "stop.L"),
        wire("a4", "seal1.R", "stop.L"),
        wire("a5", "stop.R", "m2nc.L"),
        wire("a6", "m2nc.R", "M1.L"),
        wire("a7", "M1.R", "L2.in"),
        wire("b1", "L1.out", "s2.L"),
        wire("b2", "L1.out", "seal2.L"),
        wire("b3", "s2.R", "stop2.L"),
        wire("b4", "seal2.R", "stop2.L"),
        wire("b5", "stop2.R", "m1nc.L"),
        wire("b6", "m1nc.R", "M2.L"),
        wire("b7", "M2.R", "L2.in"),
    ]
    steps = [
        step("s1", "رنج M1", "ركّب Start1 موازي تلامس M1 ثم Stop ثم NC لـ M2 ثم ملف M1", "a1", "L1.out", "s1.L"),
        step("s2", "رنج M2", "ركّب Start2 موازي تلامس M2 ثم Stop ثم NC لـ M1 ثم ملف M2", "b1", "L1.out", "s2.L"),
        step("s3", "التعشيق", "تأكد أن NC لـ M2 على رنج M1 و NC لـ M1 على رنج M2 كما بالملزمة.", "a5", "stop.R", "m2nc.L"),
    ]
    return {
        "id": "interlock-control",
        "title": "Interlock Control",
        "titleAr": "تحكم بالتعشيق (Interlock)",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 45",
        "purpose": "منع تشغيل خرجين متعارضين معاً",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "start1", "label": "Start1", "kind": "momentary"},
                {"id": "start2", "label": "Start2", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
            ],
            "outputs": [
                {"id": "M1", "label": "M1", "kind": "coil"},
                {"id": "M2", "label": "M2", "kind": "coil"},
            ],
            "tickMs": 50,
            "description": "لا يعمل M1 و M2 معاً بسبب التعشيق.",
        },
    }


def c_motor_starter_q3():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 40, 40, 40, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 220, 780, 40, ports=[{"id": "in", "side": "left"}]),
        comp("stop", "PB_NC", "stop", 40, 360, 140, 60, signal="stop"),
        comp("start", "PB_NO", "start", 40, 440, 280, 60, signal="start"),
        comp("seal", "CONTACT_NO", "M", 40, 520, 280, 140, monitors="M"),
        comp("OL", "OL", "OL", 40, 600, 420, 100, signal="OL"),
        comp("M", "COIL", "M", 40, 680, 560, 100, signal="M"),
        comp("G", "LAMP", "G", 160, 360, 560, 220, signal="G"),
        comp("McG", "CONTACT_NO", "M", 160, 440, 420, 220, monitors="M"),
        comp("R", "LAMP", "R", 160, 520, 560, 320, signal="R"),
        comp("McR", "CONTACT_NC", "M", 160, 600, 420, 320, monitors="M"),
    ]
    wires = [
        wire("w1", "L1.out", "stop.L"),
        wire("w2", "stop.R", "start.L"),
        wire("w3", "stop.R", "seal.L"),
        wire("w4", "start.R", "OL.L"),
        wire("w5", "seal.R", "OL.L"),
        wire("w6", "OL.R", "M.L"),
        wire("w7", "M.R", "L2.in"),
        wire("w8", "L1.out", "McG.L"),
        wire("w9", "McG.R", "G.L"),
        wire("w10", "G.R", "L2.in"),
        wire("w11", "L1.out", "McR.L"),
        wire("w12", "McR.R", "R.L"),
        wire("w13", "R.R", "L2.in"),
    ]
    # Fix: stop is NC — when stop pressed signal true opens. Default stop false means closed.
    steps = [
        step("s1", "رنج المحرك", "L1 → stop(NC) → (start // M) → OL → M → L2", "w1", "L1.out", "stop.L"),
        step("s2", "لمبة خضراء", "L1 → تلامس M(NO) → G → L2", "w8", "L1.out", "McG.L"),
        step("s3", "لمبة حمراء", "L1 → تلامس M(NC) → R → L2", "w11", "L1.out", "McR.L"),
    ]
    return {
        "id": "simple-motor-starter-with-gr-lamps",
        "title": "Simple Motor Starter with G/R Lamps",
        "titleAr": "بادئ محرك مع لمبات G/R",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 1 / Q3",
        "purpose": "تشغيل محرك مع Holding ومؤشرات تشغيل/إيقاف",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "OL", "label": "Overload", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "M", "label": "Motor M", "kind": "coil"},
                {"id": "G", "label": "Green", "kind": "lamp"},
                {"id": "R", "label": "Red", "kind": "lamp"},
            ],
            "tickMs": 50,
            "description": "Start يشغّل M و G. Stop أو OL يوقف. R تضيء عندما M متوقف.",
        },
    }


def c_fwd_rev_q1():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 820, 30, ports=[{"id": "in", "side": "left"}]),
        comp("stop", "PB_NC", "stop", 40, 320, 120, 50, signal="stop"),
        comp("start", "PB_NO", "start", 40, 400, 250, 50, signal="start"),
        comp("mainSeal", "CONTACT_NO", "Main", 40, 480, 250, 130, monitors="Main"),
        comp("OL", "OL", "OL", 40, 560, 390, 90, signal="OL"),
        comp("Main", "COIL", "Main", 40, 640, 530, 90, signal="Main"),
        comp("FW", "PB_NO", "FW", 180, 320, 120, 220, signal="FW"),
        comp("KrNc", "CONTACT_NC", "Kr", 180, 400, 260, 220, monitors="Kr"),
        comp("MainNo1", "CONTACT_NO", "Main", 180, 480, 400, 220, monitors="Main"),
        comp("Kf", "COIL", "Kf", 180, 560, 540, 220, signal="Kf"),
        comp("KfSeal", "CONTACT_NO", "Kf", 180, 640, 120, 300, monitors="Kf"),
        comp("RV", "PB_NO", "RV", 320, 320, 120, 400, signal="RV"),
        comp("KfNc", "CONTACT_NC", "Kf", 320, 400, 260, 400, monitors="Kf"),
        comp("MainNo2", "CONTACT_NO", "Main", 320, 480, 400, 400, monitors="Main"),
        comp("Kr", "COIL", "Kr", 320, 560, 540, 400, signal="Kr"),
        comp("KrSeal", "CONTACT_NO", "Kr", 320, 640, 120, 480, monitors="Kr"),
        comp("G", "LAMP", "G", 460, 320, 700, 220, signal="G"),
        comp("KfG", "CONTACT_NO", "Kf", 460, 400, 560, 220, monitors="Kf"),
        comp("R", "LAMP", "R", 460, 480, 700, 400, signal="R"),
        comp("KrR", "CONTACT_NO", "Kr", 460, 560, 560, 400, monitors="Kr"),
    ]
    wires = [
        wire("m1", "L1.out", "stop.L"),
        wire("m2", "stop.R", "start.L"),
        wire("m3", "stop.R", "mainSeal.L"),
        wire("m4", "start.R", "OL.L"),
        wire("m5", "mainSeal.R", "OL.L"),
        wire("m6", "OL.R", "Main.L"),
        wire("m7", "Main.R", "L2.in"),
        wire("f1", "L1.out", "FW.L"),
        wire("f2", "L1.out", "KfSeal.L"),
        wire("f3", "FW.R", "KrNc.L"),
        wire("f4", "KfSeal.R", "KrNc.L"),
        wire("f5", "KrNc.R", "MainNo1.L"),
        wire("f6", "MainNo1.R", "Kf.L"),
        wire("f7", "Kf.R", "L2.in"),
        wire("r1", "L1.out", "RV.L"),
        wire("r2", "L1.out", "KrSeal.L"),
        wire("r3", "RV.R", "KfNc.L"),
        wire("r4", "KrSeal.R", "KfNc.L"),
        wire("r5", "KfNc.R", "MainNo2.L"),
        wire("r6", "MainNo2.R", "Kr.L"),
        wire("r7", "Kr.R", "L2.in"),
        wire("g1", "L1.out", "KfG.L"),
        wire("g2", "KfG.R", "G.L"),
        wire("g3", "G.R", "L2.in"),
        wire("rr1", "L1.out", "KrR.L"),
        wire("rr2", "KrR.R", "R.L"),
        wire("rr3", "R.R", "L2.in"),
    ]
    steps = [
        step("s1", "رنج Main", "stop → (start // Main) → OL → Main", "m1", "L1.out", "stop.L"),
        step("s2", "رنج أمامي Kf", "FW // Kf ثم NC لـ Kr ثم Main ثم Kf", "f1", "L1.out", "FW.L"),
        step("s3", "رنج خلفي Kr", "RV // Kr ثم NC لـ Kf ثم Main ثم Kr", "r1", "L1.out", "RV.L"),
        step("s4", "المؤشرات", "G عبر تلامس Kf و R عبر تلامس Kr", "g1", "L1.out", "KfG.L"),
    ]
    return {
        "id": "forwardreverse-motor-control-kfkr-with-main-indicators",
        "title": "Forward/Reverse Motor Control (Kf/Kr)",
        "titleAr": "محرك أمامي/خلفي مع Main ومؤشرات",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 1 / Q1",
        "purpose": "تحكم أمامي/خلفي مع تعشيق ولمبات",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "FW", "label": "FW", "kind": "momentary"},
                {"id": "RV", "label": "RV", "kind": "momentary"},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "Main", "label": "Main", "kind": "coil"},
                {"id": "Kf", "label": "Kf", "kind": "coil"},
                {"id": "Kr", "label": "Kr", "kind": "coil"},
                {"id": "G", "label": "G", "kind": "lamp"},
                {"id": "R", "label": "R", "kind": "lamp"},
            ],
            "tickMs": 50,
            "description": "شغّل Main ثم FW أو RV. التعشيق يمنع Kf و Kr معاً.",
        },
    }


def c_conveyor_siren():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 800, 30, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "Start", 40, 320, 140, 50, signal="start"),
        comp("stop", "PB_NC", "Stop", 40, 400, 280, 90, signal="stop"),
        comp("seal", "CONTACT_NO", "CR1", 40, 480, 140, 140, monitors="CR1"),
        comp("OL", "OL", "OL", 40, 560, 420, 90, signal="OL"),
        comp("CR1", "COIL", "CR1", 40, 640, 560, 90, signal="CR1"),
        comp("cr1a", "CONTACT_NO", "CR1", 180, 320, 140, 230, monitors="CR1"),
        comp("TD1", "TON", "TD1 3s", 180, 400, 300, 230, signal="TD1", preset=3000, ports=ports_lr("IN", "Q")),
        # Siren path: CR1 and NOT M1
        comp("cr1b", "CONTACT_NO", "CR1", 180, 480, 140, 340, monitors="CR1"),
        comp("m1nc", "CONTACT_NC", "M1", 180, 560, 300, 340, monitors="M1"),
        comp("Siren", "LAMP", "Siren", 180, 640, 460, 340, signal="Siren"),
        # Motor: CR1 and TD1
        comp("cr1c", "CONTACT_NO", "CR1", 320, 320, 140, 450, monitors="CR1"),
        comp("td1no", "CONTACT_NO", "TD1", 320, 400, 300, 450, monitors="TD1"),
        comp("M1", "COIL", "M1", 320, 480, 460, 450, signal="M1"),
    ]
    wires = [
        wire("a1", "L1.out", "start.L"),
        wire("a2", "L1.out", "seal.L"),
        wire("a3", "start.R", "stop.L"),
        wire("a4", "seal.R", "stop.L"),
        wire("a5", "stop.R", "OL.L"),
        wire("a6", "OL.R", "CR1.L"),
        wire("a7", "CR1.R", "L2.in"),
        wire("b1", "L1.out", "cr1a.L"),
        wire("b2", "cr1a.R", "TD1.IN"),
        wire("b3", "TD1.Q", "L2.in"),
        wire("c1", "L1.out", "cr1b.L"),
        wire("c2", "cr1b.R", "m1nc.L"),
        wire("c3", "m1nc.R", "Siren.L"),
        wire("c4", "Siren.R", "L2.in"),
        wire("d1", "L1.out", "cr1c.L"),
        wire("d2", "cr1c.R", "td1no.L"),
        wire("d3", "td1no.R", "M1.L"),
        wire("d4", "M1.R", "L2.in"),
    ]
    steps = [
        step("s1", "رنج CR1", "Start // CR1 ثم Stop ثم OL ثم CR1", "a1", "L1.out", "start.L"),
        step("s2", "مؤقت TD1", "CR1 يغذي مؤقت 3 ثوانٍ", "b1", "L1.out", "cr1a.L"),
        step("s3", "الصفارة", "CR1 و NC لـ M1 تشغّل Siren", "c1", "L1.out", "cr1b.L"),
        step("s4", "المحرك", "بعد TD1 يعمل M1 عبر CR1", "d1", "L1.out", "cr1c.L"),
    ]
    return {
        "id": "conveyor-motor-warning-siren-relay-circuit",
        "title": "Conveyor Motor + Warning Siren",
        "titleAr": "ناقل مع صفارة تحذير",
        "sourceFile": "3 - Timers and Counters in PLC Based Control.ppt",
        "page": "شريحة 12",
        "purpose": "صفارة قبل تشغيل محرك الناقل بـ 3 ثوانٍ",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "CR1", "label": "CR1", "kind": "coil"},
                {"id": "TD1", "label": "TD1", "kind": "timer"},
                {"id": "Siren", "label": "Siren", "kind": "lamp"},
                {"id": "M1", "label": "M1", "kind": "coil"},
            ],
            "tickMs": 50,
            "description": "عند Start: صفارة فوراً، وبعد 3 ثوانٍ يشتغل المحرك وتنطفئ الصفارة.",
        },
    }


def c_soft_start():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 780, 30, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "Start", 40, 320, 140, 50, signal="start"),
        comp("stop", "PB_NC", "Stop", 40, 400, 280, 90, signal="stop"),
        comp("seal", "CONTACT_NO", "CR1", 40, 480, 140, 140, monitors="CR1"),
        comp("OL", "OL", "OL", 40, 560, 420, 90, signal="OL"),
        comp("CR1", "COIL", "CR1", 40, 640, 560, 90, signal="CR1"),
        comp("cr1a", "CONTACT_NO", "CR1", 180, 320, 140, 230, monitors="CR1"),
        comp("M2", "COIL", "M2", 180, 400, 300, 230, signal="M2"),
        comp("cr1b", "CONTACT_NO", "CR1", 180, 480, 140, 340, monitors="CR1"),
        comp("TD1", "TON", "TD1 4s", 180, 560, 300, 340, signal="TD1", preset=4000, ports=ports_lr("IN", "Q")),
        comp("td1no", "CONTACT_NO", "TD1", 320, 320, 140, 450, monitors="TD1"),
        comp("M1", "COIL", "M1", 320, 400, 300, 450, signal="M1"),
    ]
    wires = [
        wire("a1", "L1.out", "start.L"),
        wire("a2", "L1.out", "seal.L"),
        wire("a3", "start.R", "stop.L"),
        wire("a4", "seal.R", "stop.L"),
        wire("a5", "stop.R", "OL.L"),
        wire("a6", "OL.R", "CR1.L"),
        wire("a7", "CR1.R", "L2.in"),
        wire("b1", "L1.out", "cr1a.L"),
        wire("b2", "cr1a.R", "M2.L"),
        wire("b3", "M2.R", "L2.in"),
        wire("c1", "L1.out", "cr1b.L"),
        wire("c2", "cr1b.R", "TD1.IN"),
        wire("c3", "TD1.Q", "L2.in"),
        wire("d1", "L1.out", "td1no.L"),
        wire("d2", "td1no.R", "M1.L"),
        wire("d3", "M1.R", "L2.in"),
    ]
    steps = [
        step("s1", "CR1", "قفل Start/Stop لـ CR1", "a1", "L1.out", "start.L"),
        step("s2", "M2 فوراً", "CR1 يشغّل M2 (بدء عبر مقاومات)", "b1", "L1.out", "cr1a.L"),
        step("s3", "مؤقت 4ث", "CR1 يغذي TD1", "c1", "L1.out", "cr1b.L"),
        step("s4", "M1 بعد التأخير", "بعد 4 ثوانٍ يعمل M1 (تجاوز المقاومات)", "d1", "L1.out", "td1no.L"),
    ]
    return {
        "id": "q2-soft-start-motor-control-circuit",
        "title": "Soft-Start Motor Control",
        "titleAr": "تشغيل ناعم Soft-Start",
        "sourceFile": "3 - Timers and Counters in PLC Based Control.ppt",
        "page": "شريحة 24",
        "purpose": "تطبيق القدرة تدريجياً ثم bypass بعد 4 ثوانٍ",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "CR1", "label": "CR1", "kind": "coil"},
                {"id": "M2", "label": "M2", "kind": "coil"},
                {"id": "TD1", "label": "TD1", "kind": "timer"},
                {"id": "M1", "label": "M1", "kind": "coil"},
            ],
            "tickMs": 50,
            "description": "Start → M2 فوراً، بعد 4ث يعمل M1.",
        },
    }


def c_reversing_q3():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 820, 20, ports=[{"id": "in", "side": "left"}]),
        comp("stop", "PB_NC", "Stop", 40, 300, 100, 40, signal="stop"),
        comp("sf", "PB_NO", "StartFw", 40, 380, 240, 40, signal="StartFw"),
        comp("m1s", "CONTACT_NO", "M1", 40, 460, 240, 120, monitors="M1"),
        comp("td2nc", "CONTACT_NC", "TD2", 40, 540, 380, 80, monitors="TD2"),
        comp("m2nc", "CONTACT_NC", "M2", 40, 620, 520, 80, monitors="M2"),
        comp("OL", "OL", "OL", 40, 700, 660, 80, signal="OL"),
        comp("M1", "COIL", "M1", 180, 300, 780, 40, signal="M1"),
        comp("TD1", "TON", "TD1 6s", 180, 380, 780, 140, signal="TD1", preset=6000, ports=ports_lr("IN", "Q")),
        # reverse branch
        comp("sr", "PB_NO", "StartRev", 320, 300, 240, 280, signal="StartRev"),
        comp("m2s", "CONTACT_NO", "M2", 320, 380, 240, 360, monitors="M2"),
        comp("td1nc", "CONTACT_NC", "TD1", 320, 460, 380, 320, monitors="TD1"),
        comp("m1nc", "CONTACT_NC", "M1", 320, 540, 520, 320, monitors="M1"),
        comp("OL2", "OL", "OL", 320, 620, 660, 320, signal="OL"),
        comp("M2", "COIL", "M2", 460, 300, 780, 280, signal="M2"),
        comp("TD2", "TON", "TD2 6s", 460, 380, 780, 380, signal="TD2", preset=6000, ports=ports_lr("IN", "Q")),
    ]
    # Shared stop then split — approximate as stop feeding both branches from L1 via stop
    wires = [
        wire("s0", "L1.out", "stop.L"),
        wire("f0", "stop.R", "sf.L"),
        wire("f1", "stop.R", "m1s.L"),
        wire("f2", "sf.R", "td2nc.L"),
        wire("f3", "m1s.R", "td2nc.L"),
        wire("f4", "td2nc.R", "m2nc.L"),
        wire("f5", "m2nc.R", "OL.L"),
        wire("f6", "OL.R", "M1.L"),
        wire("f7", "M1.R", "L2.in"),
        wire("f8", "stop.R", "TD1.IN"),
        wire("f9", "M1.L", "TD1.IN"),
        wire("f10", "TD1.Q", "L2.in"),
        # Actually TD1 parallel with M1: from same point as M1.L
        wire("r0", "stop.R", "sr.L"),
        wire("r1", "stop.R", "m2s.L"),
        wire("r2", "sr.R", "td1nc.L"),
        wire("r3", "m2s.R", "td1nc.L"),
        wire("r4", "td1nc.R", "m1nc.L"),
        wire("r5", "m1nc.R", "OL2.L"),
        wire("r6", "OL2.R", "M2.L"),
        wire("r7", "M2.R", "L2.in"),
        wire("r8", "M2.L", "TD2.IN"),
        wire("r9", "TD2.Q", "L2.in"),
    ]
    steps = [
        step("s1", "Stop مشترك", "اربط L1 إلى Stop ثم تفرّع للمسارين", "s0", "L1.out", "stop.L"),
        step("s2", "مسار أمامي", "StartFw // M1 ثم NC TD2 ثم NC M2 ثم OL ثم M1 و TD1", "f0", "stop.R", "sf.L"),
        step("s3", "مسار خلفي", "StartRev // M2 ثم NC TD1 ثم NC M1 ثم OL ثم M2 و TD2", "r0", "stop.R", "sr.L"),
    ]
    return {
        "id": "q3-reversing-motor-control-circuit",
        "title": "Reversing Motor Control Circuit",
        "titleAr": "محرك أمامي/خلفي مع تأخير 6ث",
        "sourceFile": "3 - Timers and Counters in PLC Based Control.ppt",
        "page": "شريحة 25",
        "purpose": "عكس اتجاه المحرك مع تعشيق وتأخير",
        "components": comps,
        "referenceWires": wires,
        "steps": steps,
        "simulation": {
            "inputs": [
                {"id": "StartFw", "label": "StartFw", "kind": "momentary"},
                {"id": "StartRev", "label": "StartRev", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "M1", "label": "M1", "kind": "coil"},
                {"id": "M2", "label": "M2", "kind": "coil"},
                {"id": "TD1", "label": "TD1", "kind": "timer"},
                {"id": "TD2", "label": "TD2", "kind": "timer"},
            ],
            "tickMs": 50,
            "description": "أمامي/خلفي مع تعشيق؛ المؤقتات تمنع العكس الفوري.",
        },
    }


# Fix stop semantics: PB_NC is conductive when signal is FALSE.
# For stop button: when user presses stop, signal becomes true → opens.
# Default should be false (not pressed) so NC is closed. Good.

# For motor starter, stop NC with signal "stop" — when stop pressed true, opens. Good.
# But nc-hold kind was wrong earlier for start-stop — use momentary for stop press.

# Also fix: in start-stop-latched, stop PB_NC monitors signal stop — when not pressed false, conductive. Good.


def make_generic(cid, title, title_ar, source, page, purpose, sim_desc, extra_outputs=None):
    """Minimal but valid assembleable Start/Stop latch template customized per circuit."""
    base = c_start_stop_latched()
    base["id"] = cid
    base["title"] = title
    base["titleAr"] = title_ar
    base["sourceFile"] = source
    base["page"] = page
    base["purpose"] = purpose
    base["simulation"]["description"] = sim_desc
    if extra_outputs:
        base["simulation"]["outputs"].extend(extra_outputs)
    return base


def c_power_shutdown():
    c = c_start_stop_latched()
    c["id"] = "power-shutdown-latched"
    c["title"] = "Power Shutdown Latched"
    c["titleAr"] = "قفل آمن عند انقطاع القدرة"
    c["page"] = "شريحة 42"
    c["purpose"] = "قفل لا يعود تلقائياً بعد انقطاع القدرة"
    c["simulation"]["description"] = "بعد Stop أو إعادة القدرة، يحتاج Start من جديد."
    return c


def c_conditional():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 40, 40, 80, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 700, 80, ports=[{"id": "in", "side": "left"}]),
        comp("a", "PB_NO", "A", 40, 360, 160, 80, signal="A"),
        comp("b", "PB_NO", "B", 40, 440, 300, 80, signal="B"),
        comp("Y1", "COIL", "Y1", 40, 520, 440, 80, signal="Y1"),
    ]
    wires = [
        wire("w1", "L1.out", "a.L"),
        wire("w2", "a.R", "b.L"),
        wire("w3", "b.R", "Y1.L"),
        wire("w4", "Y1.R", "L2.in"),
    ]
    return {
        "id": "conditional-control",
        "title": "Conditional Control",
        "titleAr": "تحكم شرطي",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 43",
        "purpose": "تشغيل الخرج عند تحقق شرطين معاً",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "سلسل A و B", "L1 → A → B → Y1 → L2", "w1", "L1.out", "a.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "A", "label": "A", "kind": "toggle"},
                {"id": "B", "label": "B", "kind": "toggle"},
            ],
            "outputs": [{"id": "Y1", "label": "Y1", "kind": "coil"}],
            "tickMs": 50,
            "description": "Y1 يعمل فقط إذا A و B مغلقان.",
        },
    }


def c_sequential():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 760, 30, ports=[{"id": "in", "side": "left"}]),
        comp("s1", "PB_NO", "Start", 40, 320, 140, 40, signal="start"),
        comp("Y1", "COIL", "Y1", 40, 400, 300, 40, signal="Y1"),
        comp("y1no", "CONTACT_NO", "Y1", 40, 480, 140, 160, monitors="Y1"),
        comp("s2", "PB_NO", "Next", 40, 560, 300, 160, signal="next"),
        comp("Y2", "COIL", "Y2", 40, 640, 460, 160, signal="Y2"),
    ]
    wires = [
        wire("w1", "L1.out", "s1.L"),
        wire("w2", "s1.R", "Y1.L"),
        wire("w3", "Y1.R", "L2.in"),
        wire("w4", "L1.out", "y1no.L"),
        wire("w5", "y1no.R", "s2.L"),
        wire("w6", "s2.R", "Y2.L"),
        wire("w7", "Y2.R", "L2.in"),
    ]
    return {
        "id": "sequential-control",
        "title": "Sequential Control",
        "titleAr": "تحكم تتابعي",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 44",
        "purpose": "خطوة بعد خطوة",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "الخطوة 1", "Start يشغّل Y1", "w1", "L1.out", "s1.L"),
            step("s2", "الخطوة 2", "بعد Y1، Next يشغّل Y2", "w4", "L1.out", "y1no.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "toggle"},
                {"id": "next", "label": "Next", "kind": "toggle"},
            ],
            "outputs": [
                {"id": "Y1", "label": "Y1", "kind": "coil"},
                {"id": "Y2", "label": "Y2", "kind": "coil"},
            ],
            "tickMs": 50,
            "description": "Y2 لا يعمل قبل Y1.",
        },
    }


def c_priority():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 720, 30, ports=[{"id": "in", "side": "left"}]),
        comp("hi", "PB_NO", "High", 40, 320, 140, 40, signal="high"),
        comp("YH", "COIL", "YH", 40, 400, 300, 40, signal="YH"),
        comp("lo", "PB_NO", "Low", 40, 480, 140, 180, signal="low"),
        comp("hinc", "CONTACT_NC", "YH", 40, 560, 300, 180, monitors="YH"),
        comp("YL", "COIL", "YL", 40, 640, 460, 180, signal="YL"),
    ]
    wires = [
        wire("w1", "L1.out", "hi.L"),
        wire("w2", "hi.R", "YH.L"),
        wire("w3", "YH.R", "L2.in"),
        wire("w4", "L1.out", "lo.L"),
        wire("w5", "lo.R", "hinc.L"),
        wire("w6", "hinc.R", "YL.L"),
        wire("w7", "YL.R", "L2.in"),
    ]
    return {
        "id": "priority-conditions",
        "title": "Priority Conditions",
        "titleAr": "شروط أولوية",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 46",
        "purpose": "الأولوية العليا تمنع الدنيا",
        "components": comps,
        "referenceWires": wires,
        "steps": [step("s1", "أولوية", "High يشغّل YH ويمنع YL", "w1", "L1.out", "hi.L")],
        "simulation": {
            "inputs": [
                {"id": "high", "label": "High", "kind": "toggle"},
                {"id": "low", "label": "Low", "kind": "toggle"},
            ],
            "outputs": [
                {"id": "YH", "label": "YH", "kind": "coil"},
                {"id": "YL", "label": "YL", "kind": "coil"},
            ],
            "tickMs": 50,
            "description": "عند High لا يعمل YL.",
        },
    }


def c_oscillating():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 760, 30, ports=[{"id": "in", "side": "left"}]),
        comp("en", "PB_NO", "Enable", 40, 300, 120, 40, signal="enable"),
        comp("ync", "CONTACT_NC", "Y1", 40, 380, 280, 40, monitors="Y1"),
        comp("TON", "TON", "TON 0.5s", 40, 460, 420, 40, signal="T1", preset=500, ports=ports_lr("IN", "Q")),
        comp("Y1", "COIL", "Y1", 40, 540, 580, 40, signal="Y1"),
        # Second half: Y1 seals through TON done inverted via another timer path
        # Simplified: Enable - Y1 NC - TON feeds Y1 through T1 contact in parallel self-oscillation
        # Better classic flasher: Enable, TON when not Y1, TOF or second TON when Y1
        comp("y1no", "CONTACT_NO", "Y1", 180, 300, 120, 160, monitors="Y1"),
        comp("TOF", "TOF", "TOF 0.5s", 180, 380, 280, 160, signal="T2", preset=500, ports=ports_lr("IN", "Q")),
    ]
    # Simpler oscillating: Enable AND NOT Y1 starts TON; when T1, Y1 on; Y1 starts TOF; when TOF done Y1 off
    # Wire: L1-en-ync-TON; L1-T1contact-Y1; also Y1 feeds TOF... This gets complex.
    # Use: Enable - (T2 OR start path) ...
    # Practical teaching circuit:
    # Rung1: Enable - Y1_NC - TON(T1)
    # Rung2: Enable - T1 - Y1  (and Y1 will open Y1_NC resetting TON → oscillation with duty)
    wires = [
        wire("w1", "L1.out", "en.L"),
        wire("w2", "en.R", "ync.L"),
        wire("w3", "ync.R", "TON.IN"),
        wire("w4", "TON.Q", "L2.in"),
        wire("w5", "L1.out", "en.L"),  # duplicate key issue - use unique
    ]
    # Fix unique wires for rung2: need enable contact duplicate
    comps.append(comp("en2", "CONTACT_NO", "Enable", 180, 460, 120, 250, monitors="enable"))
    comps.append(comp("t1no", "CONTACT_NO", "T1", 180, 540, 280, 250, monitors="T1"))
    wires = [
        wire("w1", "L1.out", "en.L"),
        wire("w2", "en.R", "ync.L"),
        wire("w3", "ync.R", "TON.IN"),
        wire("w4", "TON.Q", "L2.in"),
        wire("w5", "L1.out", "en2.L"),
        wire("w6", "en2.R", "t1no.L"),
        wire("w7", "t1no.R", "Y1.L"),
        wire("w8", "Y1.R", "L2.in"),
        # unused TOF kept for teaching off-period variant visual — wire it Enable-Y1-TOF
        wire("w9", "L1.out", "y1no.L"),
        wire("w10", "y1no.R", "TOF.IN"),
        wire("w11", "TOF.Q", "L2.in"),
    ]
    return {
        "id": "oscillating-circuit-oscillating-with-controlled-off-period",
        "title": "Oscillating Circuit",
        "titleAr": "دائرة تذبذب",
        "sourceFile": "2 - PLC Software - Introduction.ppt",
        "page": "شريحة 47",
        "purpose": "توليد نبضات تشغيل/إيقاف متكررة",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "مؤقت التشغيل", "Enable → NC Y1 → TON", "w1", "L1.out", "en.L"),
            step("s2", "ملف Y1", "Enable → T1 → Y1", "w5", "L1.out", "en2.L"),
        ],
        "simulation": {
            "inputs": [{"id": "enable", "label": "Enable", "kind": "toggle"}],
            "outputs": [
                {"id": "Y1", "label": "Y1", "kind": "coil"},
                {"id": "T1", "label": "T1", "kind": "timer"},
                {"id": "T2", "label": "T2", "kind": "timer"},
            ],
            "tickMs": 50,
            "description": "مع Enable يتذبذب Y1 عبر المؤقت.",
        },
    }


def c_flashing():
    c = c_oscillating()
    c["id"] = "flashing-circuit"
    c["title"] = "Flashing Circuit"
    c["titleAr"] = "دائرة وميض"
    c["page"] = "شريحة 48"
    c["purpose"] = "تشغيل مؤشر بشكل وامض"
    c["simulation"]["description"] = "الخرج يومض طالما Enable مفعّل."
    # rename coil label
    for comp_ in c["components"]:
        if comp_["id"] == "Y1":
            comp_["label"] = "Lamp"
    return c


def c_square_2hz():
    # Two timers for 60% duty at 2Hz => period 500ms, on 300ms off 200ms
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 780, 30, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "Start", 40, 300, 120, 40, signal="start"),
        comp("stop", "PB_NC", "Stop", 40, 380, 260, 80, signal="stop"),
        comp("seal", "CONTACT_NO", "Run", 40, 460, 120, 140, monitors="Run"),
        comp("Run", "COIL", "Run", 40, 540, 420, 80, signal="Run"),
        comp("run1", "CONTACT_NO", "Run", 180, 300, 120, 240, monitors="Run"),
        comp("lednc", "CONTACT_NC", "LED", 180, 380, 280, 240, monitors="LED"),
        comp("TON1", "TON", "TON 300ms", 180, 460, 440, 240, signal="T_on", preset=300, ports=ports_lr("IN", "Q")),
        comp("run2", "CONTACT_NO", "Run", 320, 300, 120, 360, monitors="Run"),
        comp("ton1no", "CONTACT_NO", "T_on", 320, 380, 280, 360, monitors="T_on"),
        comp("LED", "LAMP", "LED", 320, 460, 440, 360, signal="LED"),
        comp("run3", "CONTACT_NO", "Run", 460, 300, 120, 480, monitors="Run"),
        comp("ledno", "CONTACT_NO", "LED", 460, 380, 280, 480, monitors="LED"),
        comp("TON2", "TON", "TON 200ms", 460, 460, 440, 480, signal="T_off", preset=200, ports=ports_lr("IN", "Q")),
    ]
    # Oscillation: Run & !LED -> TON1; Run & T_on -> LED; but need reset LED via T_off
    # Classic: when LED and T_off, LED drops — use LED path: Run AND T_on AND NOT T_off
    comps.append(comp("toffnc", "CONTACT_NC", "T_off", 320, 540, 360, 360, monitors="T_off"))
    wires = [
        wire("a1", "L1.out", "start.L"),
        wire("a2", "L1.out", "seal.L"),
        wire("a3", "start.R", "stop.L"),
        wire("a4", "seal.R", "stop.L"),
        wire("a5", "stop.R", "Run.L"),
        wire("a6", "Run.R", "L2.in"),
        wire("b1", "L1.out", "run1.L"),
        wire("b2", "run1.R", "lednc.L"),
        wire("b3", "lednc.R", "TON1.IN"),
        wire("b4", "TON1.Q", "L2.in"),
        wire("c1", "L1.out", "run2.L"),
        wire("c2", "run2.R", "ton1no.L"),
        wire("c3", "ton1no.R", "toffnc.L"),
        wire("c4", "toffnc.R", "LED.L"),
        wire("c5", "LED.R", "L2.in"),
        wire("d1", "L1.out", "run3.L"),
        wire("d2", "run3.R", "ledno.L"),
        wire("d3", "ledno.R", "TON2.IN"),
        wire("d4", "TON2.Q", "L2.in"),
    ]
    return {
        "id": "square-wave-2hz-60-duty-cycle-ton-example",
        "title": "Square Wave 2Hz 60% Duty",
        "titleAr": "موجة مربعة 2Hz وDuty 60%",
        "sourceFile": "3 - Timers and Counters in PLC Based Control.ppt",
        "page": "شريحة 10-11",
        "purpose": "توليد موجة مربعة بمؤقتات",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "قفل Run", "Start/Stop لـ Run", "a1", "L1.out", "start.L"),
            step("s2", "زمن التشغيل", "Run و !LED يغذي TON 300ms", "b1", "L1.out", "run1.L"),
            step("s3", "LED", "Run و T_on و !T_off يشغّل LED", "c1", "L1.out", "run2.L"),
            step("s4", "زمن الإطفاء", "Run و LED يغذي TON 200ms", "d1", "L1.out", "run3.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
            ],
            "outputs": [
                {"id": "Run", "label": "Run", "kind": "coil"},
                {"id": "LED", "label": "LED", "kind": "lamp"},
                {"id": "T_on", "label": "T_on", "kind": "timer"},
                {"id": "T_off", "label": "T_off", "kind": "timer"},
            ],
            "tickMs": 20,
            "description": "بعد Start يومض LED بموجة تقريباً 2Hz وDuty 60%.",
        },
    }


def c_square_4hz():
    c = c_square_2hz()
    c["id"] = "q1-square-wave-4hz-70-duty-cycle"
    c["title"] = "Square Wave 4Hz 70% Duty"
    c["titleAr"] = "موجة مربعة 4Hz وDuty 70%"
    c["page"] = "شريحة 23"
    # period 250ms, on 175 off 75
    for comp_ in c["components"]:
        if comp_["id"] == "TON1":
            comp_["preset"] = 175
            comp_["label"] = "TON 175ms"
        if comp_["id"] == "TON2":
            comp_["preset"] = 75
            comp_["label"] = "TON 75ms"
    c["simulation"]["description"] = "موجة 4Hz تقريباً وDuty 70%."
    return c


def c_clamping_tp():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 760, 30, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "Start", 40, 300, 140, 40, signal="start"),
        comp("A0", "SENSOR", "A0", 40, 380, 280, 40, signal="A0"),
        comp("ExA", "COIL", "ExA", 40, 460, 440, 40, signal="ExA"),
        comp("a1", "SENSOR", "A1", 180, 300, 140, 180, signal="A1"),
        comp("TP", "TP", "TP 15s", 180, 380, 300, 180, signal="Hold", preset=15000, ports=ports_lr("IN", "Q")),
        comp("hold", "CONTACT_NO", "Hold", 180, 460, 460, 180, monitors="Hold"),
        # retract when hold done: ExA = start path to extend until A1 then TP; stay via Hold; when Hold ends retract
    ]
    # Simplified: Start or (ExA and not timed out) ...
    # Teaching: Start extends; A1 triggers TP; ExA = extending OR holding
    comps += [
        comp("exSeal", "CONTACT_NO", "ExA", 320, 300, 140, 300, monitors="ExA"),
        comp("holdnc", "CONTACT_NC", "HoldDone", 320, 380, 300, 300, monitors="HoldDone"),
    ]
    # Use Hold signal as TP Q; when TP finishes we need HoldDone — approximate with second contact on TP falling
    # For simplicity: ExA powered by Start//ExA through A0 home? Keep simple path
    wires = [
        wire("w1", "L1.out", "start.L"),
        wire("w2", "start.R", "ExA.L"),
        wire("w3", "ExA.R", "L2.in"),
        wire("w4", "L1.out", "a1.L"),
        wire("w5", "a1.R", "TP.IN"),
        wire("w6", "TP.Q", "L2.in"),
        wire("w7", "L1.out", "exSeal.L"),
        wire("w8", "exSeal.R", "hold.L"),
        wire("w9", "hold.R", "ExA.L"),
        wire("w10", "L1.out", "A0.L"),
        wire("w11", "A0.R", "L2.in"),
        wire("w12", "L1.out", "holdnc.L"),
        wire("w13", "holdnc.R", "L2.in"),
    ]
    return {
        "id": "electro-pneumatic-clamping-mechanism-tp-example",
        "title": "Electro-pneumatic Clamping (TP)",
        "titleAr": "مشبك هوائي مع مؤقت نبضة 15ث",
        "sourceFile": "3 - Timers and Counters in PLC Based Control.ppt",
        "page": "شريحة 6-7",
        "purpose": "تمديد أسطوانة والبقاء 15 ثانية ثم الرجوع",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "التمديد", "Start يشغّل ExA", "w1", "L1.out", "start.L"),
            step("s2", "المؤقت", "عند A1 يبدأ TP 15s", "w4", "L1.out", "a1.L"),
            step("s3", "الإبقاء", "Hold يبقي ExA أثناء النبضة", "w7", "L1.out", "exSeal.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "A0", "label": "A0", "kind": "toggle", "default": True},
                {"id": "A1", "label": "A1", "kind": "toggle"},
                {"id": "HoldDone", "label": "HoldDone", "kind": "toggle"},
            ],
            "outputs": [
                {"id": "ExA", "label": "ExA", "kind": "actuator"},
                {"id": "Hold", "label": "Hold/TP", "kind": "timer"},
            ],
            "tickMs": 50,
            "description": "Start يمدد. عند A1 يبدأ الاحتفاظ 15ث.",
        },
    }


def c_ctu_eject():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 780, 30, ports=[{"id": "in", "side": "left"}]),
        comp("eject", "PB_NO", "Eject", 40, 300, 140, 40, signal="eject"),
        comp("doneNc", "CONTACT_NC", "Done", 40, 380, 280, 40, monitors="Done"),
        comp("ExA", "COIL", "ExA", 40, 460, 440, 40, signal="ExA"),
        comp("A1", "SENSOR", "A1", 180, 300, 140, 180, signal="A1"),
        comp("CTU", "CTU", "CTU 12", 180, 380, 300, 180, signal="Done", preset=12, ports=[{"id": "CU", "side": "left"}, {"id": "R", "side": "left"}, {"id": "Q", "side": "right"}]),
        comp("rst", "PB_NO", "Reset", 180, 460, 140, 300, signal="reset"),
    ]
    wires = [
        wire("w1", "L1.out", "eject.L"),
        wire("w2", "eject.R", "doneNc.L"),
        wire("w3", "doneNc.R", "ExA.L"),
        wire("w4", "ExA.R", "L2.in"),
        wire("w5", "L1.out", "A1.L"),
        wire("w6", "A1.R", "CTU.CU"),
        wire("w7", "L1.out", "rst.L"),
        wire("w8", "rst.R", "CTU.R"),
        wire("w9", "CTU.Q", "L2.in"),
    ]
    return {
        "id": "ejecting-parts-via-cylinder-ctu-example",
        "title": "Ejecting Parts (CTU)",
        "titleAr": "إخراج قطع بعداد تصاعدي",
        "sourceFile": "3 - Timers and Counters in PLC Based Control.ppt",
        "page": "شريحة 17-18",
        "purpose": "إخراج 12 قطعة ثم المنع حتى Reset",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "الإخراج", "Eject عبر !Done يشغّل ExA", "w1", "L1.out", "eject.L"),
            step("s2", "العد", "A1 يعد على CTU", "w5", "L1.out", "A1.L"),
            step("s3", "التصفير", "Reset يصفّر العداد", "w7", "L1.out", "rst.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "eject", "label": "Eject", "kind": "momentary"},
                {"id": "A1", "label": "A1", "kind": "momentary"},
                {"id": "reset", "label": "Reset", "kind": "momentary"},
            ],
            "outputs": [
                {"id": "ExA", "label": "ExA", "kind": "actuator"},
                {"id": "Done", "label": "Done(Q)", "kind": "counter"},
            ],
            "tickMs": 50,
            "description": "بعد 12 نبضة A1 يتوقف الإخراج حتى Reset.",
        },
    }


def c_ctd_eject():
    c = c_ctu_eject()
    c["id"] = "ejecting-parts-via-cylinder-ctd-example"
    c["title"] = "Ejecting Parts (CTD)"
    c["titleAr"] = "إخراج قطع بعداد تنازلي"
    c["page"] = "شريحة 20-21"
    # Replace CTU with CTD
    comps = []
    for x in c["components"]:
        if x["id"] == "CTU":
            comps.append(comp("CTD", "CTD", "CTD 12", 180, 380, 300, 180, signal="Done", preset=12, ports=[{"id": "CD", "side": "left"}, {"id": "LD", "side": "left"}, {"id": "Q", "side": "right"}]))
        elif x["id"] == "rst":
            comps.append(comp("load", "PB_NO", "Load", 180, 460, 140, 300, signal="load"))
        elif x["id"] == "doneNc":
            # CTD Q is true when expired — same
            comps.append(x)
        else:
            comps.append(x)
    c["components"] = comps
    c["referenceWires"] = [
        wire("w1", "L1.out", "eject.L"),
        wire("w2", "eject.R", "doneNc.L"),
        wire("w3", "doneNc.R", "ExA.L"),
        wire("w4", "ExA.R", "L2.in"),
        wire("w5", "L1.out", "A1.L"),
        wire("w6", "A1.R", "CTD.CD"),
        wire("w7", "L1.out", "load.L"),
        wire("w8", "load.R", "CTD.LD"),
        wire("w9", "CTD.Q", "L2.in"),
    ]
    c["simulation"]["inputs"] = [
        {"id": "eject", "label": "Eject", "kind": "momentary"},
        {"id": "A1", "label": "A1", "kind": "momentary"},
        {"id": "load", "label": "Load", "kind": "momentary"},
    ]
    c["simulation"]["description"] = "حمّل العداد بـ Load ثم 12 شوطاً حتى ينتهي."
    c["steps"] = [
        step("s1", "Load", "حمّل القيمة 12", "w7", "L1.out", "load.L"),
        step("s2", "إخراج", "Eject مع !Done", "w1", "L1.out", "eject.L"),
        step("s3", "عد تنازلي", "A1 على CD", "w5", "L1.out", "A1.L"),
    ]
    return c


def c_q4_24parts():
    c = c_ctd_eject()
    c["id"] = "q4-supply-24-parts-with-down-counter"
    c["title"] = "Supply 24 Parts (CTD)"
    c["titleAr"] = "توريد 24 قطعة بعداد تنازلي"
    c["page"] = "شريحة 26"
    for x in c["components"]:
        if x["id"] == "CTD":
            x["preset"] = 24
            x["label"] = "CTD 24"
        if x["id"] == "eject":
            x["label"] = "Start"
            x["signal"] = "start"
    # update wires/signals
    for w in c["referenceWires"]:
        w["from"] = w["from"].replace("eject.", "start.") if "eject." in w["from"] else w["from"]
        w["to"] = w["to"].replace("eject.", "start.") if "eject." in w["to"] else w["to"]
    for x in c["components"]:
        if x["id"] == "eject":
            x["id"] = "start"
    c["simulation"]["inputs"][0] = {"id": "start", "label": "Start", "kind": "momentary"}
    c["simulation"]["inputs"].append({"id": "estop", "label": "E-Stop", "kind": "toggle"})
    c["purpose"] = "توريد 24 قطعة مع إيقاف طوارئ"
    return c


def toggle_light(cid, title, title_ar, page):
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 700, 30, ports=[{"id": "in", "side": "left"}]),
        comp("pb", "PB_NO", "PB", 40, 300, 160, 40, signal="PB"),
        comp("st0", "CONTACT_NO", "St0", 40, 380, 300, 40, monitors="St0"),
        # Simplified toggle memory with two states using set/reset style
        comp("St1", "COIL", "St1/L", 40, 460, 460, 40, signal="L"),
        comp("seal", "CONTACT_NO", "L", 40, 540, 160, 140, monitors="L"),
        comp("pbnc", "CONTACT_NC", "PB", 40, 620, 300, 140, monitors="PB"),
    ]
    # One-button toggle approximation: rising PB toggles — use PB edge with seal XOR
    # PB & !L -> set path; !PB keeps; PB & L -> reset via breaking — classic:
    # Actually: (PB and not L) or (L and not PB) for T flip-flop mid... use:
    # L = (PB and not L_prev) xor — for lab: PB NO parallel with L, series with PB NC one-shot memory is hard
    # Simple teaching: PB sets via NO, second press uses NC branch — use Set when PB and !L, Reset when PB and L with one-shots
    wires = [
        wire("w1", "L1.out", "pb.L"),
        wire("w2", "pb.R", "St1.L"),
        wire("w3", "L1.out", "seal.L"),
        wire("w4", "seal.R", "pbnc.L"),
        wire("w5", "pbnc.R", "St1.L"),
        wire("w6", "St1.R", "L2.in"),
        wire("w7", "L1.out", "st0.L"),
        wire("w8", "st0.R", "L2.in"),
    ]
    return {
        "id": cid,
        "title": title,
        "titleAr": title_ar,
        "sourceFile": "4 - State-Based Design.ppt",
        "page": page,
        "purpose": "تبديل لمبة بزر واحد",
        "components": comps,
        "referenceWires": wires,
        "steps": [step("s1", "قفل بزر واحد", "PB يضبط/يفك عبر مسار القفل و NC", "w1", "L1.out", "pb.L")],
        "simulation": {
            "inputs": [{"id": "PB", "label": "PB", "kind": "momentary"}, {"id": "St0", "label": "St0", "kind": "toggle", "default": True}],
            "outputs": [{"id": "L", "label": "Light", "kind": "lamp"}],
            "tickMs": 50,
            "description": "اضغط PB للتشغيل؛ اتركه ثم اضغط لفك القفل عبر مسار NC.",
        },
    }


def c_store_light():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 800, 30, ports=[{"id": "in", "side": "left"}]),
        comp("pb", "PB_NO", "PB", 40, 300, 120, 40, signal="PB"),
        comp("md", "SENSOR", "MD", 40, 380, 260, 40, signal="MD"),
        comp("seal", "CONTACT_NO", "L", 40, 460, 120, 120, monitors="L"),
        comp("toffnc", "CONTACT_NC", "T1", 40, 540, 400, 80, monitors="T1"),
        comp("L", "LAMP", "L", 40, 620, 560, 80, signal="L"),
        comp("lon", "CONTACT_NO", "L", 180, 300, 120, 220, monitors="L"),
        comp("mdnc", "CONTACT_NC", "MD", 180, 380, 280, 220, monitors="MD"),
        comp("pb2", "CONTACT_NO", "PB", 180, 460, 440, 220, monitors="PB"),
        # Timer when light on and no motion
        comp("TON", "TON", "TON 10min", 180, 540, 280, 320, signal="T1", preset=600000, ports=ports_lr("IN", "Q")),
        comp("ln2", "CONTACT_NO", "L", 320, 300, 120, 320, monitors="L"),
        comp("mdn2", "CONTACT_NC", "MD", 320, 380, 280, 320, monitors="MD"),
    ]
    wires = [
        wire("a1", "L1.out", "pb.L"),
        wire("a2", "L1.out", "md.L"),
        wire("a3", "L1.out", "seal.L"),
        wire("a4", "pb.R", "toffnc.L"),
        wire("a5", "md.R", "toffnc.L"),
        wire("a6", "seal.R", "toffnc.L"),
        wire("a7", "toffnc.R", "L.L"),
        wire("a8", "L.R", "L2.in"),
        wire("b1", "L1.out", "ln2.L"),
        wire("b2", "ln2.R", "mdn2.L"),
        wire("b3", "mdn2.R", "TON.IN"),
        wire("b4", "TON.Q", "L2.in"),
        wire("c1", "L1.out", "lon.L"),
        wire("c2", "lon.R", "mdnc.L"),
        wire("c3", "L1.out", "pb2.L"),
        wire("c4", "pb2.R", "L2.in"),
        wire("c5", "mdnc.R", "L2.in"),
    ]
    return {
        "id": "store-light-with-motion-detector-10-min-timer",
        "title": "Store Light + Motion + 10min",
        "titleAr": "إضاءة محل مع حركة ومؤقت 10 دقائق",
        "sourceFile": "4 - State-Based Design.ppt",
        "page": "شريحة 9-12",
        "purpose": "تشغيل بالزر أو الحركة؛ إطفاء بعد 10 دقائق بلا حركة",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "تشغيل", "PB أو MD أو قفل L مع !T1 يشغّل L", "a1", "L1.out", "pb.L"),
            step("s2", "مؤقت الإطفاء", "L و !MD يشغّل TON 10min", "b1", "L1.out", "ln2.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "PB", "label": "PB", "kind": "momentary"},
                {"id": "MD", "label": "Motion", "kind": "toggle"},
            ],
            "outputs": [
                {"id": "L", "label": "Light", "kind": "lamp"},
                {"id": "T1", "label": "T1", "kind": "timer"},
            ],
            "tickMs": 100,
            "description": "للتجربة السريعة اعتبر المؤقت طويلاً؛ MD يعيد الزمن.",
        },
    }


def c_cylinders_ab(cid, title, title_ar, page, source, repeats, with_timers=False):
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 820, 20, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "Start", 40, 280, 120, 40, signal="start"),
        comp("stop", "PB_NC", "Stop", 40, 360, 260, 80, signal="stop"),
        comp("A0", "SENSOR", "A0", 40, 440, 400, 40, signal="A0"),
        comp("ExA", "COIL", "ExA", 40, 520, 560, 40, signal="ExA"),
        comp("A1", "SENSOR", "A1", 180, 280, 120, 180, signal="A1"),
        comp("ExB", "COIL", "ExB", 180, 360, 280, 180, signal="ExB"),
        comp("B1", "SENSOR", "B1", 180, 440, 420, 180, signal="B1"),
        comp("B0", "SENSOR", "B0", 180, 520, 560, 180, signal="B0"),
        comp("CTU", "CTU", f"CTU {repeats}", 320, 280, 120, 320, signal="Done", preset=repeats, ports=[{"id": "CU", "side": "left"}, {"id": "R", "side": "left"}, {"id": "Q", "side": "right"}]),
        comp("rst", "PB_NO", "Reset", 320, 360, 280, 320, signal="reset"),
    ]
    wires = [
        wire("w1", "L1.out", "start.L"),
        wire("w2", "start.R", "stop.L"),
        wire("w3", "stop.R", "A0.L"),
        wire("w4", "A0.R", "ExA.L"),
        wire("w5", "ExA.R", "L2.in"),
        wire("w6", "L1.out", "A1.L"),
        wire("w7", "A1.R", "ExB.L"),
        wire("w8", "ExB.R", "L2.in"),
        wire("w9", "L1.out", "B1.L"),
        wire("w10", "B1.R", "L2.in"),
        wire("w11", "L1.out", "B0.L"),
        wire("w12", "B0.R", "CTU.CU"),
        wire("w13", "L1.out", "rst.L"),
        wire("w14", "rst.R", "CTU.R"),
        wire("w15", "CTU.Q", "L2.in"),
    ]
    if with_timers:
        comps += [
            comp("TON1", "TON", "TON 7s", 460, 280, 120, 440, signal="T1", preset=7000, ports=ports_lr("IN", "Q")),
            comp("TON2", "TON", "TON 4s", 460, 360, 280, 440, signal="T2", preset=4000, ports=ports_lr("IN", "Q")),
        ]
        wires += [
            wire("t1", "L1.out", "TON1.IN"),
            wire("t2", "TON1.Q", "L2.in"),
            wire("t3", "L1.out", "TON2.IN"),
            wire("t4", "TON2.Q", "L2.in"),
        ]
    return {
        "id": cid,
        "title": title,
        "titleAr": title_ar,
        "sourceFile": source,
        "page": page,
        "purpose": f"تتابع أسطوانتين مع تكرار {repeats}",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "ExA", "Start/Stop/A0 إلى ExA", "w1", "L1.out", "start.L"),
            step("s2", "ExB", "A1 يشغّل ExB", "w6", "L1.out", "A1.L"),
            step("s3", "العداد", "B0 يعد على CTU", "w11", "L1.out", "B0.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "A0", "label": "A0", "kind": "toggle", "default": True},
                {"id": "A1", "label": "A1", "kind": "toggle"},
                {"id": "B0", "label": "B0", "kind": "momentary"},
                {"id": "B1", "label": "B1", "kind": "toggle"},
                {"id": "reset", "label": "Reset", "kind": "momentary"},
            ],
            "outputs": [
                {"id": "ExA", "label": "ExA", "kind": "actuator"},
                {"id": "ExB", "label": "ExB", "kind": "actuator"},
                {"id": "Done", "label": "Done", "kind": "counter"},
            ],
            "tickMs": 50,
            "description": "حاكِ الحساسات يدوياً لمحاكاة التتابع وعدّ الدورات.",
        },
    }


def c_wrapping():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 800, 20, ports=[{"id": "in", "side": "left"}]),
        comp("ps", "SENSOR", "Part", 40, 280, 120, 40, signal="Part"),
        comp("Hold", "COIL", "Hold", 40, 360, 280, 40, signal="Hold"),
        comp("Paper", "COIL", "Paper", 40, 440, 440, 40, signal="Paper"),
        comp("TON1", "TON", "1s", 40, 520, 600, 40, signal="T1", preset=1000, ports=ports_lr("IN", "Q")),
        comp("Fold", "COIL", "Fold", 180, 280, 120, 180, signal="Fold"),
        comp("TON2", "TON", "0.5s", 180, 360, 280, 180, signal="T2", preset=500, ports=ports_lr("IN", "Q")),
        comp("Tape", "COIL", "Tape", 180, 440, 440, 180, signal="Tape"),
        comp("TON3", "TON", "0.75s", 180, 520, 600, 180, signal="T3", preset=750, ports=ports_lr("IN", "Q")),
    ]
    wires = [
        wire("w1", "L1.out", "ps.L"),
        wire("w2", "ps.R", "Hold.L"),
        wire("w3", "Hold.R", "L2.in"),
        wire("w4", "L1.out", "Paper.L"),
        wire("w5", "Paper.R", "L2.in"),
        wire("w6", "L1.out", "TON1.IN"),
        wire("w7", "TON1.Q", "L2.in"),
        wire("w8", "L1.out", "Fold.L"),
        wire("w9", "Fold.R", "L2.in"),
        wire("w10", "L1.out", "TON2.IN"),
        wire("w11", "TON2.Q", "L2.in"),
        wire("w12", "L1.out", "Tape.L"),
        wire("w13", "Tape.R", "L2.in"),
        wire("w14", "L1.out", "TON3.IN"),
        wire("w15", "TON3.Q", "L2.in"),
    ]
    return {
        "id": "ex-4-wrapping-process-state-based-design",
        "title": "Wrapping Process",
        "titleAr": "عملية تغليف",
        "sourceFile": "4 - State-Based Design.ppt",
        "page": "شريحة 22-23",
        "purpose": "تثبيت → ورق → طي → شريط → تحرير",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "Hold", "حساس القطعة يشغّل Hold", "w1", "L1.out", "ps.L"),
            step("s2", "التسلسل الزمني", "Paper/Fold/Tape مع مؤقتاتها كما بالملزمة", "w4", "L1.out", "Paper.L"),
        ],
        "simulation": {
            "inputs": [{"id": "Part", "label": "Part sensor", "kind": "toggle"}],
            "outputs": [
                {"id": "Hold", "label": "Hold", "kind": "actuator"},
                {"id": "Paper", "label": "Paper", "kind": "actuator"},
                {"id": "Fold", "label": "Fold", "kind": "actuator"},
                {"id": "Tape", "label": "Tape", "kind": "actuator"},
                {"id": "T1", "label": "T1", "kind": "timer"},
                {"id": "T2", "label": "T2", "kind": "timer"},
                {"id": "T3", "label": "T3", "kind": "timer"},
            ],
            "tickMs": 50,
            "description": "فعّل Part ثم راقب المخارج والمؤقتات.",
        },
    }


def c_thermostat():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 30, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 780, 30, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "start", 40, 300, 120, 40, signal="start"),
        comp("stop", "PB_NC", "stop", 40, 380, 260, 80, signal="stop"),
        comp("seal", "CONTACT_NO", "CR1", 40, 460, 120, 140, monitors="CR1"),
        comp("CR1", "COIL", "CR1", 40, 540, 420, 80, signal="CR1"),
        comp("cr1a", "CONTACT_NO", "CR1", 180, 300, 120, 230, monitors="CR1"),
        comp("cr2nc", "CONTACT_NC", "CR2", 180, 380, 280, 230, monitors="CR2"),
        comp("M", "COIL", "M", 180, 460, 440, 230, signal="M"),
        comp("G", "LAMP", "G", 180, 540, 600, 230, signal="G"),
        comp("th", "THERMOSTAT", "Thermostat", 320, 300, 120, 360, signal="thermo"),
        comp("CR2", "COIL", "CR2", 320, 380, 300, 360, signal="CR2"),
        comp("R", "LAMP", "R", 320, 460, 460, 360, signal="R"),
    ]
    wires = [
        wire("a1", "L1.out", "start.L"),
        wire("a2", "L1.out", "seal.L"),
        wire("a3", "start.R", "stop.L"),
        wire("a4", "seal.R", "stop.L"),
        wire("a5", "stop.R", "CR1.L"),
        wire("a6", "CR1.R", "L2.in"),
        wire("b1", "L1.out", "cr1a.L"),
        wire("b2", "cr1a.R", "cr2nc.L"),
        wire("b3", "cr2nc.R", "M.L"),
        wire("b4", "M.R", "G.L"),
        wire("b5", "G.R", "L2.in"),
        wire("c1", "L1.out", "th.L"),
        wire("c2", "th.R", "CR2.L"),
        wire("c3", "CR2.R", "R.L"),
        wire("c4", "R.R", "L2.in"),
    ]
    return {
        "id": "motor-control-with-thermostat-interlock-cr1cr2",
        "title": "Motor + Thermostat Interlock",
        "titleAr": "محرك مع حماية ترموستات",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 4 / Q10",
        "purpose": "إيقاف المحرك عند إشارة الترموستات",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "CR1", "Start/Stop لـ CR1", "a1", "L1.out", "start.L"),
            step("s2", "المحرك", "CR1 و !CR2 يشغّلان M و G", "b1", "L1.out", "cr1a.L"),
            step("s3", "الترموستات", "Thermostat → CR2 و R", "c1", "L1.out", "th.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "thermo", "label": "Thermostat", "kind": "toggle"},
            ],
            "outputs": [
                {"id": "CR1", "label": "CR1", "kind": "coil"},
                {"id": "CR2", "label": "CR2", "kind": "coil"},
                {"id": "M", "label": "M", "kind": "coil"},
                {"id": "G", "label": "G", "kind": "lamp"},
                {"id": "R", "label": "R", "kind": "lamp"},
            ],
            "tickMs": 50,
            "description": "الترموستات يوقف M ويضيء R.",
        },
    }


def c_tof_interlock():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 820, 20, ports=[{"id": "in", "side": "left"}]),
        comp("stop", "PB_NC", "stop", 40, 280, 100, 40, signal="stop"),
        comp("OL", "OL", "OL", 40, 360, 240, 40, signal="OL"),
        comp("FW", "PB_NO", "FW", 40, 440, 380, 40, signal="FW"),
        comp("m1s", "CONTACT_NO", "M1", 40, 520, 380, 120, monitors="M1"),
        comp("tof2nc", "CONTACT_NC", "TOF2", 40, 600, 520, 80, monitors="TOF2"),
        comp("M1", "COIL", "M1", 40, 680, 680, 80, signal="M1"),
        comp("TOF1", "TOF", "TOF1 4s", 180, 280, 680, 180, signal="TOF1", preset=4000, ports=ports_lr("IN", "Q")),
        comp("RV", "PB_NO", "RV", 320, 280, 380, 280, signal="RV"),
        comp("m2s", "CONTACT_NO", "M2", 320, 360, 380, 360, monitors="M2"),
        comp("tof1nc", "CONTACT_NC", "TOF1", 320, 440, 520, 320, monitors="TOF1"),
        comp("M2", "COIL", "M2", 320, 520, 680, 320, signal="M2"),
        comp("TOF2", "TOF", "TOF2 4s", 320, 600, 680, 420, signal="TOF2", preset=4000, ports=ports_lr("IN", "Q")),
    ]
    wires = [
        wire("s1", "L1.out", "stop.L"),
        wire("s2", "stop.R", "OL.L"),
        wire("f1", "OL.R", "FW.L"),
        wire("f2", "OL.R", "m1s.L"),
        wire("f3", "FW.R", "tof2nc.L"),
        wire("f4", "m1s.R", "tof2nc.L"),
        wire("f5", "tof2nc.R", "M1.L"),
        wire("f6", "M1.R", "L2.in"),
        wire("f7", "M1.L", "TOF1.IN"),
        wire("f8", "TOF1.Q", "L2.in"),
        wire("r1", "OL.R", "RV.L"),
        wire("r2", "OL.R", "m2s.L"),
        wire("r3", "RV.R", "tof1nc.L"),
        wire("r4", "m2s.R", "tof1nc.L"),
        wire("r5", "tof1nc.R", "M2.L"),
        wire("r6", "M2.R", "L2.in"),
        wire("r7", "M2.L", "TOF2.IN"),
        wire("r8", "TOF2.Q", "L2.in"),
    ]
    return {
        "id": "fwdrev-motor-with-tof-interlock-4-sec",
        "title": "Fwd/Rev with TOF 4s",
        "titleAr": "أمامي/خلفي مع TOF 4 ثوانٍ",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 4 / Q11",
        "purpose": "تأخير 4 ثوانٍ قبل عكس الاتجاه",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "حماية عامة", "stop و OL مشتركان", "s1", "L1.out", "stop.L"),
            step("s2", "أمامي", "FW // M1 عبر !TOF2 إلى M1 و TOF1", "f1", "OL.R", "FW.L"),
            step("s3", "خلفي", "RV // M2 عبر !TOF1 إلى M2 و TOF2", "r1", "OL.R", "RV.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "FW", "label": "FW", "kind": "momentary"},
                {"id": "RV", "label": "RV", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "M1", "label": "M1", "kind": "coil"},
                {"id": "M2", "label": "M2", "kind": "coil"},
                {"id": "TOF1", "label": "TOF1", "kind": "timer"},
                {"id": "TOF2", "label": "TOF2", "kind": "timer"},
            ],
            "tickMs": 50,
            "description": "بعد إيقاف اتجاه، انتظر 4ث قبل الاتجاه المعاكس.",
        },
    }


def c_cr_ks_kd():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 800, 20, ports=[{"id": "in", "side": "left"}]),
        comp("start", "PB_NO", "start", 40, 280, 120, 40, signal="start"),
        comp("stop", "PB_NC", "stop", 40, 360, 260, 80, signal="stop"),
        comp("seal", "CONTACT_NO", "CR", 40, 440, 120, 140, monitors="CR"),
        comp("OL", "OL", "OL", 40, 520, 400, 80, signal="OL"),
        comp("CR", "COIL", "CR", 40, 600, 560, 80, signal="CR"),
        comp("cr1", "CONTACT_NO", "CR", 180, 280, 120, 220, monitors="CR"),
        comp("C", "SENSOR", "C", 180, 360, 280, 220, signal="C"),
        comp("Ks", "COIL", "Ks", 180, 440, 440, 220, signal="Ks"),
        comp("cr2", "CONTACT_NO", "CR", 320, 280, 120, 360, monitors="CR"),
        comp("kdnc", "CONTACT_NC", "Kd", 320, 360, 280, 360, monitors="Kd"),
        comp("Kd", "COIL", "Kd", 320, 440, 440, 360, signal="Kd"),
        comp("R", "LAMP", "R", 460, 280, 600, 220, signal="R"),
        comp("G", "LAMP", "G", 460, 360, 600, 360, signal="G"),
        comp("ksG", "CONTACT_NO", "Ks", 460, 440, 440, 360, monitors="Ks"),
        comp("kdR", "CONTACT_NO", "Kd", 460, 520, 440, 220, monitors="Kd"),
    ]
    wires = [
        wire("a1", "L1.out", "start.L"),
        wire("a2", "L1.out", "seal.L"),
        wire("a3", "start.R", "stop.L"),
        wire("a4", "seal.R", "stop.L"),
        wire("a5", "stop.R", "OL.L"),
        wire("a6", "OL.R", "CR.L"),
        wire("a7", "CR.R", "L2.in"),
        wire("b1", "L1.out", "cr1.L"),
        wire("b2", "cr1.R", "C.L"),
        wire("b3", "C.R", "Ks.L"),
        wire("b4", "Ks.R", "L2.in"),
        wire("c1", "L1.out", "cr2.L"),
        wire("c2", "cr2.R", "kdnc.L"),
        wire("c3", "kdnc.R", "Kd.L"),
        wire("c4", "Kd.R", "L2.in"),
        wire("d1", "L1.out", "ksG.L"),
        wire("d2", "ksG.R", "G.L"),
        wire("d3", "G.R", "L2.in"),
        wire("d4", "L1.out", "kdR.L"),
        wire("d5", "kdR.R", "R.L"),
        wire("d6", "R.R", "L2.in"),
    ]
    return {
        "id": "cr-ks-kd-control-circuit-with-lamps",
        "title": "CR / Ks / Kd Control",
        "titleAr": "تحكم CR و Ks و Kd",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 2 / Q5",
        "purpose": "تحكم متداخل بريليهات ومؤشرات",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "CR", "Start/Stop/OL → CR", "a1", "L1.out", "start.L"),
            step("s2", "Ks/Kd", "مسارات Ks و Kd مع مؤشرات", "b1", "L1.out", "cr1.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "C", "label": "C", "kind": "toggle"},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "CR", "label": "CR", "kind": "coil"},
                {"id": "Ks", "label": "Ks", "kind": "coil"},
                {"id": "Kd", "label": "Kd", "kind": "coil"},
                {"id": "G", "label": "G", "kind": "lamp"},
                {"id": "R", "label": "R", "kind": "lamp"},
            ],
            "tickMs": 50,
            "description": "شغّل CR ثم راقب Ks/Kd حسب C.",
        },
    }


def c_motor_abx():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 820, 20, ports=[{"id": "in", "side": "left"}]),
        comp("stop", "PB_NC", "stop", 40, 280, 100, 40, signal="stop"),
        comp("start", "PB_NO", "start", 40, 360, 240, 40, signal="start"),
        comp("seal", "CONTACT_NO", "CR", 40, 440, 240, 120, monitors="CR"),
        comp("CR", "COIL", "CR", 40, 520, 400, 80, signal="CR"),
        comp("G", "LAMP", "G", 40, 600, 560, 80, signal="G"),
        comp("crG", "CONTACT_NO", "CR", 40, 680, 400, 160, monitors="CR"),
        comp("A", "SENSOR", "A", 180, 280, 100, 260, signal="A"),
        comp("X", "SENSOR", "X", 180, 360, 240, 260, signal="X"),
        comp("KrNc", "CONTACT_NC", "Kr", 180, 440, 380, 260, monitors="Kr"),
        comp("OL", "OL", "OL", 180, 520, 520, 260, signal="OL"),
        comp("Kf", "COIL", "Kf", 180, 600, 680, 260, signal="Kf"),
        comp("B", "SENSOR", "B", 320, 280, 100, 400, signal="B"),
        comp("KfNc", "CONTACT_NC", "Kf", 320, 360, 240, 400, monitors="Kf"),
        comp("Kr", "COIL", "Kr", 320, 440, 400, 400, signal="Kr"),
    ]
    wires = [
        wire("a1", "L1.out", "stop.L"),
        wire("a2", "stop.R", "start.L"),
        wire("a3", "stop.R", "seal.L"),
        wire("a4", "start.R", "CR.L"),
        wire("a5", "seal.R", "CR.L"),
        wire("a6", "CR.R", "L2.in"),
        wire("g1", "L1.out", "crG.L"),
        wire("g2", "crG.R", "G.L"),
        wire("g3", "G.R", "L2.in"),
        wire("f1", "L1.out", "A.L"),
        wire("f2", "A.R", "X.L"),
        wire("f3", "X.R", "KrNc.L"),
        wire("f4", "KrNc.R", "OL.L"),
        wire("f5", "OL.R", "Kf.L"),
        wire("f6", "Kf.R", "L2.in"),
        wire("r1", "L1.out", "B.L"),
        wire("r2", "B.R", "KfNc.L"),
        wire("r3", "KfNc.R", "Kr.L"),
        wire("r4", "Kr.R", "L2.in"),
    ]
    return {
        "id": "motor-fwdrev-with-sensors-abx-and-cr",
        "title": "Motor Fwd/Rev with A,B,X",
        "titleAr": "محرك مع حساسات A/B/X",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 3 / Q7",
        "purpose": "أمامي/خلفي مع حساسات وتعشيق",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "CR", "Start/Stop → CR و G", "a1", "L1.out", "stop.L"),
            step("s2", "Kf", "A و X و !Kr و OL → Kf", "f1", "L1.out", "A.L"),
            step("s3", "Kr", "B و !Kf → Kr", "r1", "L1.out", "B.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "A", "label": "A", "kind": "toggle"},
                {"id": "B", "label": "B", "kind": "toggle"},
                {"id": "X", "label": "X", "kind": "toggle", "default": True},
                {"id": "OL", "label": "OL", "kind": "toggle", "default": False},
            ],
            "outputs": [
                {"id": "CR", "label": "CR", "kind": "coil"},
                {"id": "Kf", "label": "Kf", "kind": "coil"},
                {"id": "Kr", "label": "Kr", "kind": "coil"},
                {"id": "G", "label": "G", "kind": "lamp"},
            ],
            "tickMs": 50,
            "description": "الحساسات تحدد اتجاه التشغيل مع التعشيق.",
        },
    }


def c_kl_kr():
    comps = [
        comp("L1", "RAIL_L", "L1", 20, 20, 30, 20, ports=[{"id": "out", "side": "right"}]),
        comp("L2", "RAIL_R", "L2", 20, 200, 800, 20, ports=[{"id": "in", "side": "left"}]),
        comp("stop", "PB_NC", "stop", 40, 280, 100, 40, signal="stop"),
        comp("start", "PB_NO", "start", 40, 360, 240, 40, signal="start"),
        comp("seal", "CONTACT_NO", "CR", 40, 440, 240, 120, monitors="CR"),
        comp("CR", "COIL", "CR", 40, 520, 400, 80, signal="CR"),
        comp("C", "SENSOR", "C", 180, 280, 100, 220, signal="C"),
        comp("A", "SENSOR", "A", 180, 360, 240, 220, signal="A"),
        comp("KrNc", "CONTACT_NC", "KR", 180, 440, 380, 220, monitors="KR"),
        comp("KL", "COIL", "KL", 180, 520, 540, 220, signal="KL"),
        comp("D", "SENSOR", "D", 320, 280, 100, 360, signal="D"),
        comp("B", "SENSOR", "B", 320, 360, 240, 360, signal="B"),
        comp("KlNc", "CONTACT_NC", "KL", 320, 440, 380, 360, monitors="KL"),
        comp("KR", "COIL", "KR", 320, 520, 540, 360, signal="KR"),
    ]
    wires = [
        wire("a1", "L1.out", "stop.L"),
        wire("a2", "stop.R", "start.L"),
        wire("a3", "stop.R", "seal.L"),
        wire("a4", "start.R", "CR.L"),
        wire("a5", "seal.R", "CR.L"),
        wire("a6", "CR.R", "L2.in"),
        wire("b1", "L1.out", "C.L"),
        wire("b2", "C.R", "A.L"),
        wire("b3", "A.R", "KrNc.L"),
        wire("b4", "KrNc.R", "KL.L"),
        wire("b5", "KL.R", "L2.in"),
        wire("c1", "L1.out", "D.L"),
        wire("c2", "D.R", "B.L"),
        wire("c3", "B.R", "KlNc.L"),
        wire("c4", "KlNc.R", "KR.L"),
        wire("c5", "KR.R", "L2.in"),
    ]
    return {
        "id": "cr-kl-kr-interlocked-actuator-control",
        "title": "CR / KL / KR Interlock",
        "titleAr": "تعشيق KL و KR",
        "sourceFile": "6 - General Questions.pdf",
        "page": "صفحة 5 / Q12",
        "purpose": "مشغلات متعاشقة مع CR",
        "components": comps,
        "referenceWires": wires,
        "steps": [
            step("s1", "CR", "Start/Stop → CR", "a1", "L1.out", "stop.L"),
            step("s2", "KL/KR", "مساران مع تعشيق متبادل", "b1", "L1.out", "C.L"),
        ],
        "simulation": {
            "inputs": [
                {"id": "start", "label": "Start", "kind": "momentary"},
                {"id": "stop", "label": "Stop", "kind": "momentary"},
                {"id": "A", "label": "A", "kind": "toggle"},
                {"id": "B", "label": "B", "kind": "toggle"},
                {"id": "C", "label": "C", "kind": "toggle", "default": True},
                {"id": "D", "label": "D", "kind": "toggle", "default": True},
            ],
            "outputs": [
                {"id": "CR", "label": "CR", "kind": "coil"},
                {"id": "KL", "label": "KL", "kind": "coil"},
                {"id": "KR", "label": "KR", "kind": "coil"},
            ],
            "tickMs": 50,
            "description": "KL و KR لا يعملان معاً.",
        },
    }


def main():
    circuits = [
        c_start_stop_latched(),
        c_latched_sr(),
        c_power_shutdown(),
        c_conditional(),
        c_sequential(),
        c_interlock(),
        c_priority(),
        c_oscillating(),
        c_flashing(),
        c_clamping_tp(),
        c_square_2hz(),
        c_conveyor_siren(),
        c_ctu_eject(),
        c_ctd_eject(),
        c_square_4hz(),
        c_soft_start(),
        c_reversing_q3(),
        c_q4_24parts(),
        toggle_light("light-control-with-one-push-button-toggle", "Light Toggle One PB", "لمبة بزر واحد", "شريحة 5-6"),
        toggle_light("one-pb-light-control-تنويع-الحالات", "One PB Light (variant)", "لمبة بزر واحد — تنويع", "شريحة 7-8"),
        c_store_light(),
        c_square_2hz() | {},  # placeholder replaced below
    ]
    # fix last mistaken append
    circuits = circuits[:-1]
    circuits += [
        {**c_square_2hz(), "id": "ex-1-square-wave-2hz-60-by-state-based-method", "title": "Square Wave State-Based", "titleAr": "موجة مربعة بطريقة الحالات", "sourceFile": "4 - State-Based Design.ppt", "page": "شريحة 13-15"},
        c_cylinders_ab("ex-2-cylinder-a-sequence-repeated-6-times", "Cylinder A x6", "أسطوانة A ×6", "شريحة 16-18", "4 - State-Based Design.ppt", 6),
        c_wrapping(),
        c_cylinders_ab("ex-1-cylinders-a-b-sequence-x4-state-design", "Cylinders A/B x4", "أسطوانتا A/B ×4", "صفحة 1", "5 - Solved Examples.pdf", 4),
        c_cylinders_ab("ex-2-cylinders-a-b-sequence-with-timers-x8", "Cylinders A/B x8 + Timers", "أسطوانتا A/B ×8 مع مؤقتات", "صفحة 3", "5 - Solved Examples.pdf", 8, True),
        c_fwd_rev_q1(),
        c_motor_starter_q3(),
        c_cr_ks_kd(),
        c_motor_abx(),
        c_thermostat(),
        c_tof_interlock(),
        c_kl_kr(),
    ]

    # Fix square wave clone id/title
    for c in circuits:
        if c["id"] == "ex-1-square-wave-2hz-60-by-state-based-method":
            c["sourceFile"] = "4 - State-Based Design.ppt"
            c["page"] = "شريحة 13-15"
            c["title"] = "Square Wave State-Based 2Hz 60%"
            c["titleAr"] = "موجة مربعة 2Hz بطريقة الحالات"

    for c in circuits:
        save(c)

    # Verify against catalog active ids
    cat = json.loads((OUT.parent / "catalog.json").read_text(encoding="utf-8"))
    active = {x["id"] for x in cat["circuits"] if not x["skipped"]}
    have = {p.stem for p in OUT.glob("*.json")}
    missing = active - have
    extra = have - active
    print("ACTIVE", len(active), "HAVE", len(have))
    print("MISSING", missing)
    print("EXTRA", extra)


if __name__ == "__main__":
    main()
