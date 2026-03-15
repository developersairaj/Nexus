"""
focus_timer.py  —  NEXUS / Focus Zone Website
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✦ After session ends → NEW SESSION button, no file restart needed
  ✦ face-api.js TinyFaceDetector — no API key, runs in browser
  ✦ OS screen blocker (tkinter fullscreen overlay)
  ✦ Server-side timer (cannot be cheated)
  ✦ Day / Night mode
  ✦ 15-second test mode
  ✦ Premium mission-control UI
  ✦ FIX: screens no longer overlap (display:none + showScr helper)

    pip install flask
    python focus_timer.py

Opens at http://localhost:5000
"""

import threading
import time
import webbrowser
import platform
import subprocess
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

state = {
    "active":    False,
    "start_ts":  0,
    "total_sec": 0,
    "done":      False,
    "resets":    0,
    "sessions":  0,
}
state_lock = threading.Lock()
_cafe_proc = None


def acquire_wake_lock():
    global _cafe_proc
    sys = platform.system()
    if sys == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000002)
        except Exception: pass
    elif sys == "Darwin":
        try: _cafe_proc = subprocess.Popen(["caffeinate", "-d"])
        except Exception: pass
    else:
        try:
            subprocess.Popen(["xset", "s", "off"])
            subprocess.Popen(["xset", "-dpms"])
        except Exception: pass


def release_wake_lock():
    global _cafe_proc
    sys = platform.system()
    if sys == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        except Exception: pass
    elif sys == "Darwin":
        if _cafe_proc:
            try: _cafe_proc.terminate()
            except Exception: pass
            _cafe_proc = None
    else:
        try:
            subprocess.Popen(["xset", "s", "on"])
            subprocess.Popen(["xset", "+dpms"])
        except Exception: pass


_blocker_root = None


def show_blocker():
    def _run():
        global _blocker_root
        try:
            import tkinter as tk
            root = tk.Tk()
            root.title("NEXUS")
            root.configure(bg="#050508")
            root.attributes("-fullscreen", True)
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            root.protocol("WM_DELETE_WINDOW", lambda: None)
            for seq in ("<Escape>", "<Alt-F4>", "<Control-w>", "<Control-q>",
                        "<Super_L>", "<Super_R>"):
                root.bind(seq, lambda e: "break")
            root.bind("<FocusOut>",
                      lambda e: root.after(100, lambda: (root.lift(), root.focus_force())))
            tk.Frame(root, bg="#00ffe0", height=2).pack(fill="x", side="top")
            tk.Label(root, text="NEXUS", bg="#050508", fg="#00ffe0",
                     font=("Courier New", 11, "bold")).place(relx=0.5, rely=0.36, anchor="center")
            tk.Label(root, text="SESSION IN PROGRESS",
                     bg="#050508", fg="#00ffe0",
                     font=("Courier New", 32, "bold")).place(relx=0.5, rely=0.44, anchor="center")
            tk.Label(root,
                     text="Return to your browser window to view the live timer.\n"
                          "This overlay disappears when your session ends.",
                     bg="#050508", fg="#1a2a28", font=("Courier New", 12),
                     justify="center").place(relx=0.5, rely=0.56, anchor="center")
            tk.Frame(root, bg="#00ffe0", height=2).pack(fill="x", side="bottom")
            _blocker_root = root
            root.mainloop()
        except Exception as e:
            print(f"[blocker] {e}")
    threading.Thread(target=_run, daemon=True).start()


def hide_blocker():
    global _blocker_root
    if _blocker_root:
        try: _blocker_root.after(0, _blocker_root.destroy)
        except Exception: pass
        _blocker_root = None


def timer_worker(total_sec, session_id):
    time.sleep(total_sec)
    with state_lock:
        if state["active"] and state["sessions"] == session_id:
            state["active"] = False
            state["done"]   = True
    release_wake_lock()
    hide_blocker()
    print(f"[timer] Session #{session_id} complete!")


@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")


@app.route("/api/start", methods=["POST"])
def api_start():
    data  = request.get_json(force=True) or {}
    mins  = float(data.get("minutes", 25))
    total = mins * 60
    with state_lock:
        if state["active"]:
            return jsonify({"ok": False, "error": "Session already running"}), 400
        state["active"]    = True
        state["done"]      = False
        state["start_ts"]  = time.time()
        state["total_sec"] = total
        state["resets"]    = 0
        state["sessions"] += 1
        sid = state["sessions"]
    acquire_wake_lock()
    show_blocker()
    threading.Thread(target=timer_worker, args=(total, sid), daemon=True).start()
    print(f"[timer] Session #{sid} started — {mins} min")
    return jsonify({"ok": True, "total_sec": total, "session_id": sid})


@app.route("/api/reset_timer", methods=["POST"])
def api_reset_timer():
    with state_lock:
        if not state["active"]:
            return jsonify({"ok": False, "error": "No active session"}), 400
        state["start_ts"]  = time.time()
        state["resets"]   += 1
        resets = state["resets"]
        total  = state["total_sec"]
    print(f"[face] No face — reset #{resets}")
    return jsonify({"ok": True, "resets": resets, "total_sec": total})


@app.route("/api/status")
def api_status():
    with state_lock:
        s = dict(state)
    if s["done"]:
        return jsonify({"status": "done", "remaining": 0,
                        "total": s["total_sec"], "resets": s["resets"], "sessions": s["sessions"]})
    if not s["active"]:
        return jsonify({"status": "idle", "remaining": 0,
                        "total": 0, "resets": s["resets"], "sessions": s["sessions"]})
    elapsed   = time.time() - s["start_ts"]
    remaining = max(0.0, s["total_sec"] - elapsed)
    return jsonify({"status": "running", "remaining": remaining,
                    "total": s["total_sec"], "resets": s["resets"], "sessions": s["sessions"]})


@app.route("/api/new_session", methods=["POST"])
def api_new_session():
    """Reset state for a new session — no Python restart needed."""
    with state_lock:
        state["active"]    = False
        state["done"]      = False
        state["start_ts"]  = 0
        state["total_sec"] = 0
        state["resets"]    = 0
    release_wake_lock()
    hide_blocker()
    print("[server] Ready for new session")
    return jsonify({"ok": True, "sessions": state["sessions"]})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    with state_lock:
        state["active"] = False
        state["done"]   = False
        state["resets"] = 0
    release_wake_lock()
    hide_blocker()
    return jsonify({"ok": True})




HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NEXUS — Focus Zone</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#050508; --bg2:#0a0a10; --surf:#0d0d18; --surf2:#111120;
  --b1:rgba(0,255,210,.1); --b2:rgba(0,255,210,.22); --b3:rgba(0,255,210,.5);
  --c:#00ffd2; --c2:#00c8a8; --cglow:rgba(0,255,210,.28); --cdim:rgba(0,255,210,.07);
  --gold:#ffd166; --gdim:rgba(255,209,102,.08); --gglow:rgba(255,209,102,.28);
  --red:#ff3d5a; --rdim:rgba(255,61,90,.08);
  --tx:#cef0eb; --tx2:#4a8880; --tx3:#1e3832;
  --font-h:'Orbitron',monospace; --font-m:'Space Mono',monospace; --font-b:'DM Sans',sans-serif;
  --ease:cubic-bezier(.4,0,.2,1);
}
.lt{
  --bg:#eef4f3; --bg2:#e2ecea; --surf:#fff; --surf2:#f5faf9;
  --b1:rgba(0,120,105,.12); --b2:rgba(0,120,105,.24); --b3:rgba(0,120,105,.55);
  --c:#007868; --c2:#005c52; --cglow:rgba(0,120,105,.2); --cdim:rgba(0,120,105,.07);
  --gold:#9a5e00; --gdim:rgba(154,94,0,.07); --gglow:rgba(154,94,0,.18);
  --red:#c0001e; --rdim:rgba(192,0,30,.07);
  --tx:#071a18; --tx2:#38736a; --tx3:#aaccca;
}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--tx);font-family:var(--font-b);user-select:none;transition:background .5s,color .4s}

/* Grid background */
.grid{position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(var(--b1) 1px,transparent 1px),linear-gradient(90deg,var(--b1) 1px,transparent 1px);
  background-size:52px 52px;
  mask-image:radial-gradient(ellipse 75% 75% at 50% 50%,black 35%,transparent 100%);
  animation:gdrift 50s linear infinite}
@keyframes gdrift{0%{background-position:0 0,0 0}100%{background-position:52px 52px,52px 52px}}
.vignette{position:fixed;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(ellipse 90% 85% at 50% 50%,transparent 55%,rgba(5,5,8,.6) 100%)}

/* HEADER */
.hdr{position:fixed;top:0;left:0;right:0;z-index:500;height:50px;
  display:flex;align-items:center;justify-content:space-between;padding:0 24px;
  background:rgba(5,5,8,.88);border-bottom:1px solid var(--b1);backdrop-filter:blur(20px);
  transition:background .5s}
.lt .hdr{background:rgba(238,244,243,.92)}
.logo{display:flex;align-items:center;gap:11px}
.ldot{width:8px;height:8px;border-radius:50%;background:var(--c);box-shadow:0 0 14px var(--c);animation:ldp 2.5s ease-in-out infinite}
@keyframes ldp{0%,100%{box-shadow:0 0 6px var(--c)}50%{box-shadow:0 0 22px var(--c)}}
.ltxt{font-family:var(--font-h);font-size:13px;letter-spacing:.22em;color:var(--c)}
.hdr-r{display:flex;align-items:center;gap:16px}
.sbadge{font-family:var(--font-m);font-size:10px;letter-spacing:.14em;color:var(--tx2)}
.sbadge b{color:var(--c);font-weight:700}
.tbtn{width:40px;height:40px;border-radius:50%;background:var(--surf2);border:1px solid var(--b2);
  display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:16px;
  transition:all .25s;box-shadow:0 0 16px var(--cglow)}
.tbtn:hover{border-color:var(--c);box-shadow:0 0 28px var(--cglow);transform:scale(1.1)}

/* ════════════════════════════════════════
   SCREENS — KEY FIX: display:none by default
   Only one screen visible at a time
   ════════════════════════════════════════ */
.scr{
  position:fixed;inset:0;z-index:10;
  display:none;              /* <-- was display:flex — this caused overlap */
  flex-direction:column;
  align-items:center;justify-content:center;gap:26px;
  opacity:0;pointer-events:none;
  transition:opacity .55s var(--ease)
}
.scr.on{
  display:flex;              /* <-- only the active screen is rendered */
  opacity:1;
  pointer-events:all
}

/* ════ SETUP ════ */
#ss{padding-top:50px;background:transparent}
.eyebrow{font-family:var(--font-m);font-size:10px;letter-spacing:.3em;color:var(--tx2);text-transform:uppercase;
  display:flex;align-items:center;gap:10px}
.ebl{width:28px;height:1px;background:var(--b2)}
.big-title{font-family:var(--font-h);font-size:clamp(44px,8.5vw,82px);line-height:.95;
  color:var(--c);letter-spacing:.08em;text-align:center;
  text-shadow:0 0 80px var(--cglow);transition:text-shadow .5s}
.lt .big-title{text-shadow:none}
.big-title small{display:block;font-size:.3em;letter-spacing:.45em;color:var(--tx2);
  font-family:var(--font-m);margin-top:10px}
.mpill{display:inline-flex;align-items:center;gap:9px;padding:8px 18px;
  border:1px solid var(--b2);background:var(--cdim);
  font-family:var(--font-m);font-size:10px;letter-spacing:.18em;color:var(--tx2);text-transform:uppercase;
  transition:all .3s}
