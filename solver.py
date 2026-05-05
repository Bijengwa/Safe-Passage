from collections import deque

START = (True, True, True, True)
GOAL  = (False, False, False, False)

NAMES = ["Supervisor", "Lion", "Goat", "Grass"]

def state_str(state):
    left = [NAMES[i] for i, v in enumerate(state) if v]
    right = [NAMES[i] for i, v in enumerate(state) if not v]
    return f"Left: {left} | Right: {right}"

def safe(state):
    s, l, g, gr = state

    if l == g and s != l:
        return False

    if g == gr and s != g:
        return False

    return True

def next_states(state):
    s, l, g, gr = state
    new_s = not s

    direction = "Right" if s else "Left"

    moves = []

    def try_move(desc, new_state):
        if safe(new_state):
            moves.append((desc, new_state))

    # Move alone
    try_move(f"Supervisor moves alone {direction}", (new_s, l, g, gr))

    # Move with lion
    if l == s:
        try_move(f"Supervisor takes Lion {direction}", (new_s, not l, g, gr))

    # Move with goat
    if g == s:
        try_move(f"Supervisor takes Goat {direction}", (new_s, l, not g, gr))

    # Move with grass
    if gr == s:
        try_move(f"Supervisor takes Grass {direction}", (new_s, l, g, not gr))

    return moves

def solve():
    q = deque([(START, [], [START])])
    seen = {START}

    while q:
        state, path, states_path = q.popleft()

        if state == GOAL:
            return path, states_path

        for move, nxt in next_states(state):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [move], states_path + [nxt]))

    return None, None

if __name__ == "__main__":
    solution, states = solve()

    if solution:

        for i in range(len(solution)):
            print(f"Step {i+1}: {solution[i]}")
            print(f"   {state_str(states[i+1])}\n")

    else:
        print("No solution exists.")