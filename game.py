#!/usr/bin/env python3
"""
🌊 River Crossing Puzzle — Lion · Goat · Grass
────────────────────────────────────────────────
A classic puzzle with a modern tkinter GUI.
No external dependencies — runs with standard Python 3.

✨ RULE UPDATE (Lion priority)
• When the supervisor leaves lion, goat AND grass together on a bank,
  only the lion eats the goat. The grass survives because:
    - The lion is faster/stronger.
    - The grass is placed in the middle with equal distance to both animals.
    - So the lion reaches and eats the goat before the goat can reach the grass.
• Other rules remain the same:
    - Lion + Goat alone (no supervisor, no grass) → Lion eats Goat.
    - Goat + Grass alone (no supervisor) → Goat eats Grass.
"""

import tkinter as tk
from tkinter import ttk
import math, time

# ══════════════════════════════════════════════
#  PALETTE (cool nature vibe)
# ══════════════════════════════════════════════
BG                = "#0b1a2f"
BANK_TOP          = "#1e4d2b"
BANK_BOT          = "#0c2e15"
RIVER_DEEP        = "#0a2e5c"
RIVER_SHALLOW     = "#1565c0"
WAVE_CLR          = "#7ec8e3"
BOAT_HULL         = "#915f3d"
BOAT_RIM          = "#5e381a"
BOAT_OAR          = "#d4a373"
TEXT_GOLD         = "#f4d03f"
TEXT_TEAL         = "#b2dfdb"
TEXT_WHITE        = "#f8f9fa"
OK_GREEN          = "#a7e0b3"
ERR_RED           = "#ff8fa3"
BTN_GO_ALONE      = "#e76f51"
BTN_TAKE          = "#2a9d8f"
BTN_RESET         = "#7b2d8b"
LOSE_OVERLAY      = "#331111"
WIN_OVERLAY       = "#0a3829"
MODAL_BTN         = "#ffb703"
CHAR_COLORS = {
    "supervisor": "#ffd166",
    "lion":       "#ff6b35",
    "goat":       "#95e1d3",
    "grass":      "#52b788",
}
EMOJIS = {
    "supervisor": "👨",
    "lion":       "🦁",
    "goat":       "🐐",
    "grass":      "🌿",
}
ALL_ITEMS = ["supervisor", "lion", "goat", "grass"]
CARGO      = ["lion", "goat", "grass"]

W, H = 900, 440   # canvas dimensions

# ══════════════════════════════════════════════
#  GAME LOGIC
# ══════════════════════════════════════════════
def check_safety(left, right):
    """
    Return (is_safe, message).
    Check each bank for dangerous combinations when the supervisor is absent.
    
    🧠 NEW RULE (lion priority):
    Because the lion is faster/stronger and the grass is placed between them,
    if all three (lion, goat, grass) are together without the supervisor,
    the lion eats the goat first, and the goat never gets a chance to eat the grass.
    The function checks "lion + goat" first, so it will report that loss
    and never check "goat + grass". This correctly implements the new behaviour.
    """
    for bank_side, bank_set in [("left", left), ("right", right)]:
        # Priority 1: Lion eats goat (all three present? still lion wins)
        if "lion" in bank_set and "goat" in bank_set and "supervisor" not in bank_set:
            return False, f"🦁 Simba atamla mbuzi bila msimamizi upande wa {bank_side}!"
        # Only checked if no lion+goat danger
        if "goat" in bank_set and "grass" in bank_set and "supervisor" not in bank_set:
            return False, f"🐐 Mbuzi atakula nyasi bila msimamizi upande wa {bank_side}!"
    return True, ""