.mpill.ok{border-color:var(--c);color:var(--c)}
.mpill.er{border-color:var(--red);color:var(--red)}
.mpdot{width:6px;height:6px;border-radius:50%;background:currentColor}
.mpill.ok .mpdot{animation:ldp 2s infinite}
.dur-sec{display:flex;flex-direction:column;align-items:center;gap:11px}
.dur-lbl{font-family:var(--font-m);font-size:9px;letter-spacing:.28em;color:var(--tx3);text-transform:uppercase}
.dur-row{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
.db{position:relative;overflow:hidden;padding:11px 20px;
  background:var(--surf2);border:1px solid var(--b1);
  font-family:var(--font-m);font-size:11px;letter-spacing:.16em;color:var(--tx2);text-transform:uppercase;
  cursor:pointer;outline:none;transition:all .2s;
  clip-path:polygon(0 0,calc(100% - 7px) 0,100% 7px,100% 100%,7px 100%,0 calc(100% - 7px))}
.db::before{content:'';position:absolute;inset:0;background:var(--cdim);opacity:0;transition:opacity .2s}
.db:hover{border-color:var(--b3);color:var(--tx)}
.db:hover::before{opacity:1}
.db.sel{border-color:var(--c);color:var(--c);background:var(--cdim);box-shadow:0 0 18px var(--cglow)}
.db.tst{border-color:var(--gold);color:var(--gold);background:var(--gdim);box-shadow:0 0 14px var(--gglow)}
.db.tst.sel{box-shadow:0 0 24px var(--gglow)}
.cust{display:flex;align-items:center;gap:12px}
.cust input{width:70px;padding:11px 8px;text-align:center;background:var(--surf2);
  border:1px solid var(--b1);color:var(--tx);font-family:var(--font-m);font-size:13px;
  letter-spacing:.1em;outline:none;transition:all .2s;
  clip-path:polygon(0 0,calc(100% - 6px) 0,100% 6px,100% 100%,6px 100%,0 calc(100% - 6px))}
.cust input:focus{border-color:var(--c);box-shadow:0 0 14px var(--cglow)}
.cust span{font-family:var(--font-m);font-size:9px;letter-spacing:.2em;color:var(--tx2);text-transform:uppercase}
.err{font-family:var(--font-m);font-size:11px;letter-spacing:.14em;color:var(--red);min-height:18px;text-align:center}
.cta{position:relative;overflow:hidden;padding:17px 58px;background:var(--c);border:none;
  font-family:var(--font-h);font-size:17px;letter-spacing:.2em;color:#050508;cursor:pointer;
  clip-path:polygon(0 0,calc(100% - 12px) 0,100% 12px,100% 100%,12px 100%,0 calc(100% - 12px));
  transition:all .22s;box-shadow:0 0 30px var(--cglow)}
.lt .cta{color:#fff}
.cta::after{content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.16),transparent);
  transform:translateX(-100%);transition:transform .5s}
.cta:hover::after{transform:translateX(100%)}
.cta:hover{box-shadow:0 0 50px var(--cglow);transform:translateY(-2px)}
.cta:active{transform:translateY(0)}
.cta:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none}

/* ════ TIMER SCREEN ════ */
#st{padding-top:50px;background:transparent}
.orbits{position:fixed;inset:0;pointer-events:none;z-index:5;display:flex;align-items:center;justify-content:center}
.orb{position:absolute;border-radius:50%;border:1px solid;animation:orb-p 5s ease-in-out infinite}
.orb:nth-child(1){width:400px;height:400px;border-color:rgba(0,255,210,.07);animation-delay:0s}
.orb:nth-child(2){width:600px;height:600px;border-color:rgba(0,255,210,.045);animation-delay:1.5s}
.orb:nth-child(3){width:800px;height:800px;border-color:rgba(0,255,210,.025);animation-delay:3s}
.orb:nth-child(4){width:1000px;height:1000px;border-color:rgba(0,255,210,.013);animation-delay:1s}
.lt .orb{border-color:rgba(0,120,105,.07)!important}
@keyframes orb-p{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.016);opacity:.5}}

.tbody{position:relative;z-index:10;display:grid;grid-template-columns:220px 1fr 250px;align-items:center;gap:48px;padding:0 32px;width:100%;max-width:1160px}

/* Stat column */
.scol{display:flex;flex-direction:column;gap:12px}
.sb{padding:14px 18px;border:1px solid var(--b1);background:var(--surf);position:relative;transition:border-color .3s}
.sb::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--c);transition:background .4s}
.sb.w::before{background:var(--gold)}
.sb.d::before{background:var(--red)}
.slb{font-family:var(--font-m);font-size:8px;letter-spacing:.24em;color:var(--tx2);text-transform:uppercase;margin-bottom:5px}
.sv{font-family:var(--font-h);font-size:20px;letter-spacing:.06em;color:var(--c);transition:color .4s}
.sv.w{color:var(--gold)} .sv.d{color:var(--red)}
.ss{font-family:var(--font-m);font-size:8px;letter-spacing:.12em;color:var(--tx3);margin-top:3px}
.abtn{margin-top:6px;padding:9px 14px;width:100%;background:transparent;
  border:1px solid rgba(255,61,90,.22);font-family:var(--font-m);font-size:9px;letter-spacing:.2em;
  color:rgba(255,61,90,.45);text-transform:uppercase;cursor:pointer;transition:all .2s}
.abtn:hover{border-color:var(--red);color:var(--red);background:var(--rdim)}

/* Clock center */
.cc{display:flex;flex-direction:column;align-items:center;gap:14px}
.stag{display:flex;align-items:center;gap:8px;font-family:var(--font-m);font-size:9px;letter-spacing:.3em;color:var(--tx2);text-transform:uppercase}
.bdot{width:6px;height:6px;border-radius:50%;background:var(--c);box-shadow:0 0 8px var(--c);animation:ldp 2s ease-in-out infinite}
.rclock{position:relative;width:286px;height:286px}
.rclock svg{position:absolute;inset:0;transform:rotate(-90deg)}
.rcbg{fill:none;stroke:var(--surf2);stroke-width:2}
.rcprog{fill:none;stroke:var(--c);stroke-width:4;stroke-linecap:round;
  transition:stroke-dashoffset .9s var(--ease),stroke .6s;filter:drop-shadow(0 0 8px var(--c))}
.rci{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px}
.rcl{font-family:var(--font-m);font-size:8px;letter-spacing:.35em;color:var(--tx3);text-transform:uppercase}
#clock{font-family:var(--font-h);font-size:clamp(50px,7.5vw,72px);letter-spacing:.04em;color:var(--c);
  text-shadow:0 0 40px var(--cglow);transition:color .6s,text-shadow .6s;line-height:1}
.css{font-family:var(--font-m);font-size:8px;letter-spacing:.2em;color:var(--tx3);margin-top:2px}
.lck{display:flex;align-items:center;gap:9px;border:1px solid rgba(255,61,90,.18);padding:8px 18px;background:rgba(255,61,90,.04)}
.lck span{font-family:var(--font-m);font-size:8px;letter-spacing:.2em;color:rgba(255,61,90,.5);text-transform:uppercase}
#wmsg{font-family:var(--font-m);font-size:9px;letter-spacing:.18em;color:var(--red);height:16px}

