import tkinter as tk
from tkinter import ttk
import math, time

# ------------------------- CONSTANTS (Colours, Layout, Game) -------------------------
BG                = "#59749B"
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

W, H = 900, 440

# ---------- Game constants for energy & speed ----------
MAX_ENERGY = 100
CROSS_ENERGY_COST = 10               # energy lost each time lion or goat crosses
BASE_SPEED_LION = 5.0                # units per second (conceptual)
BASE_SPEED_GOAT = 3.0
DISTANCE_LION_GOAT = 1.0             # relative distance between lion and goat
DISTANCE_GOAT_GRASS = 1.0            # relative distance between goat and grass

# ------------------------- Safety & Chase Logic -------------------------
def compute_chase_outcome(bank_set, supervisor_present, lion_energy, goat_energy):
    """
    Returns (safe: bool, message: str, eaten: str)
    eaten can be None, "goat" or "grass"
    """
    if supervisor_present:
        return True, "", None

    lion_here = "lion" in bank_set
    goat_here = "goat" in bank_set
    grass_here = "grass" in bank_set

    # Lion + Goat (and possibly Grass) – Lion chases Goat
    if lion_here and goat_here:
        lion_speed = BASE_SPEED_LION * (lion_energy / MAX_ENERGY)
        goat_speed = BASE_SPEED_GOAT * (goat_energy / MAX_ENERGY)
        # Lion catches goat in t_lion = distance / speed
        t_lion = DISTANCE_LION_GOAT / max(lion_speed, 0.01)

        # Also possible Goat + Grass chase (if grass present)
        t_goat = float('inf')
        if goat_here and grass_here:
            t_goat = DISTANCE_GOAT_GRASS / max(goat_speed, 0.01)

        if t_lion <= t_goat:
            return False, "🦁 Simba amemkamata mbuzi! (Lion caught the goat!)", "goat"
        else:
            return False, "🐐 Mbuzi amekula nyasi kabla simba hajamkamata! (Goat ate the grass first!)", "grass"

    # Only Goat + Grass (no Lion)
    if goat_here and grass_here and not lion_here:
        return False, "🐐 Mbuzi amekula nyasi! (Goat ate the grass!)", "grass"

    # No dangerous pair
    return True, "", None


