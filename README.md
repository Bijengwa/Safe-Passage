# Safe-Passage

**AI river-crossing puzzle solver** – Lion, Goat & Grass.

The supervisor must get the lion, the goat, and the grass across the river safely.  
The boat carries only the supervisor and one passenger at a time.  
The AI uses **breadth‑first search (BFS)** to discover the shortest solution entirely by itself — no moves are hard‑coded.

---

##  How the AI works (brief)

1. **State representation** – a tuple `(supervisor, lion, goat, grass)` where `True` means “on the left bank”.
2. **Moves** – The supervisor can cross alone or take one item that is on the same bank.
3. **Safety check** – After each move, the AI verifies:
   - Lion & goat left alone → goat gets eaten ❌
   - Goat & grass left alone → grass gets eaten ❌
   - Supervisor present → safe ✅
4. **Search** – BFS explores all legal states until it reaches the goal: everything on the right bank `(False, False, False, False)`. The shortest path is returned.

---

##  Prerequisites

- **Python 3.7+** (tested with Python 3.14)  
  Check your version:
  ```bash
  python --version