/* Camera column */
.camcol{display:flex;flex-direction:column;align-items:flex-start;gap:12px}
.camh{display:flex;align-items:center;justify-content:space-between;width:100%;
  font-family:var(--font-m);font-size:8px;letter-spacing:.24em;color:var(--tx2);text-transform:uppercase}
.camhdot{width:5px;height:5px;border-radius:50%;background:var(--c);box-shadow:0 0 7px var(--c);animation:ldp 2s ease-in-out infinite}
.cframe{position:relative;width:240px;height:180px;border:1px solid var(--b1);background:var(--surf);overflow:hidden;transition:border-color .3s,box-shadow .3s;
  clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px))}
.cframe.ok{border-color:var(--c);box-shadow:0 0 18px var(--cglow)}
.cframe.bad{border-color:var(--red);box-shadow:0 0 18px rgba(255,61,90,.28);animation:csh .35s ease}
.cframe.chk{border-color:var(--gold);box-shadow:0 0 18px var(--gglow)}
@keyframes csh{0%,100%{transform:translateX(0)}25%{transform:translateX(-3px)}75%{transform:translateX(3px)}}
#camVid{width:100%;height:100%;object-fit:cover;transform:scaleX(-1);display:block}
#fc{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.nc{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;background:var(--surf)}
.nc.h{display:none}
.nc p{font-family:var(--font-m);font-size:8px;letter-spacing:.17em;color:var(--tx3);text-transform:uppercase;text-align:center;padding:0 12px}
.scan{position:absolute;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--c),transparent);opacity:.4;animation:scanl 2.8s linear infinite}
.cframe.bad .scan{background:linear-gradient(90deg,transparent,var(--red),transparent)}
.cframe.chk .scan{background:linear-gradient(90deg,transparent,var(--gold),transparent)}
@keyframes scanl{0%{top:-2px}100%{top:100%}}
.cfoot{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(5,5,8,.8));
  padding:14px 10px 5px;display:flex;justify-content:space-between}
.lt .cfoot{background:linear-gradient(transparent,rgba(238,244,243,.88))}
.cfl{font-family:var(--font-m);font-size:8px;letter-spacing:.14em;color:var(--tx2);text-transform:uppercase}
#cst{color:var(--c);transition:color .3s;font-size:8px;letter-spacing:.12em;font-family:var(--font-m)}
.chkw{width:240px}
.chkh{display:flex;justify-content:space-between;margin-bottom:5px;
  font-family:var(--font-m);font-size:8px;letter-spacing:.17em;color:var(--tx2);text-transform:uppercase}
#chkcd{color:var(--c);transition:color .3s}
.chkt{width:100%;height:2px;background:var(--surf2);overflow:hidden}
#chkb{height:100%;background:var(--c);transition:width .3s linear,background .3s;position:relative;z-index:1}
.cstats{display:flex;gap:8px;width:240px}
.csb{flex:1;padding:10px 12px;border:1px solid var(--b1);background:var(--surf);display:flex;flex-direction:column;align-items:center;gap:3px}
.csn{font-family:var(--font-h);font-size:20px;color:var(--c);transition:color .4s}
.csn.w{color:var(--gold)} .csl{font-family:var(--font-m);font-size:8px;letter-spacing:.18em;color:var(--tx2);text-transform:uppercase}

/* OVERLAYS */
#eo{position:fixed;inset:0;z-index:9000;pointer-events:none;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:10px;border:1px solid transparent;opacity:0}
#eo.fl{border-color:rgba(255,61,90,.4);background:rgba(255,61,90,.04);animation:qf .85s forwards}
.eh{font-family:var(--font-h);font-size:24px;letter-spacing:.14em;color:var(--red)}
.es{font-family:var(--font-m);font-size:9px;letter-spacing:.2em;color:rgba(255,61,90,.6)}
@keyframes qf{0%{opacity:1}60%{opacity:1}100%{opacity:0}}
#ff{position:fixed;inset:0;z-index:8999;pointer-events:none;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:18px;opacity:0}
#ff.sh{animation:fwa 2s forwards}
@keyframes fwa{0%{opacity:0;background:rgba(255,61,90,0)}12%{opacity:1;background:rgba(255,61,90,.12)}65%{opacity:1;background:rgba(255,61,90,.07)}100%{opacity:0;background:rgba(255,61,90,0)}}
.ffh{font-family:var(--font-h);font-size:38px;letter-spacing:.1em;color:var(--red)}
.ffs{font-family:var(--font-m);font-size:10px;letter-spacing:.2em;color:rgba(255,61,90,.75);text-align:center}

/* ════ DONE ════ */
#sd{padding-top:50px;background:transparent;gap:0}
.done-wrap{display:flex;flex-direction:column;align-items:center;gap:24px;text-align:center}
.done-badge{font-family:var(--font-m);font-size:9px;letter-spacing:.3em;color:var(--c);text-transform:uppercase;
  display:flex;align-items:center;gap:12px;padding:7px 22px;border:1px solid var(--b2);background:var(--cdim)}
.done-badge::before,.done-badge::after{content:'';width:18px;height:1px;background:var(--c)}
.done-h{font-family:var(--font-h);font-size:clamp(42px,7.5vw,90px);letter-spacing:.08em;line-height:.9;
  color:var(--c);text-shadow:0 0 80px var(--cglow);animation:dglow 2s ease-in-out infinite}
.lt .done-h{text-shadow:none;animation:none}
@keyframes dglow{0%,100%{text-shadow:0 0 60px var(--cglow)}50%{text-shadow:0 0 120px var(--cglow),0 0 200px rgba(0,255,210,.1)}}
.done-sub{font-family:var(--font-m);font-size:10px;letter-spacing:.3em;color:var(--tx2);text-transform:uppercase}
.dstats{display:flex;gap:14px}
.ds{padding:14px 26px;border:1px solid var(--b2);background:var(--surf);display:flex;flex-direction:column;align-items:center;gap:5px;
  clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px))}
