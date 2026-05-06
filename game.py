import tkinter as tk
from tkinter import messagebox

# ---------- Puzzle logic (same as your solver) ----------
START = (True, True, True, True)   # all on left
GOAL  = (False, False, False, False)

NAMES = ["Supervisor", "Lion", "Goat", "Grass"]

def safe(state):
    s, l, g, gr = state
    if l == g and s != l:
        return False
    if g == gr and s != g:
        return False
    return True

def next_states(state):
    """Get all possible safe moves from a state (used for hints later)."""
    s, l, g, gr = state
    new_s = not s
    moves = []

    def try_move(desc, new_state):
        if safe(new_state):
            moves.append((desc, new_state))

    try_move("Go alone", (new_s, l, g, gr))
    if l == s:
        try_move("Take Lion", (new_s, not l, g, gr))
    if g == s:
        try_move("Take Goat", (new_s, l, not g, gr))
    if gr == s:
        try_move("Take Grass", (new_s, l, g, not gr))

    return moves

# ---------- GUI ----------
class SafePassageGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Safe Passage – Lion, Goat & Grass")
        self.state = START        # current state
        self.move_count = 0

        # --- Display frames ---
        self.left_frame = tk.LabelFrame(root, text="Left Bank", padx=20, pady=20)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20)

        self.right_frame = tk.LabelFrame(root, text="Right Bank", padx=20, pady=20)
        self.right_frame.grid(row=0, column=2, padx=20, pady=20)

        # River image (just a label)
        self.river_label = tk.Label(root, text="🌊 RIVER 🌊", font=("Arial", 14))
        self.river_label.grid(row=0, column=1)

        # Labels for each character
        self.labels = {}
        for i, name in enumerate(NAMES):
            lbl_left = tk.Label(self.left_frame, text=name, font=("Arial", 12))
            lbl_left.pack(anchor="w")
            lbl_right = tk.Label(self.right_frame, text="", font=("Arial", 12))
            lbl_right.pack(anchor="w")
            self.labels[name] = (lbl_left, lbl_right)

        # --- Move buttons ---
        self.btn_frame = tk.Frame(root)
        self.btn_frame.grid(row=1, column=0, columnspan=3, pady=10)

        self.btn_alone = tk.Button(self.btn_frame, text="Go Alone", command=lambda: self.move(None))
        self.btn_alone.pack(side="left", padx=5)

        for item in ["Lion", "Goat", "Grass"]:
            btn = tk.Button(self.btn_frame, text=f"Take {item}",
                            command=lambda it=item: self.move(it))
            btn.pack(side="left", padx=5)

        # --- Message / status ---
        self.status_label = tk.Label(root, text="Make your move.", font=("Arial", 12))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=10)

        # --- Move counter ---
        self.counter_label = tk.Label(root, text="Moves: 0")
        self.counter_label.grid(row=3, column=0, columnspan=3)

        self.update_display()

    def update_display(self):
        """Refresh the left/right bank labels according to current state."""
        s, l, g, gr = self.state
        state_dict = {
            "Supervisor": s,
            "Lion": l,
            "Goat": g,
            "Grass": gr,
        }
        for name, is_left in state_dict.items():
            lbl_left, lbl_right = self.labels[name]
            if is_left:
                lbl_left.config(text=name)
                lbl_right.config(text="")
            else:
                lbl_left.config(text="")
                lbl_right.config(text=name)

        # Enable/disable buttons based on where supervisor is and which items are with them
        # (Always allow go alone)
        # For items: enabled only if the item is on the same bank as supervisor
        for btn, item in zip(self.btn_frame.winfo_children()[1:], ["Lion", "Goat", "Grass"]):
            if state_dict[item] == s:
                btn.config(state="normal")
            else:
                btn.config(state="disabled")

        self.counter_label.config(text=f"Moves: {self.move_count}")

    def move(self, item):
        """Attempt to move the supervisor, optionally with an item."""
        s, l, g, gr = self.state
        new_s = not s   # supervisor crosses

        if item is None:
            new_state = (new_s, l, g, gr)
            move_desc = "Go alone"
        elif item == "Lion":
            if l != s:
                self.status_label.config(text="Lion is not on this bank!")
                return
            new_state = (new_s, not l, g, gr)
            move_desc = "Take Lion"
        elif item == "Goat":
            if g != s:
                self.status_label.config(text="Goat is not on this bank!")
                return
            new_state = (new_s, l, not g, gr)
            move_desc = "Take Goat"
        elif item == "Grass":
            if gr != s:
                self.status_label.config(text="Grass is not on this bank!")
                return
            new_state = (new_s, l, g, not gr)
            move_desc = "Take Grass"
        else:
            return

        # Safety check
        if not safe(new_state):
            # Show warning and do NOT apply the move
            self.status_label.config(text="Danger! That move is unsafe. Try again.")
            return

        # Move accepted
        self.state = new_state
        self.move_count += 1
        self.update_display()

        # Win condition
        if self.state == GOAL:
            self.status_label.config(text=f"Congratulations! You solved it in {self.move_count} moves!")
            messagebox.showinfo("Safe Passage", f"You won in {self.move_count} moves!")
            self.root.quit()
        else:
            # Check if we are stuck (no safe moves) – not necessary but nice
            possible_moves = next_states(self.state)
            if not possible_moves:
                self.status_label.config(text="No safe moves left. You lost!")
                messagebox.showinfo("Safe Passage", "You're stuck! Refresh to try again.")
                # Optionally reset
            else:
                self.status_label.config(text="Safe move. Continue.")

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    game = SafePassageGame(root)
    root.mainloop()