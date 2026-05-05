from collections import deque

# State: (supervisor, lion, goat, grass) – True = on left bank
START = (True, True, True, True)
GOAL  = (False, False, False, False)

def safe(state):
    s, l, g, gr = state
    # lion eats goat if left alone without supervisor
    if l == g and s != l:
        return False
    # goat eats grass if left alone without supervisor
    if g == gr and s != g:
        return False
    return True

def next_states(state):
    s, l, g, gr = state
    new_s = not s   # supervisor always moves to the opposite bank

    # Determine direction and phrasing
    if s is True:   # currently on left, moving to right
        direction = "crosses to the right"
    else:           # currently on right, moving to left
        direction = "returns to the left"

    moves = []

    # Supervisor moves alone
    new_state = (new_s, l, g, gr)
    if safe(new_state):
        moves.append((f"Supervisor {direction} alone", new_state))

    # Supervisor takes lion (if on same bank)
    if l == s:
        new_state = (new_s, not l, g, gr)
        if safe(new_state):
            moves.append((f"Supervisor {direction} with the lion", new_state))

    # Supervisor takes goat
    if g == s:
        new_state = (new_s, l, not g, gr)
        if safe(new_state):
            moves.append((f"Supervisor {direction} with the goat", new_state))

    # Supervisor takes grass
    if gr == s:
        new_state = (new_s, l, g, not gr)
        if safe(new_state):
            moves.append((f"Supervisor {direction} with the grass", new_state))

    return moves

def solve():
    q = deque([(START, [])])
    seen = {START}
    while q:
        st, path = q.popleft()
        if st == GOAL:
            return path
        for move, nxt in next_states(st):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [move]))
    return None

if __name__ == "__main__":
    sol = solve()
    if sol:
        print(" SafePassage AI – solution found:\n")
        for i, step in enumerate(sol, 1):
            print(f"  {i}. {step}")
    else:
        print("No solution exists.")