.dsn{font-family:var(--font-h);font-size:30px;color:var(--c);line-height:1}
.dsl{font-family:var(--font-m);font-size:8px;letter-spacing:.2em;color:var(--tx2);text-transform:uppercase}
.done-acts{display:flex;gap:12px;margin-top:4px}
.nbtn{position:relative;overflow:hidden;padding:15px 42px;background:var(--c);border:none;
  font-family:var(--font-h);font-size:16px;letter-spacing:.2em;color:#050508;cursor:pointer;
  clip-path:polygon(0 0,calc(100% - 11px) 0,100% 11px,100% 100%,11px 100%,0 calc(100% - 11px));
  transition:all .22s;box-shadow:0 0 28px var(--cglow)}
.lt .nbtn{color:#fff}
.nbtn::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.15),transparent);transform:translateX(-100%);transition:transform .5s}
.nbtn:hover::after{transform:translateX(100%)}
.nbtn:hover{box-shadow:0 0 48px var(--cglow);transform:translateY(-2px)}
.nbtn:active{transform:translateY(0)}
.rbtn{padding:15px 30px;background:transparent;border:1px solid var(--b2);
  font-family:var(--font-m);font-size:10px;letter-spacing:.17em;color:var(--tx2);text-transform:uppercase;cursor:pointer;
  clip-path:polygon(0 0,calc(100% - 8px) 0,100% 8px,100% 100%,8px 100%,0 calc(100% - 8px));transition:all .2s}
.rbtn:hover{border-color:var(--b3);color:var(--tx)}
.rw{width:320px}
.rt{width:100%;height:2px;background:var(--surf2);overflow:hidden}
#rf{height:100%;width:0%;background:var(--c);transition:width linear}
#rtxt{font-family:var(--font-m);font-size:9px;letter-spacing:.18em;color:var(--tx3);text-transform:uppercase;margin-top:7px}

@media(max-width:960px){.tbody{grid-template-columns:1fr;gap:24px}.scol,.camcol{display:none}}
@media(max-width:640px){.big-title{font-size:36px}.cta{padding:14px 38px;font-size:15px}}
</style>
</head>
<body>

<div class="grid"></div>
<div class="vignette"></div>

<header class="hdr">
  <div class="logo">
    <div class="ldot"></div>
    <div class="ltxt">NEXUS</div>
  </div>
  <div class="hdr-r">
    <div class="sbadge">Sessions: <b id="hs">0</b></div>
    <div class="tbtn" id="tbtn">🌙</div>
  </div>
</header>

<!-- SETUP -->
<div class="scr on" id="ss">
  <div class="eyebrow"><div class="ebl"></div>Deep Work Protocol<div class="ebl"></div></div>
  <h1 class="big-title">NEXUS<small>Focus Zone Website</small></h1>
  <div class="mpill" id="mp"><div class="mpdot"></div><span id="mt">Loading face detection model…</span></div>
  <div class="dur-sec">
    <div class="dur-lbl">Select Duration</div>
    <div class="dur-row" id="dr">
      <button class="db tst sel" data-m="0.25">⚡ 15s TEST</button>
      <button class="db" data-m="15">15 MIN</button>
      <button class="db" data-m="25">25 MIN</button>
      <button class="db" data-m="45">45 MIN</button>
      <button class="db" data-m="60">60 MIN</button>
      <button class="db" data-m="90">90 MIN</button>
    </div>
  </div>
  <div class="cust">
    <input type="number" id="ci" placeholder="–" min="1" max="480">
    <span>min custom</span>
  </div>
  <div class="err" id="em"></div>
  <button class="cta" id="sb">INITIATE SESSION</button>
</div>

<!-- TIMER -->
<div class="scr" id="st">
  <div class="orbits"><div class="orb"></div><div class="orb"></div><div class="orb"></div><div class="orb"></div></div>
  <div class="tbody">

    <div class="scol">
      <div class="sb" id="el-blk">
        <div class="slb">Time Elapsed</div>
        <div class="sv" id="el">00:00</div>
        <div class="ss">of total session</div>
      </div>
      <div class="sb" id="rs-blk">
        <div class="slb">Focus Breaks</div>
        <div class="sv" id="rsv">0</div>
        <div class="ss">timer resets (face loss)</div>
      </div>
      <div class="sb" id="sc-blk">
        <div class="slb">Focus Score</div>
        <div class="sv" id="scv">100%</div>
        <div class="ss">based on detection checks</div>
      </div>
      <button class="abtn" onclick="abort()">■ ABORT SESSION</button>
    </div>

    <div class="cc">
      <div class="stag"><div class="bdot"></div><span id="stxt">LOCK PROTOCOL ACTIVE</span></div>
      <div class="rclock">
        <svg viewBox="0 0 286 286" width="286" height="286">
          <circle class="rcbg" cx="143" cy="143" r="130"/>
          <g id="tks"></g>
          <circle class="rcprog" id="rp" cx="143" cy="143" r="130" stroke-dasharray="816.81" stroke-dashoffset="0"/>
        </svg>
        <div class="rci">
          <div class="rcl">REMAINING</div>
          <div id="clock">00:00</div>
          <div class="css" id="cssl"></div>
        </div>
      </div>
      <div class="lck"><span>🔒</span><span>Session locked — exits blocked</span></div>
      <div id="wmsg"></div>
    </div>

    <div class="camcol">
      <div class="camh"><span>Face Monitor</span><div class="camhdot"></div></div>
      <div class="cframe" id="cf">
        <video id="camVid" autoplay muted playsinline></video>
        <canvas id="fc"></canvas>
        <div class="nc" id="nc"><p>📷 CAMERA ACCESS</p><p>Required for focus detection</p></div>
        <div class="scan"></div>
        <div class="cfoot"><span class="cfl">FOCUS CAM</span><span id="cst">INIT</span></div>
      </div>
      <div class="chkw">
        <div class="chkh"><span>Next check</span><span id="chkcd">15s</span></div>
        <div class="chkt"><div id="chkb" style="width:100%"></div></div>
      </div>
      <div class="cstats">
        <div class="csb"><div class="csn" id="cr">0</div><div class="csl">Resets</div></div>
        <div class="csb"><div class="csn" id="cc2">–</div><div class="csl">Confidence</div></div>
      </div>
    </div>

  </div>
</div>