# ══════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════
class RiverGame(tk.Tk):
    ANIM_STEPS = 30   # frames per crossing animation

    def __init__(self):
        super().__init__()
        self.title("🌊  Mchezo wa Kuvuka Mto  |  River Crossing Puzzle")
        self.resizable(False, False)
        self.configure(bg=BG)

        # ttk modern theme
        style = ttk.Style(self)
        style.theme_use("clam")
        # Configure ttk button styles
        style.configure("Go.TButton", background=BTN_GO_ALONE, foreground="white",
                        font=("Helvetica", 11, "bold"), borderwidth=0, relief="flat",
                        padding=10)
        style.map("Go.TButton", background=[("active", "#f85a40")])
        style.configure("Take.TButton", background=BTN_TAKE, foreground="white",
                        font=("Helvetica", 11, "bold"), relief="flat", padding=10)
        style.map("Take.TButton", background=[("active", "#259082")])
        style.configure("Reset.TButton", background=BTN_RESET, foreground="white",
                        font=("Helvetica", 11, "bold"), relief="flat", padding=10)
        style.map("Reset.TButton", background=[("active", "#9b4dca")])
        style.configure("TCombobox", fieldbackground="#16213e", foreground="white",
                        arrowcolor="white", background="#16213e")

        self._init_state()
        self._build_ui()
        self._render()

    # ──────────────────────────────────────────
    #  STATE
    # ──────────────────────────────────────────
    def _init_state(self):
        """Initial puzzle state: everything on the left bank."""
        self.left      = {"supervisor", "lion", "goat", "grass"}
        self.right     = set()
        self.moves     = 0
        self.boat_x    = 290.0   # boat starts on the left side (pixels)
        self.boat_dest = 290.0   # destination during animation
        self.animating = False
        self.anim_payload = None
        self.game_over = False
        self.loss_message = ""

    # ──────────────────────────────────────────
    #  UI BUILD
    # ──────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(10, 0))

        tk.Label(hdr,
                 text="🌊  River Crossing Puzzle",
                 font=("Helvetica", 20, "bold"),
                 bg=BG, fg=TEXT_GOLD).pack(side="left")

        self.moves_lbl = tk.Label(hdr,
                 text="Moves: 0",
                 font=("Helvetica", 13, "bold"),
                 bg=BG, fg=TEXT_TEAL)
        self.moves_lbl.pack(side="right", padx=6)

        # ── Canvas ──
        self.cv = tk.Canvas(self, width=W, height=H,
                            bg=BG, highlightthickness=0)
        self.cv.pack(padx=20, pady=6)
        # Bind click on canvas (used by modal buttons)
        self.cv.bind("<Button-1>", self._canvas_click)

        # ── Status bar ──
        self.status_var = tk.StringVar(
            value="🎯 Vushia kila kitu upande wa kulia!  /  Get everyone to the RIGHT bank!")
        self.status_lbl = tk.Label(self,
                 textvariable=self.status_var,
                 font=("Helvetica", 11),
                 bg=BG, fg=OK_GREEN,
                 wraplength=860, justify="center")
        self.status_lbl.pack(pady=(0, 4))

        # ── Controls ──
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=8)

        # Go alone button
        ttk.Button(ctrl, text="🚣  Go Alone", style="Go.TButton",
                   command=self._go_alone).grid(row=0, column=0, padx=10)

        # Separator
        tk.Frame(ctrl, width=2, bg="#334455").grid(
            row=0, column=1, padx=6, pady=4, sticky="ns")

        # Take section
        take_f = tk.Frame(ctrl, bg=BG)
        take_f.grid(row=0, column=2, padx=10)

        tk.Label(take_f, text="Chagua / Take:",
                 font=("Helvetica", 11), bg=BG, fg=TEXT_WHITE
                 ).pack(side="left", padx=(0, 6))

        self.take_var = tk.StringVar(value="goat")
        self.take_menu = ttk.Combobox(take_f, textvariable=self.take_var,
                                      state="readonly",
                                      font=("Helvetica", 11),
                                      width=12)
        self.take_menu.pack(side="left")
        self.take_menu.bind("<<ComboboxSelected>>", lambda e: None)  # keep selection

        ttk.Button(take_f, text="Take  ➜", style="Take.TButton",
                   command=self._take_item).pack(side="left", padx=(8, 0))

        # Separator
        tk.Frame(ctrl, width=2, bg="#334455").grid(
            row=0, column=3, padx=6, pady=4, sticky="ns")

        # Reset button
        ttk.Button(ctrl, text="🔄  Reset", style="Reset.TButton",
                   command=self._reset).grid(row=0, column=4, padx=10)

        # ── Rules hint (collapsible) ──
        self.rules_visible = False
        self.rules_btn = tk.Button(self, text="ℹ️  Show Rules",
                                   command=self._toggle_rules,
                                   font=("Helvetica", 9), bg=BG, fg=TEXT_TEAL,
                                   relief="flat", cursor="hand2", bd=0)
        self.rules_btn.pack()
        self.rules_lbl = tk.Label(self, text=(
            "• Simba (🦁) akiachwa na Mbuzi (🐐) bila msimamizi → Simba atamla!\n"
            "• Mbuzi (🐐) akiachwa na Nyasi (🌿) bila msimamizi → Mbuzi atakula!\n"
            "• Simba, Mbuzi na Nyasi wote pamoja bila msimamizi → Simba atamla Mbuzi\n"
            "  (Simba ana kasi, Nyasi iko katikati, Mbuzi hafikii Nyasi).\n"
            "• Mashua haiwezi kwenda bila msimamizi.\n"
            "─────────────────────────────────────────────────────────────\n"
            "• Lion + Goat left alone → Lion eats Goat!\n"
            "• Goat + Grass left alone → Goat eats Grass!\n"
            "• Lion, Goat & Grass together without supervisor → Lion eats Goat\n"
            "  (Lion is faster, Grass in the middle, Goat can't reach Grass).\n"
            "• The boat won't move without the supervisor."
        ), font=("Helvetica", 9), bg="#0a1520", fg=TEXT_TEAL,
                                  justify="left", padx=12, pady=6)

    # ──────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────
    def _sup_side(self):
        """Return 'left' or 'right' depending on where the supervisor currently is."""
        return "left" if "supervisor" in self.left else "right"

    def _bank(self, side):
        """Return the set of items on the given side ('left' or 'right')."""
        return self.left if side == "left" else self.right

    def _other(self, side):
        """Return the opposite side."""
        return "right" if side == "left" else "left"

    def _set_status(self, msg, error=False):
        self.status_var.set(msg)
        self.status_lbl.config(fg=ERR_RED if error else OK_GREEN)

    def _toggle_rules(self):
        self.rules_visible = not self.rules_visible
        if self.rules_visible:
            self.rules_lbl.pack(padx=20, pady=4)
            self.rules_btn.config(text="ℹ️  Hide Rules")
        else:
            self.rules_lbl.pack_forget()
            self.rules_btn.config(text="ℹ️  Show Rules")

    # ──────────────────────────────────────────
    #  RENDERING
    # ──────────────────────────────────────────
    def _render(self, anim_item=None):
        """Draw the full scene. anim_item is the item currently on the boat."""
        cv = self.cv
        cv.delete("all")

        # ── Sky gradient ──
        for i in range(15):
            shade = "#%02x%02x%02x" % (11+i*3, 26+i*4, 47+i*5)
            cv.create_rectangle(0, i*10, W, (i+1)*10, fill=shade, outline="")

        # ── Sun ──
        cv.create_oval(70, 25, 120, 75, fill="#f4d03f", outline="#f9e076", width=2)
        cv.create_oval(80, 35, 110, 65, fill="#fdebd0", outline="")

        # ── Clouds ──
        for (cx, cy) in [(200, 30), (450, 20), (700, 40)]:
            cv.create_oval(cx-30, cy-10, cx+30, cy+10, fill="#d4e6f1", outline="")
            cv.create_oval(cx-15, cy-20, cx+15, cy, fill="#e0eaf5", outline="")
            cv.create_oval(cx+10, cy-18, cx+35, cy+2, fill="#d4e6f1", outline="")

        # ── Left bank ──
        cv.create_rectangle(0, 80, 270, H,   fill=BANK_TOP, outline="")
        cv.create_rectangle(0, H-45, 270, H, fill=BANK_BOT, outline="")
        # Trees on left bank
        self._draw_trees(cv, [(30, 120), (100, 150), (200, 100)])
        # Texture lines
        for y in range(90, H-50, 18):
            cv.create_line(0, y, 270, y, fill="#163a2a", width=1)

        # ── Right bank ──
        cv.create_rectangle(630, 80, W, H,   fill=BANK_TOP, outline="")
        cv.create_rectangle(630, H-45, W, H, fill=BANK_BOT, outline="")
        self._draw_trees(cv, [(680, 140), (770, 110), (850, 160)])
        for y in range(90, H-50, 18):
            cv.create_line(630, y, W, y, fill="#163a2a", width=1)

        # ── River ──
        for i in range(25):
            r = int(0x0a + i*0.4)
            g = int(0x2e + i*0.3)
            b = int(0x5c + i*0.5)
            shade = "#%02x%02x%02x" % (min(r,255), min(g,255), min(b,255))
            cv.create_rectangle(270, 80 + i*18, 630, 80 + (i+1)*18,
                                fill=shade, outline="")

        # Waves
        t = int(time.time() * 2) % 25
        for row in range(6):
            y = 100 + row * 55
            for col in range(10):
                x = 275 + col * 37 + (t if row % 2 == 0 else -t)
                cv.create_arc(x, y, x+30, y+12,
                              start=0, extent=180,
                              outline=WAVE_CLR, width=1.5, style="arc")

        # ── Bank labels ──
        cv.create_text(135, 92, text="LEFT BANK",
                       font=("Helvetica", 10, "bold"), fill=TEXT_TEAL)
        cv.create_text(765, 92, text="RIGHT BANK",
                       font=("Helvetica", 10, "bold"), fill=TEXT_TEAL)

        # ── Boat ──
        bx = self.boat_x
        self._draw_boat(bx, 270, anim_item)

        # ── Bank items (hide those that are on the boat or in transit) ──
        left_show  = self.left  - ({"supervisor"} | ({anim_item} if anim_item else set())
                                   if self._sup_side() == "left" else set())
        right_show = self.right - ({"supervisor"} | ({anim_item} if anim_item else set())
                                   if self._sup_side() == "right" else set())

        # During animation the supervisor is "in transit"
        if self.animating:
            left_show.discard("supervisor")
            right_show.discard("supervisor")
            if anim_item:
                left_show.discard(anim_item)
                right_show.discard(anim_item)

        self._draw_bank_items(left_show, cx=135)
        self._draw_bank_items(right_show, cx=765)

        # ── Ripple under boat ──
        cv.create_oval(bx+10, 300, bx+100, 316,
                       outline="#3a7bd5", width=1)

        # ── Overlays (loss / win) ──
        if self.game_over and self.loss_message:
            self._draw_loss_overlay()
        elif self.game_over:
            self._draw_win_overlay()

        # Refresh dropdown
        self._refresh_dropdown()

    def _draw_trees(self, cv, positions):
        for (x, y) in positions:
            # trunk
            cv.create_rectangle(x-3, y, x+3, y+20, fill="#4a3b2f", outline="")
            # foliage triangles
            for offset, size in [(0, 15), (0, 25), (0, 35)]:
                cv.create_polygon(x, y-offset-5,
                                  x-size//2, y-offset-5+size*0.6,
                                  x+size//2, y-offset-5+size*0.6,
                                  fill="#2d6230", outline="#1b4720")

    def _draw_boat(self, bx, by, cargo_item=None):
        cv = self.cv
        bw = 110

        # Shadow (solid dark grey, no alpha)
        cv.create_oval(bx+5, by+38, bx+bw-5, by+50,
                       fill="#1a1a1a", outline="")
        # Hull
        cv.create_polygon(
            bx+2, by,  bx+bw-2, by,
            bx+bw-14, by+38, bx+14, by+38,
            fill=BOAT_HULL, outline=BOAT_RIM, width=3)
        # Top plank / rim
        cv.create_rectangle(bx-2, by-14, bx+bw+2, by+4,
                            fill="#b87a52", outline=BOAT_RIM, width=2)
        # Wood grain lines
        for i in range(3):
            yy = by - 10 + i * 4
            cv.create_line(bx+6, yy, bx+bw-6, yy, fill="#7a4a1e", width=1)

        # Oar
        cv.create_line(bx+bw//2-5, by-6, bx+bw//2+38, by-34,
                       fill=BOAT_OAR, width=3, capstyle="round")
        cv.create_oval(bx+bw//2+30, by-40, bx+bw//2+46, by-28,
                       fill=BOAT_OAR, outline=BOAT_RIM)

        # Supervisor on boat
        sup_side = self._sup_side()
        boat_at_left  = (bx < 400)
        show_sup = self.animating or (boat_at_left and sup_side == "left") or \
                   (not boat_at_left and sup_side == "right")

        items_on_boat = []
        if show_sup or self.animating:
            items_on_boat.append("supervisor")
        if cargo_item:
            items_on_boat.append(cargo_item)

        cx = bx + bw // 2
        n = len(items_on_boat)
        for i, item in enumerate(items_on_boat):
            ox = cx + (i - (n-1)/2) * 32
            col = CHAR_COLORS[item]
            cv.create_oval(ox-16, by-32, ox+16, by-2,
                           fill=col, outline="white", width=1)
            cv.create_text(ox, by-17, text=EMOJIS[item],
                           font=("Arial", 15))

    def _draw_bank_items(self, items, cx):
        """
        Draw the set of items on a bank, centred at horizontal position cx.
        
        IMPORTANT: If the three items are {lion, goat, grass}, we enforce a
        special order: LION – GRASS – GOAT, so that the grass is exactly in
        the middle with equal spacing. This matches the new rule where the
        lion reaches the goat before the goat can reach the grass.
        For any other combination, items are sorted alphabetically.
        """
        if not items:
            return
        # Choose the order (list) for drawing.
        if items == {"lion", "goat", "grass"}:
            # Custom order: lion on one side, grass in centre, goat on the other
            items_list = ["lion", "grass", "goat"]
        else:
            items_list = sorted(items)   # default alphabetical (goat, grass, lion etc.)

        n = len(items_list)
        # Maximum horizontal space for drawing: 220px (within the bank area)
        # Spacing between adjacent items is limited to 90px so they don't spread too far.
        spacing = min(90, 220 // max(n, 1))
        # x0 is the leftmost item coordinate
        x0 = cx - spacing * (n - 1) / 2

        for i, item in enumerate(items_list):
            # Calculate x position: centre of the i-th item
            x = int(x0 + i * spacing)
            y = 240
            col = CHAR_COLORS[item]
            # glow shadow
            self.cv.create_oval(x-26, y-26, x+26, y+26,
                                fill="#000000", outline="")
            # colour bubble
            self.cv.create_oval(x-24, y-27, x+24, y+23,
                                fill=col, outline=TEXT_WHITE, width=2)
            # emoji
            self.cv.create_text(x, y-2, text=EMOJIS[item],
                                font=("Arial", 20))
            # label
            self.cv.create_text(x, y+34,
                                text=item.capitalize(),
                                font=("Helvetica", 8, "bold"), fill=TEXT_WHITE)

    # ──────────────────────────────────────────
    #  LOSS / WIN OVERLAYS
    # ──────────────────────────────────────────
    def _draw_loss_overlay(self):
        cv = self.cv
        # dark overlay
        cv.create_rectangle(0, 0, W, H, fill="#000000", stipple="gray25")
        # modal box
        bx, by, bw, bh = 200, 120, 500, 200
        cv.create_rectangle(bx, by, bx+bw, by+bh,
                            fill=LOSE_OVERLAY, outline=TEXT_GOLD, width=3)
        cv.create_text(bx+bw//2, by+40,
                       text="❌  UMEPOTEZA!  ❌",
                       font=("Helvetica", 22, "bold"), fill=TEXT_GOLD)
        message = self.loss_message + "\nTahadhari: Hakuna msimamizi!"
        cv.create_text(bx+bw//2, by+90,
                       text=message,
                       font=("Helvetica", 12), fill=TEXT_WHITE, justify="center", width=450)
        # Try Again button (canvas text that responds to clicks)
        btn_x1, btn_y1 = bx+bw//2-80, by+130
        btn_x2, btn_y2 = btn_x1+160, btn_y1+40
        cv.create_rectangle(btn_x1, btn_y1, btn_x2, btn_y2,
                            fill=MODAL_BTN, outline=TEXT_GOLD, width=2,
                            tags="tryagain_btn")
        cv.create_text(btn_x1+80, btn_y1+20,
                       text="↻  Try Again",
                       font=("Helvetica", 13, "bold"), fill="black",
                       tags="tryagain_btn")

    def _draw_win_overlay(self):
        cv = self.cv
        cv.create_rectangle(0, 0, W, H, fill="#000000", stipple="gray25")
        bx, by, bw, bh = 200, 120, 500, 200
        cv.create_rectangle(bx, by, bx+bw, by+bh,
                            fill=WIN_OVERLAY, outline=TEXT_GOLD, width=3)
        cv.create_text(bx+bw//2, by+40,
                       text="🎉  UMEFANIKIWA!  🎉",
                       font=("Helvetica", 22, "bold"), fill=TEXT_GOLD)
        cv.create_text(bx+bw//2, by+90,
                       text=f"Hongera! Umevuka kwa hatua {self.moves}.",
                       font=("Helvetica", 13), fill=TEXT_WHITE)
        btn_x1, btn_y1 = bx+bw//2-80, by+130
        btn_x2, btn_y2 = btn_x1+160, btn_y1+40
        cv.create_rectangle(btn_x1, btn_y1, btn_x2, btn_y2,
                            fill=MODAL_BTN, outline=TEXT_GOLD, width=2,
                            tags="tryagain_btn")
        cv.create_text(btn_x1+80, btn_y1+20,
                       text="↻  Play Again",
                       font=("Helvetica", 13, "bold"), fill="black",
                       tags="tryagain_btn")

    def _canvas_click(self, event):
        """Check if user clicked on a modal button."""
        if self.game_over:
            # Check if we hit any item tagged "tryagain_btn"
            items = self.cv.find_withtag("tryagain_btn")
            for item in items:
                coords = self.cv.bbox(item)
                if coords:
                    x1, y1, x2, y2 = coords
                    if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                        self._reset()
                        return

    # ──────────────────────────────────────────
    #  DROPDOWN REFRESH
    # ──────────────────────────────────────────
    def _refresh_dropdown(self):
        sup = self._sup_side()
        bank = self._bank(sup)
        available = [it for it in CARGO if it in bank]
        self.take_menu["values"] = available
        if available:
            if self.take_var.get() not in available:
                self.take_var.set(available[0])
        else:
            self.take_var.set("–")

    # ──────────────────────────────────────────
    #  ANIMATION
    # ──────────────────────────────────────────
    def _animate(self, dest_x, on_done, payload=None):
        """
        Smoothly move the boat from current boat_x to dest_x.
        Step size computed as (dest_x - boat_x) / ANIM_STEPS.
        Each tick moves the boat a fraction and re-renders.
        """
        self.animating = True
        step_size = (dest_x - self.boat_x) / self.ANIM_STEPS

        def tick(remaining):
            if remaining <= 0:
                self.boat_x = dest_x
                self.animating = False
                on_done()
                return
            self.boat_x += step_size
            self._render(anim_item=payload)
            self.after(16, tick, remaining - 1)

        tick(self.ANIM_STEPS)

    # ──────────────────────────────────────────
    #  MOVE LOGIC (no warnings, only loss)
    # ──────────────────────────────────────────
    def _attempt_move(self, cargo=None):
        if self.animating or self.game_over:
            return

        sup = self._sup_side()
        dest = self._other(sup)

        # Compute the new state after the move
        new_left  = self.left.copy()
        new_right = self.right.copy()

        # Remove supervisor and cargo from both sides (they are in transit)
        for bank in (new_left, new_right):
            bank.discard("supervisor")
            if cargo:
                bank.discard(cargo)

        # Place supervisor (and cargo) on the destination bank
        dest_bank = new_right if dest == "right" else new_left
        dest_bank.add("supervisor")
        if cargo:
            dest_bank.add(cargo)

        # Check safety of the new state (only loss, no warning)
        ok, msg = check_safety(new_left, new_right)

        # Boat destination pixel (left bank: 290, right bank: 490)
        dest_boat_x = 290.0 if dest == "left" else 490.0

        def finalize():
            self.left  = new_left
            self.right = new_right
            self.moves += 1
            self.moves_lbl.config(text=f"Moves: {self.moves}")
            if not ok:
                # Game Over - Loss
                self.game_over = True
                self.loss_message = msg
                self._set_status("❌ Umepoteza! " + msg, error=True)
                self._render()   # will show loss overlay
            else:
                if cargo:
                    self._set_status(
                        f"✅ Msimamizi amevusha {cargo} upande wa {dest}!  "
                        f"(Supervisor took the {cargo} to the {dest} bank.)")
                else:
                    self._set_status(
                        f"✅ Msimamizi amevuka upande wa {dest} peke yake!  "
                        f"(Supervisor crossed to the {dest} bank alone.)")
                self._render()
                self._check_win()

        self._animate(dest_boat_x, on_done=finalize, payload=cargo)

    def _go_alone(self):
        self._attempt_move(cargo=None)

    def _take_item(self):
        item = self.take_var.get()
        if item in ("–", "", None):
            self._set_status("⚠️  Chagua kitu kwanza! / Select an item first!", error=True)
            return
        sup = self._sup_side()
        if item not in self._bank(sup):
            self._set_status("⚠️  Kitu hiki hakiko upande wa msimamizi!", error=True)
            return
        self._attempt_move(cargo=item)

    # ──────────────────────────────────────────
    #  WIN CHECK
    # ──────────────────────────────────────────
    def _check_win(self):
        if self.right == {"supervisor", "lion", "goat", "grass"}:
            self.game_over = True
            self.loss_message = ""   # not a loss
            self._set_status(
                f"🎉 UMESHINDA kwa hatua {self.moves}!  YOU WIN in {self.moves} moves! 🎉")
            self._render()   # will show win overlay

    # ──────────────────────────────────────────
    #  RESET
    # ──────────────────────────────────────────
    def _reset(self):
        self._init_state()
        self.moves_lbl.config(text="Moves: 0")
        self._set_status("🎯 Vushia kila kitu upande wa kulia!  /  Get everyone to the RIGHT bank!")
        self._render()


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    app = RiverGame()
    # Animate waves by re-rendering every 800 ms
    def _wave_tick():
        if not app.animating and not app.game_over:
            app._render()
        app.after(800, _wave_tick)
    app.after(800, _wave_tick)
    app.mainloop()