class RiverGame(tk.Tk):
    ANIM_STEPS = 30

    def __init__(self):
        super().__init__()
        self.title("🌊  Mchezo wa Kuvuka Mto  |  River Crossing Puzzle (Energy & Chase)")
        self.resizable(False, False)
        self.configure(bg=BG)

        # ttk style
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Go.TButton", background=BTN_GO_ALONE, foreground="white",
                        font=("Helvetica", 11, "bold"), borderwidth=0, relief="flat", padding=10)
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
        self._update_energy_display()
        self._render()

    # ------------------------- State Management -------------------------
    def _init_state(self):
        self.left      = {"supervisor", "lion", "goat", "grass"}
        self.right     = set()
        self.moves     = 0
        self.boat_x    = 290.0        # left bank boat position
        self.animating = False
        self.anim_payload = None
        self.game_over = False
        self.loss_message = ""

        # Energy & speed tracking
        self.lion_energy = MAX_ENERGY
        self.goat_energy = MAX_ENERGY

    def _reset(self):
        self._init_state()
        self.moves_lbl.config(text="Moves: 0")
        self._set_status("🎯 Vushia kila kitu upande wa kulia!  /  Get everyone to the RIGHT bank!")
        self._update_energy_display()
        self._render()

    def _sup_side(self):
        return "left" if "supervisor" in self.left else "right"

    def _bank(self, side):
        return self.left if side == "left" else self.right

    def _other(self, side):
        return "right" if side == "left" else "left"

    def _set_status(self, msg, error=False):
        self.status_var.set(msg)
        self.status_lbl.config(fg=ERR_RED if error else OK_GREEN)

    # ------------------------- UI Building (Energy Bars) -------------------------
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(10, 0))

        tk.Label(hdr, text="🌊  River Crossing Puzzle (Energy + Chase)",
                 font=("Helvetica", 18, "bold"), bg=BG, fg=TEXT_GOLD).pack(side="left")

        self.moves_lbl = tk.Label(hdr, text="Moves: 0", font=("Helvetica", 13, "bold"),
                                  bg=BG, fg=TEXT_TEAL)
        self.moves_lbl.pack(side="right", padx=6)

        # --- Energy display frame (lion & goat progress bars) ---
        energy_frame = tk.Frame(self, bg=BG)
        energy_frame.pack(fill="x", padx=20, pady=(5, 0))

        # Lion energy
        tk.Label(energy_frame, text="🦁 Lion Energy:", font=("Helvetica", 10, "bold"),
                 bg=BG, fg=TEXT_WHITE).pack(side="left", padx=(0, 5))
        self.lion_bar = ttk.Progressbar(energy_frame, length=180, mode='determinate',
                                        maximum=MAX_ENERGY, value=MAX_ENERGY)
        self.lion_bar.pack(side="left", padx=(0, 10))
        self.lion_energy_lbl = tk.Label(energy_frame, text="100%", font=("Helvetica", 10),
                                        bg=BG, fg=TEXT_TEAL)
        self.lion_energy_lbl.pack(side="left", padx=(0, 20))

        # Goat energy
        tk.Label(energy_frame, text="🐐 Goat Energy:", font=("Helvetica", 10, "bold"),
                 bg=BG, fg=TEXT_WHITE).pack(side="left", padx=(0, 5))
        self.goat_bar = ttk.Progressbar(energy_frame, length=180, mode='determinate',
                                        maximum=MAX_ENERGY, value=MAX_ENERGY)
        self.goat_bar.pack(side="left", padx=(0, 10))
        self.goat_energy_lbl = tk.Label(energy_frame, text="100%", font=("Helvetica", 10),
                                        bg=BG, fg=TEXT_TEAL)
        self.goat_energy_lbl.pack(side="left")

        # Canvas
        self.cv = tk.Canvas(self, width=W, height=H, bg=BG, highlightthickness=0)
        self.cv.pack(padx=20, pady=6)
        self.cv.bind("<Button-1>", self._canvas_click)

        # Status
        self.status_var = tk.StringVar(value="🎯 Get everyone to the RIGHT bank!  (Energy affects chase)")
        self.status_lbl = tk.Label(self, textvariable=self.status_var, font=("Helvetica", 11),
                                   bg=BG, fg=OK_GREEN, wraplength=860, justify="center")
        self.status_lbl.pack(pady=(0, 4))

        # Control panel
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=8)

        ttk.Button(ctrl, text="🚣  Go Alone", style="Go.TButton", command=self._go_alone).grid(row=0, column=0, padx=10)
        tk.Frame(ctrl, width=2, bg="#334455").grid(row=0, column=1, padx=6, pady=4, sticky="ns")

        take_f = tk.Frame(ctrl, bg=BG)
        take_f.grid(row=0, column=2, padx=10)
        tk.Label(take_f, text="Chagua / Take:", font=("Helvetica", 11), bg=BG, fg=TEXT_WHITE).pack(side="left", padx=(0, 6))
        self.take_var = tk.StringVar(value="goat")
        self.take_menu = ttk.Combobox(take_f, textvariable=self.take_var, state="readonly",
                                      font=("Helvetica", 11), width=12)
        self.take_menu.pack(side="left")
        ttk.Button(take_f, text="Take  ➜", style="Take.TButton", command=self._take_item).pack(side="left", padx=(8, 0))

        tk.Frame(ctrl, width=2, bg="#334455").grid(row=0, column=3, padx=6, pady=4, sticky="ns")
        ttk.Button(ctrl, text="🔄  Reset", style="Reset.TButton", command=self._reset).grid(row=0, column=4, padx=10)

        # Rules toggle
        self.rules_visible = False
        self.rules_btn = tk.Button(self, text="ℹ️  Show Rules", command=self._toggle_rules,
                                   font=("Helvetica", 9), bg=BG, fg=TEXT_TEAL, relief="flat", cursor="hand2", bd=0)
        self.rules_btn.pack()
        self.rules_lbl = tk.Label(self, text=(
            "• Simba (🦁) + Mbuzi (🐐) bila msimamizi → Simba humkamata mbuzi (kasi inategemea nguvu)\n"
            "• Mbuzi (🐐) + Nyasi (🌿) bila msimamizi → Mbuzi hula nyasi\n"
            "• Wote watatu pamoja: Simba hukimbia mbuzi, mbuzi hukimbia nyasi. Mchujo hufanyika kwa kasi (nguvu)\n"
            "• Kila kuvuka kwa simba au mbuzi kunapunguza nguvu kwa 10% (huathiri kasi)\n"
            "• Mashua haiwezi kwenda bila msimamizi.\n"
            "─────────────────────────────────────────────────────────────\n"
            "• Lion + Goat without supervisor → Lion chases Goat (speed depends on energy)\n"
            "• Goat + Grass without supervisor → Goat eats Grass\n"
            "• All three together → race: Lion towards Goat, Goat towards Grass\n"
            "• Lion or goat lose 10 energy each time they cross the river (affects speed)\n"
            "• The boat won't move without the supervisor."
        ), font=("Helvetica", 9), bg="#0a1520", fg=TEXT_TEAL, justify="left", padx=12, pady=6)

    def _update_energy_display(self):
        """Refresh the energy bars and percentage labels."""
        self.lion_bar['value'] = self.lion_energy
        self.goat_bar['value'] = self.goat_energy
        self.lion_energy_lbl.config(text=f"{int(self.lion_energy)}%")
        self.goat_energy_lbl.config(text=f"{int(self.goat_energy)}%")

    # ------------------------- Drawing (with energy bars on animals) -------------------------
    def _draw_bank_items(self, items, cx):
        """Draw items on a bank, adding energy bar for lion and goat."""
        if not items:
            return

        # For aesthetic order: if all three present, show lion, grass, goat (gap in middle)
        if items == {"lion", "goat", "grass"}:
            items_list = ["lion", "grass", "goat"]
        else:
            items_list = sorted(items)

        n = len(items_list)
        spacing = min(90, 220 // max(n, 1))
        x0 = cx - spacing * (n - 1) / 2

        for i, item in enumerate(items_list):
            x = int(x0 + i * spacing)
            y = 240
            col = CHAR_COLORS[item]
            # drop shadow
            self.cv.create_oval(x-26, y-26, x+26, y+26, fill="#000000", outline="")
            self.cv.create_oval(x-24, y-27, x+24, y+23, fill=col, outline=TEXT_WHITE, width=2)
            self.cv.create_text(x, y-2, text=EMOJIS[item], font=("Arial", 20))
            self.cv.create_text(x, y+34, text=item.capitalize(), font=("Helvetica", 8, "bold"), fill=TEXT_WHITE)

            # Draw energy bar for lion or goat
            if item == "lion":
                energy = self.lion_energy
                pct = energy / MAX_ENERGY
                bar_width = 48
                bar_height = 8
                bar_x = x - bar_width//2
                bar_y = y + 50
                self.cv.create_rectangle(bar_x, bar_y, bar_x+bar_width, bar_y+bar_height,
                                         fill="#333333", outline="")
                fill_width = int(bar_width * pct)
                self.cv.create_rectangle(bar_x, bar_y, bar_x+fill_width, bar_y+bar_height,
                                         fill="#ffb74d", outline="")
                self.cv.create_text(x, bar_y-5, text=f"{int(energy)}%", font=("Helvetica", 8), fill="white")
            elif item == "goat":
                energy = self.goat_energy
                pct = energy / MAX_ENERGY
                bar_width = 48
                bar_height = 8
                bar_x = x - bar_width//2
                bar_y = y + 50
                self.cv.create_rectangle(bar_x, bar_y, bar_x+bar_width, bar_y+bar_height,
                                         fill="#333333", outline="")
                fill_width = int(bar_width * pct)
                self.cv.create_rectangle(bar_x, bar_y, bar_x+fill_width, bar_y+bar_height,
                                         fill="#81c784", outline="")
                self.cv.create_text(x, bar_y-5, text=f"{int(energy)}%", font=("Helvetica", 8), fill="white")

    def _draw_loss_overlay(self):
        cv = self.cv
        cv.create_rectangle(0, 0, W, H, fill="#000000", stipple="gray25")
        bx, by, bw, bh = 200, 120, 500, 200
        cv.create_rectangle(bx, by, bx+bw, by+bh, fill=LOSE_OVERLAY, outline=TEXT_GOLD, width=3)
        cv.create_text(bx+bw//2, by+40, text="❌  UMEPOTEZA!  ❌", font=("Helvetica", 22, "bold"), fill=TEXT_GOLD)
        cv.create_text(bx+bw//2, by+90, text=self.loss_message, font=("Helvetica", 12), fill=TEXT_WHITE, justify="center", width=450)
        btn_x1, btn_y1 = bx+bw//2-80, by+130
        btn_x2, btn_y2 = btn_x1+160, btn_y1+40
        cv.create_rectangle(btn_x1, btn_y1, btn_x2, btn_y2, fill=MODAL_BTN, outline=TEXT_GOLD, width=2, tags="tryagain_btn")
        cv.create_text(btn_x1+80, btn_y1+20, text="↻  Try Again", font=("Helvetica", 13, "bold"), fill="black", tags="tryagain_btn")

    def _draw_win_overlay(self):
        cv = self.cv
        cv.create_rectangle(0, 0, W, H, fill="#000000", stipple="gray25")
        bx, by, bw, bh = 200, 120, 500, 200
        cv.create_rectangle(bx, by, bx+bw, by+bh, fill=WIN_OVERLAY, outline=TEXT_GOLD, width=3)
        cv.create_text(bx+bw//2, by+40, text="🎉  UMEFANIKIWA!  🎉", font=("Helvetica", 22, "bold"), fill=TEXT_GOLD)
        cv.create_text(bx+bw//2, by+90, text=f"Hongera! Umevuka kwa hatua {self.moves}.", font=("Helvetica", 13), fill=TEXT_WHITE)
        btn_x1, btn_y1 = bx+bw//2-80, by+130
        btn_x2, btn_y2 = btn_x1+160, btn_y1+40
        cv.create_rectangle(btn_x1, btn_y1, btn_x2, btn_y2, fill=MODAL_BTN, outline=TEXT_GOLD, width=2, tags="tryagain_btn")
        cv.create_text(btn_x1+80, btn_y1+20, text="↻  Play Again", font=("Helvetica", 13, "bold"), fill="black", tags="tryagain_btn")

    # ------------------------- Game Logic (Safety with Energy & Chase) -------------------------
    def _evaluate_bank_safety(self, left_set, right_set):
        """Check both banks using current lion/goat energy. Returns (safe, message)."""
        for bank_side, bank_set in [("left", left_set), ("right", right_set)]:
            sup_present = "supervisor" in bank_set
            safe, msg, _ = compute_chase_outcome(bank_set, sup_present, self.lion_energy, self.goat_energy)
            if not safe:
                # Append bank side
                return False, f"{msg} (upande wa {bank_side})"
        return True, ""

    def _check_post_move_loss_and_win(self):
        """After state update, check if any bank is unsafe (loss) or win."""
        safe, msg = self._evaluate_bank_safety(self.left, self.right)
        if not safe:
            self.game_over = True
            self.loss_message = msg
            self._set_status(f"❌ {msg}", error=True)
            self._render()
            return True  # loss happened
        # Win condition
        if self.right == {"supervisor", "lion", "goat", "grass"}:
            self.game_over = True
            self.loss_message = ""
            self._set_status(f"🎉 UMESHINDA kwa hatua {self.moves}!  YOU WIN! 🎉")
            self._render()
            return True
        return False

    # ------------------------- Movement and Animation -------------------------
    def _go_alone(self):
        if self.animating or self.game_over:
            return
        sup = self._sup_side()
        dest = self._other(sup)
        new_left = self.left.copy()
        new_right = self.right.copy()
        # supervisor moves
        new_left.discard("supervisor")
        new_right.discard("supervisor")
        (new_right if dest == "right" else new_left).add("supervisor")

        dest_boat_x = 290.0 if dest == "left" else 490.0

        def finalize():
            self.left = new_left
            self.right = new_right
            self.moves += 1
            self.moves_lbl.config(text=f"Moves: {self.moves}")
            # No energy change for going alone
            self._set_status(f"✅ Msimamizi amevuka peke yake upande wa {dest}.")
            self._render()
            self._check_post_move_loss_and_win()

        self._animate(dest_boat_x, finalize, payload=None)

    def _take_item(self):
        if self.animating or self.game_over:
            return
        item = self.take_var.get()
        if item in ("–", "", None):
            self._set_status("⚠️  Chagua kitu kwanza!", error=True)
            return
        sup = self._sup_side()
        if item not in self._bank(sup):
            self._set_status("⚠️  Kitu hiki hakiko upande wa msimamizi!", error=True)
            return

        dest = self._other(sup)
        new_left = self.left.copy()
        new_right = self.right.copy()
        # Remove supervisor and cargo from both, then add to dest side
        new_left.discard("supervisor")
        new_right.discard("supervisor")
        if item:
            new_left.discard(item)
            new_right.discard(item)

        dest_bank = new_right if dest == "right" else new_left
        dest_bank.add("supervisor")
        if item:
            dest_bank.add(item)

        dest_boat_x = 290.0 if dest == "left" else 490.0

        def finalize():
            self.left = new_left
            self.right = new_right
            # Apply energy loss if cargo is lion or goat
            energy_msg = ""
            if item == "lion":
                self.lion_energy = max(0, self.lion_energy - CROSS_ENERGY_COST)
                energy_msg = f"Simba anapoteza nguvu ({CROSS_ENERGY_COST})! → {self.lion_energy}%"
                self._update_energy_display()
            elif item == "goat":
                self.goat_energy = max(0, self.goat_energy - CROSS_ENERGY_COST)
                energy_msg = f"Mbuzi anapoteza nguvu ({CROSS_ENERGY_COST})! → {self.goat_energy}%"
                self._update_energy_display()

            self.moves += 1
            self.moves_lbl.config(text=f"Moves: {self.moves}")
            self._set_status(f"✅ Msimamizi amevusha {item} upande wa {dest}. {energy_msg}")
            self._render()
            self._check_post_move_loss_and_win()

        self._animate(dest_boat_x, finalize, payload=item)

    def _animate(self, dest_x, on_done, payload=None):
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

    def _render(self, anim_item=None):
        """Draw full scene (banks, boat, items, energy bars)."""
        cv = self.cv
        cv.delete("all")

        # Sky & river gradient
        for i in range(15):
            shade = "#%02x%02x%02x" % (11+i*3, 26+i*4, 47+i*5)
            cv.create_rectangle(0, i*10, W, (i+1)*10, fill=shade, outline="")
        # Sun & clouds
        cv.create_oval(70, 25, 120, 75, fill="#f4d03f", outline="#f9e076", width=2)
        cv.create_oval(80, 35, 110, 65, fill="#fdebd0", outline="")
        for (cx, cy) in [(200, 30), (450, 20), (700, 40)]:
            cv.create_oval(cx-30, cy-10, cx+30, cy+10, fill="#d4e6f1", outline="")
            cv.create_oval(cx-15, cy-20, cx+15, cy, fill="#e0eaf5", outline="")
            cv.create_oval(cx+10, cy-18, cx+35, cy+2, fill="#d4e6f1", outline="")

        # Banks
        cv.create_rectangle(0, 80, 270, H,   fill=BANK_TOP, outline="")
        cv.create_rectangle(0, H-45, 270, H, fill=BANK_BOT, outline="")
        self._draw_trees(cv, [(30, 120), (100, 150), (200, 100)])
        cv.create_rectangle(630, 80, W, H,   fill=BANK_TOP, outline="")
        cv.create_rectangle(630, H-45, W, H, fill=BANK_BOT, outline="")
        self._draw_trees(cv, [(680, 140), (770, 110), (850, 160)])

        # River water
        for i in range(25):
            r = int(0x0a + i*0.4)
            g = int(0x2e + i*0.3)
            b = int(0x5c + i*0.5)
            shade = "#%02x%02x%02x" % (min(r,255), min(g,255), min(b,255))
            cv.create_rectangle(270, 80 + i*18, 630, 80 + (i+1)*18, fill=shade, outline="")

        # Waves
        t = int(time.time() * 2) % 25
        for row in range(6):
            y = 100 + row * 55
            for col in range(10):
                x = 275 + col * 37 + (t if row % 2 == 0 else -t)
                cv.create_arc(x, y, x+30, y+12, start=0, extent=180, outline=WAVE_CLR, width=1.5, style="arc")

        cv.create_text(135, 92, text="LEFT BANK", font=("Helvetica", 10, "bold"), fill=TEXT_TEAL)
        cv.create_text(765, 92, text="RIGHT BANK", font=("Helvetica", 10, "bold"), fill=TEXT_TEAL)

        # Boat
        bx = self.boat_x
        self._draw_boat(bx, 270, anim_item)

        # Calculate visible sets (hide items on boat during animation)
        left_show = self.left - ({"supervisor"} | ({anim_item} if anim_item else set())
                                 if self._sup_side() == "left" else set())
        right_show = self.right - ({"supervisor"} | ({anim_item} if anim_item else set())
                                   if self._sup_side() == "right" else set())
        if self.animating:
            left_show.discard("supervisor")
            right_show.discard("supervisor")
            if anim_item:
                left_show.discard(anim_item)
                right_show.discard(anim_item)

        self._draw_bank_items(left_show, cx=135)
        self._draw_bank_items(right_show, cx=765)

        # Modals
        if self.game_over and self.loss_message:
            self._draw_loss_overlay()
        elif self.game_over:
            self._draw_win_overlay()

        self._refresh_dropdown()

    def _draw_boat(self, bx, by, cargo_item=None):
        cv = self.cv
        bw = 110
        cv.create_oval(bx+5, by+38, bx+bw-5, by+50, fill="#1a1a1a", outline="")
        cv.create_polygon(bx+2, by,  bx+bw-2, by, bx+bw-14, by+38, bx+14, by+38,
                          fill=BOAT_HULL, outline=BOAT_RIM, width=3)
        cv.create_rectangle(bx-2, by-14, bx+bw+2, by+4, fill="#b87a52", outline=BOAT_RIM, width=2)
        for i in range(3):
            yy = by - 10 + i * 4
            cv.create_line(bx+6, yy, bx+bw-6, yy, fill="#7a4a1e", width=1)
        cv.create_line(bx+bw//2-5, by-6, bx+bw//2+38, by-34, fill=BOAT_OAR, width=3, capstyle="round")
        cv.create_oval(bx+bw//2+30, by-40, bx+bw//2+46, by-28, fill=BOAT_OAR, outline=BOAT_RIM)

        sup_side = self._sup_side()
        boat_at_left = (bx < 400)
        show_sup = self.animating or (boat_at_left and sup_side == "left") or (not boat_at_left and sup_side == "right")
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
            cv.create_oval(ox-16, by-32, ox+16, by-2, fill=col, outline="white", width=1)
            cv.create_text(ox, by-17, text=EMOJIS[item], font=("Arial", 15))

    def _draw_trees(self, cv, positions):
        for (x, y) in positions:
            cv.create_rectangle(x-3, y, x+3, y+20, fill="#4a3b2f", outline="")
            for offset, size in [(0, 15), (0, 25), (0, 35)]:
                cv.create_polygon(x, y-offset-5,
                                  x-size//2, y-offset-5+size*0.6,
                                  x+size//2, y-offset-5+size*0.6,
                                  fill="#2d6230", outline="#1b4720")

    def _canvas_click(self, event):
        if self.game_over:
            items = self.cv.find_withtag("tryagain_btn")
            for item in items:
                coords = self.cv.bbox(item)
                if coords and coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]:
                    self._reset()
                    return

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

    def _toggle_rules(self):
        self.rules_visible = not self.rules_visible
        if self.rules_visible:
            self.rules_lbl.pack(padx=20, pady=4)
            self.rules_btn.config(text="ℹ️  Hide Rules")
        else:
            self.rules_lbl.pack_forget()
            self.rules_btn.config(text="ℹ️  Show Rules")


if __name__ == "__main__":
    app = RiverGame()

    def _wave_tick():
        if not app.animating and not app.game_over:
            app._render()
        app.after(800, _wave_tick)

    app.after(800, _wave_tick)
    app.mainloop()