<div id="eo"><div class="eh">SESSION LOCKED</div><div class="es">Complete your session to unlock</div></div>
<div id="ff"><div class="ffh">⚠ FACE NOT DETECTED</div><div class="ffs">Stay at your desk!<br>Timer has been reset.</div></div>

<!-- DONE -->
<div class="scr" id="sd">
  <div class="done-wrap">
    <div class="done-badge">Mission Complete</div>
    <div class="done-h">SESSION<br>COMPLETE</div>
    <div class="done-sub">Outstanding discipline. Your focus paid off.</div>
    <div class="dstats">
      <div class="ds"><div class="dsn" id="dd">–</div><div class="dsl">Duration</div></div>
      <div class="ds"><div class="dsn" id="db2">0</div><div class="dsl">Focus Breaks</div></div>
      <div class="ds"><div class="dsn" id="dsc">–</div><div class="dsl">Focus Score</div></div>
    </div>
    <div class="done-acts">
      <button class="nbtn" onclick="newSess()">↺ &nbsp;NEW SESSION</button>
      <button class="rbtn" id="rbtn">OPEN REWARDS →</button>
    </div>
    <div class="rw">
      <div class="rt"><div id="rf"></div></div>
      <div id="rtxt">Auto-redirect in 10s — or click NEW SESSION</div>
    </div>
  </div>
</div>

<script>
const CIRC=816.81, CHECK=15;
const MODEL='https://unpkg.com/face-api.js@0.22.2/weights';
let selM=0.25,totS=0,active=false,pInt=null,wl=null,esc=0,resets=0,chkT=0,chkPass=0,rdCd=null,day=false;
let cam=null,mloaded=false,chkTimer=CHECK,chkInt=null;
const G=id=>document.getElementById(id);

// ── FIX: single screen switcher — hides all, shows only the requested one ──
function showScr(id){
  ['ss','st','sd'].forEach(s=>{G(s).classList.remove('on');});
  // tiny delay lets the browser repaint before fading in
  setTimeout(()=>G(id).classList.add('on'),20);
}

// Build SVG ticks
(()=>{const g=G('tks');for(let i=0;i<60;i++){const a=i*6*Math.PI/180,mj=i%5===0,r1=mj?120:124;
const x1=143+r1*Math.cos(a),y1=143+r1*Math.sin(a),x2=143+130*Math.cos(a),y2=143+130*Math.sin(a);
const l=document.createElementNS('http://www.w3.org/2000/svg','line');
l.setAttribute('x1',x1);l.setAttribute('y1',y1);l.setAttribute('x2',x2);l.setAttribute('y2',y2);
l.setAttribute('stroke',mj?'rgba(0,255,210,.38)':'rgba(0,255,210,.13)');
l.setAttribute('stroke-width',mj?'2':'1');g.appendChild(l);}})();

// Theme
G('tbtn').addEventListener('click',()=>{day=!day;document.body.classList.toggle('lt',day);G('tbtn').textContent=day?'🌙':'☀️';});

// Duration buttons
G('dr').addEventListener('click',e=>{const b=e.target.closest('.db');if(!b)return;
document.querySelectorAll('.db').forEach(x=>x.classList.remove('sel'));b.classList.add('sel');
selM=parseFloat(b.dataset.m);G('ci').value='';});
G('ci').addEventListener('input',e=>{const v=parseFloat(e.target.value);
if(v>0){document.querySelectorAll('.db').forEach(x=>x.classList.remove('sel'));selM=v;}});

// Load models
async function loadM(){
  try{
    G('mt').textContent='Downloading TinyFaceDetector weights…';
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL);
    mloaded=true;
    G('mp').classList.add('ok');
    G('mt').textContent='✓ Face detection ready — no API key required';
  } catch(e){
    console.warn('[face-api] Model load failed:',e);
    G('mp').classList.add('er');
    G('mt').textContent='⚠ Detection unavailable — session runs without face check';
    mloaded=false;
  }
}

// Camera
async function initCam(){
  try{cam=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});
    G('camVid').srcObject=cam;await new Promise(r=>{G('camVid').onloadedmetadata=r;});
    G('nc').classList.add('h');G('cf').className='cframe ok';G('cst').textContent='LIVE';resizeCv();}
  catch(e){G('cst').textContent='DENIED';G('nc').querySelector('p:last-child').textContent='⚠ Permission denied';}}
function resizeCv(){const cv=G('fc'),f=G('cf');cv.width=f.offsetWidth;cv.height=f.offsetHeight;}
window.addEventListener('resize',resizeCv);
function stopCam(){if(cam){cam.getTracks().forEach(t=>t.stop());cam=null;}}

// Detection
async function detect(){
  const cv=G('fc'),ctx=cv.getContext('2d');ctx.clearRect(0,0,cv.width,cv.height);
  if(!mloaded||!cam){
    G('cf').className='cframe ok';G('cst').textContent='SKIP';
    return{f:true};
  }
  G('cf').className='cframe chk';G('cst').textContent='SCANNING…';chkT++;
  try{
    const opts=new faceapi.TinyFaceDetectorOptions({inputSize:224,scoreThreshold:0.45});
    const d=await faceapi.detectAllFaces(G('camVid'),opts);
    if(d.length>0){
      chkPass++;
      const sx=cv.width/G('camVid').videoWidth,sy=cv.height/G('camVid').videoHeight;
      const col=getComputedStyle(document.documentElement).getPropertyValue('--c').trim()||'#00ffd2';
      d.forEach(det=>{
        const{x,y,width:w,height:h}=det.box;
        const mx=cv.width-(x+w)*sx,my=y*sy,mw=w*sx,mh=h*sy;
        const pct=Math.round(det.score*100);
        ctx.strokeStyle=col;ctx.lineWidth=2;ctx.setLineDash([4,3]);ctx.strokeRect(mx,my,mw,mh);ctx.setLineDash([]);
        const cs=10;ctx.lineWidth=3;ctx.strokeStyle=col;
        ctx.beginPath();ctx.moveTo(mx,my+cs);ctx.lineTo(mx,my);ctx.lineTo(mx+cs,my);ctx.stroke();
        ctx.beginPath();ctx.moveTo(mx+mw-cs,my);ctx.lineTo(mx+mw,my);ctx.lineTo(mx+mw,my+cs);ctx.stroke();
        ctx.beginPath();ctx.moveTo(mx,my+mh-cs);ctx.lineTo(mx,my+mh);ctx.lineTo(mx+cs,my+mh);ctx.stroke();
        ctx.beginPath();ctx.moveTo(mx+mw-cs,my+mh);ctx.lineTo(mx+mw,my+mh);ctx.lineTo(mx+mw,my+mh-cs);ctx.stroke();
        ctx.fillStyle='rgba(0,255,210,.18)';ctx.fillRect(mx,my-18,68,18);
        ctx.fillStyle=col;ctx.font='bold 9px "Space Mono",monospace';ctx.fillText(`FACE ${pct}%`,mx+4,my-5);
      });
      const b=Math.round(d[0].score*100);
      G('cf').className='cframe ok';G('cst').textContent=`✓ ${b}%`;G('cc2').textContent=`${b}%`;G('cc2').style.color='';
      updScore();return{f:true,s:b};
    }else{
      G('cf').className='cframe bad';G('cst').textContent='✗ LOST';G('cc2').textContent='0%';G('cc2').style.color='var(--red)';
      updScore();return{f:false,s:0};}
  }catch(e){G('cf').className='cframe ok';G('cst').textContent='ERR';return{f:true};}}

function updScore(){
  const s=chkT===0?100:Math.round((chkPass/chkT)*100);G('scv').textContent=s+'%';
  if(s<60){G('scv').className='sv d';G('sc-blk').className='sb d';}
  else if(s<85){G('scv').className='sv w';G('sc-blk').className='sb w';}
  else{G('scv').className='sv';G('sc-blk').className='sb';}}

// Check loop
function startLoop(){chkTimer=CHECK;updBar();
  chkInt=setInterval(async()=>{if(!active)return;chkTimer--;updBar();
    if(chkTimer<=0){chkTimer=CHECK;const{f}=await detect();if(!f)await doReset();}},1000);}
function stopLoop(){if(chkInt){clearInterval(chkInt);chkInt=null;}chkTimer=CHECK;updBar();}
function updBar(){const p=(chkTimer/CHECK)*100,bar=G('chkb');
  bar.style.width=p+'%';bar.style.background=chkTimer<=4?'var(--gold)':'var(--c)';
  G('chkcd').textContent=chkTimer+'s';G('chkcd').style.color=chkTimer<=4?'var(--gold)':'var(--c)';}

// Reset
async function doReset(){
  G('ff').classList.remove('sh');void G('ff').offsetWidth;G('ff').classList.add('sh');
  setTimeout(()=>G('ff').classList.remove('sh'),2100);
  if(navigator.vibrate)navigator.vibrate([200,100,200]);
  try{const r=await(await fetch('/api/reset_timer',{method:'POST'})).json();
    if(r.ok){resets=r.resets;totS=r.total_sec;G('rsv').textContent=resets;G('cr').textContent=resets;
      if(resets>0){G('rsv').className='sv w';G('rs-blk').className='sb w';}
      G('stxt').textContent=`⚠ RESET ×${resets} — FACE LOST`;
      setTimeout(()=>{if(active)G('stxt').textContent='LOCK PROTOCOL ACTIVE';},3500);}}catch(e){}}

// Wake lock
async function getWL(){if('wakeLock'in navigator)try{wl=await navigator.wakeLock.request('screen');}catch(e){}}
document.addEventListener('visibilitychange',()=>{if(active&&document.visibilityState==='visible')getWL();});

// Start
G('sb').addEventListener('click',async()=>{
  const cv=parseFloat(G('ci').value);if(cv>0)selM=cv;
  if(!selM||selM<=0){G('em').textContent='Select a duration first.';return;}
  G('em').textContent='Initialising…';G('sb').disabled=true;
  try{
    const d=await(await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({minutes:selM})})).json();
    if(!d.ok){G('em').textContent=d.error||'Server error.';G('sb').disabled=false;return;}
    totS=d.total_sec;active=true;esc=0;resets=0;chkT=0;chkPass=0;
    G('em').textContent='';G('cssl').textContent=selM<1?`${Math.round(selM*60)}-second test`:`${selM}-minute session`;
    G('rsv').textContent='0';G('cr').textContent='0';G('scv').textContent='100%';G('sc-blk').className='sb';
    G('cc2').textContent='–';G('cc2').style.color='';G('wmsg').textContent='';G('stxt').textContent='LOCK PROTOCOL ACTIVE';
    showScr('st');  // ← replaces the old remove/add combo
    await initCam();try{await document.documentElement.requestFullscreen();}catch(e){}
    await getWL();history.pushState(null,'',location.href);
    pInt=setInterval(poll,1000);startLoop();
  }catch(e){G('em').textContent='Cannot reach server. Is focus_timer.py running?';G('sb').disabled=false;}});

async function abort(){if(!confirm('Abort this session?'))return;
  try{await fetch('/api/stop',{method:'POST'});}catch(e){}endSess(false);}

// Poll
async function poll(){
  try{const d=await(await fetch('/api/status')).json();
    G('hs').textContent=d.sessions||0;
    if(d.status==='done'){clearInterval(pInt);pInt=null;endSess(true,d);return;}
    if(d.status==='running'){totS=d.total;renderClock(d.remaining);renderProg(d.remaining,d.total);
      G('el').textContent=fmt(d.total-d.remaining);
      if(d.resets!==undefined){resets=d.resets;G('rsv').textContent=resets;G('cr').textContent=resets;}
      document.title=`🔒 ${fmt(d.remaining)} — NEXUS`;}}catch(e){}}

// End session
function endSess(ok,data){
  stopLoop();active=false;
  if(wl){try{wl.release();}catch(e){}wl=null;}
  if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});
  stopCam();
  const cv=G('fc');cv.getContext('2d').clearRect(0,0,cv.width,cv.height);
  if(ok){
    document.title='✅ NEXUS — Complete!';
    showDone(data);  // ← showScr('sd') is called inside showDone
  } else {
    document.title='NEXUS';
    setTimeout(()=>{G('sb').disabled=false;showScr('ss');},300);  // ← clean swap
  }
}

function showDone(data){
  const dur=data?.total||totS,m=Math.floor(dur/60),s=Math.round(dur%60);
  const score=chkT===0?100:Math.round((chkPass/chkT)*100);
  G('dd').textContent=m>0?`${m}m ${s}s`:`${s}s`;G('db2').textContent=resets;G('dsc').textContent=score+'%';
  try{const ac=new(window.AudioContext||window.webkitAudioContext)();
    [660,880,1100,1320].forEach((f,i)=>{const o=ac.createOscillator(),g=ac.createGain();
      o.connect(g);g.connect(ac.destination);o.frequency.value=f;o.type='sine';
      g.gain.setValueAtTime(.22,ac.currentTime+i*.18);g.gain.exponentialRampToValueAtTime(.001,ac.currentTime+i*.18+.4);
      o.start(ac.currentTime+i*.18);o.stop(ac.currentTime+i*.18+.5);});}catch(e){}
  setTimeout(()=>showScr('sd'),300);  // ← clean swap
  let n=10;G('rf').style.transition='width 10s linear';setTimeout(()=>G('rf').style.width='100%',50);
  G('rtxt').textContent=`Auto-redirect in ${n}s — or click NEW SESSION`;
  rdCd=setInterval(()=>{n--;
    if(n<=0){clearInterval(rdCd);rdCd=null;location.href='http://127.0.0.1:5500/coupon_system/frontend/index.html';}
    else G('rtxt').textContent=`Auto-redirect in ${n}s — or click NEW SESSION`;},1000);
  G('rbtn').onclick=()=>{if(rdCd){clearInterval(rdCd);rdCd=null;}location.href='http://127.0.0.1:5500/coupon_system/frontend/index.html';};}

// NEW SESSION — no restart needed
async function newSess(){
  if(rdCd){clearInterval(rdCd);rdCd=null;}
  try{await fetch('/api/new_session',{method:'POST'});}catch(e){}
  resets=0;chkT=0;chkPass=0;esc=0;totS=0;active=false;
  G('stxt').textContent='LOCK PROTOCOL ACTIVE';G('el').textContent='00:00';
  G('rsv').textContent='0';G('scv').textContent='100%';G('sc-blk').className='sb';
  G('wmsg').textContent='';G('cr').textContent='0';G('cc2').textContent='–';G('cc2').style.color='';
  G('cf').className='cframe';G('nc').classList.remove('h');
  G('fc').getContext('2d').clearRect(0,0,G('fc').width,G('fc').height);
  G('clock').textContent='00:00';G('clock').style.color='';G('clock').style.textShadow='';
  G('rp').style.strokeDashoffset='0';G('rp').style.stroke='var(--c)';G('rf').style.width='0%';G('rf').style.transition='none';
  document.querySelectorAll('.db').forEach(b=>b.classList.remove('sel'));
  document.querySelector('[data-m="0.25"]').classList.add('sel');selM=0.25;G('ci').value='';
  try{const st=await(await fetch('/api/status')).json();G('hs').textContent=st.sessions||0;}catch(e){}
  setTimeout(()=>{G('sb').disabled=false;showScr('ss');},300);  // ← clean swap
}

const fmt=s=>`${String(Math.floor(s/60)).padStart(2,'0')}:${String(Math.floor(s%60)).padStart(2,'0')}`;
function renderClock(r){G('clock').textContent=fmt(r);const f=r/totS;
  G('clock').style.color=f<=.2?'var(--red)':f<=.5?'var(--gold)':'var(--c)';
  G('clock').style.textShadow=f<=.2?'0 0 40px rgba(255,61,90,.55)':f<=.5?'0 0 40px rgba(255,209,102,.5)':'0 0 40px var(--cglow)';}
function renderProg(r,t){const f=r/t;G('rp').style.strokeDashoffset=CIRC*(1-f);
  G('rp').style.stroke=f<=.2?'var(--red)':f<=.5?'var(--gold)':'var(--c)';
  G('rp').style.filter=f<=.2?'drop-shadow(0 0 8px rgba(255,61,90,.7))':f<=.5?'drop-shadow(0 0 8px rgba(255,209,102,.65))':'drop-shadow(0 0 8px var(--c))';}

function flashE(){if(!active)return;esc++;G('wmsg').textContent=`⚠ BLOCKED — ${esc} attempt${esc>1?'s':''}`;
  const o=G('eo');o.classList.remove('fl');void o.offsetWidth;o.classList.add('fl');setTimeout(()=>o.classList.remove('fl'),880);}
document.addEventListener('keydown',e=>{if(!active)return;
  if(['Escape','F5','F11'].includes(e.key)||(e.altKey&&e.key==='F4')||(e.ctrlKey&&'wWrRtTqQ'.includes(e.key))||(e.metaKey&&'wWrRqQ'.includes(e.key))||(e.altKey&&e.key==='ArrowLeft'))
    {e.preventDefault();e.stopPropagation();flashE();}},true);
window.addEventListener('popstate',()=>{if(active){history.pushState(null,'',location.href);flashE();}});
window.addEventListener('beforeunload',e=>{if(active){e.preventDefault();e.returnValue='Focus session running!';}});
document.addEventListener('contextmenu',e=>{if(active)e.preventDefault();});
document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&active){flashE();setTimeout(()=>document.documentElement.requestFullscreen().catch(()=>{}),500);}});

(async()=>{
  loadM();
  try{const d=await(await fetch('/api/status')).json();G('hs').textContent=d.sessions||0;
    if(d.status==='running'){totS=d.total;active=true;resets=d.resets||0;
      G('cssl').textContent=`${Math.round(d.total/60)}-minute session`;G('cr').textContent=resets;G('rsv').textContent=resets;
      renderClock(d.remaining);renderProg(d.remaining,d.total);
      showScr('st');  // ← clean swap
      await initCam();await getWL();pInt=setInterval(poll,1000);startLoop();}
    else if(d.status==='done'){showDone(d);setTimeout(()=>showScr('sd'),300);}}  // ← clean swap
  catch(e){}})();
</script>
</body>
</html>"""


if __name__ == "__main__":
    def _open():
        import time as _t
        _t.sleep(1.3)
        webbrowser.open("http://localhost:5000")

    threading.Thread(target=_open, daemon=True).start()
    print("\n" + "═" * 58)
    print("  NEXUS — Focus Zone  →  http://localhost:5000")
    print("  face-api.js — no API key required")
    print("  Click 'NEW SESSION' after done — no restart needed")
    print("═" * 58 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)