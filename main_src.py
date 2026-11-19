import json, os, sys, urllib.request as u

# Chess engine: fetches the server base URL from the environment
# (used to call /game and /move).

E = os.environ.get("MAKEFUN_ENV_URL", "")

N, S = 10, -10

ND = (21, 19, 12, 8, -8, -12, -19, -21)
KD = (N, S, 1, -1, N + 1, N - 1, S + 1, S - 1)
BD = (N + 1, N - 1, S + 1, S - 1)
RD = (N, S, 1, -1)

MV = {
    'P': (N, 2 * N, N + 1, N - 1),
    'p': (S, 2 * S, S + 1, S - 1),
    'N': ND, 'n': ND,
    'B': BD, 'b': BD,
    'R': RD, 'r': RD,
    'Q': KD, 'q': KD,
    'K': KD, 'k': KD,
}

V = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900,
}

AL = "0123456789abcdefghijklmnopqrstuvwxyz"

T = {
    'E': ("077777707aehhea77eorroe77eruure77eruure77eorroe77aehhea707aaaa70", 17, 3),
    'P': ("aaaaaaaacff00ffcc85aa58caaakkaaaccfmmfccffkppkffzzzzzzzzaaaaaaaa", 10, 2),
    'N': ("05aaaa505fprrpf5aruxxuraapxzzxpaarxzzxraapuxxupa5fppppf505aaaa50", 25, 2),
    'B': ("0aaaaaa0apkkkkpaauuuuuuaakuuuukaappuuppaakpuupkaakkkkkka0aaaaaa0", 20, 1),
    'R': ("555aa55500000000000000000000000000000000affffffa5555555555555555", 5, 1),
    'Q': ("0aaaaaa0apkkkkpaauuuuuuaakuuuukaappuuppaakpuupkaakkkkkka0aaaaaa0", 20, 1),
    'K': ("74400447744004477440044774400447a774477aeaaaaaaeoohhhhooorkhhkro", 17, 3),
}


def q(c, s):
    r = s // 10 - 2
    f = s % 10 - 1
    if c.islower():
        r = 7 - r
    t = T[c.upper()]
    return t[2] * (AL.index(t[0][r * 8 + f]) - t[1])


def P(fen):
    p = fen.split()
    B = [' '] * 120
    for r in range(2, 10):
        B[r * 10 + 1:r * 10 + 9] = ['.'] * 8
    r = 9
    for w in p[0].split('/'):
        f = 1
        for c in w:
            if c.isdigit():
                f += int(c)
            else:
                B[r * 10 + f] = c
                f += 1
        r -= 1
    ep = 0
    if p[3] != '-':
        ep = (int(p[3][1]) + 1) * 10 + ord(p[3][0]) - 96
    return B, p[1] == 'w', p[2], ep


def A(B, s, w):
    if w:
        if 'P' in (B[s - 11], B[s - 9]):
            return 1
    elif 'p' in (B[s + 11], B[s + 9]):
        return 1
    n = ('n', 'N')[w]
    k = ('k', 'K')[w]
    for d in ND:
        if B[s + d] == n:
            return 1
    for d in KD:
        if B[s + d] == k:
            return 1
    for d in BD + RD:
        t = s + d
        while B[t] == '.':
            t += d
        c = B[t]
        if c == ('q', 'Q')[w] or (d in BD and c == ('b', 'B')[w]) or (d in RD and c == ('r', 'R')[w]):
            return 1
    return 0


def G(p, cp=0):
    B, w, ca, ep = p
    M = []
    for s in range(21, 99):
        c = B[s]
        if c in '. ' or c.isupper() != w:
            continue
        if c in 'Pp':
            d = N if w else S
            pr = 'q' if (s + d) // 10 == (9 if w else 2) else ''
            if B[s + d] == '.':
                M.append((s, s + d, pr))
                if not cp and s // 10 == (3 if w else 8) and B[s + 2 * d] == '.':
                    M.append((s, s + 2 * d, ''))
            for e in (d + 1, d - 1):
                t = s + e
                b = B[t]
                if b not in '. ' and b.isupper() != w:
                    M.append((s, t, 'q' if t // 10 == (9 if w else 2) else ''))
                elif ep and t == ep:
                    M.append((s, t, ''))
        elif c in 'NnKk':
            for d in MV[c]:
                t = s + d
                b = B[t]
                if b != ' ' and ((b == '.' and not cp) or b.isupper() != w):
                    M.append((s, t, ''))
        else:
            for d in MV[c]:
                t = s + d
                while B[t] == '.':
                    if not cp:
                        M.append((s, t, ''))
                    t += d
                b = B[t]
                if b != ' ' and b.isupper() != w:
                    M.append((s, t, ''))
    if cp:
        return M
    if w and B[25] == 'K':
        if 'K' in ca and B[26] + B[27] == '..' and not A(B, 25, 0) and not A(B, 26, 0):
            M.append((25, 27, ''))
        if 'Q' in ca and B[25] == 'K' and B[24] + B[23] + B[22] == '...' and not A(B, 25, 0) and not A(B, 24, 0):
            M.append((25, 23, ''))
    if not w and B[95] == 'k':
        if 'k' in ca and B[96] + B[97] == '..' and not A(B, 95, 1) and not A(B, 96, 1):
            M.append((95, 97, ''))
        if 'q' in ca and B[94] + B[93] + B[92] == '...' and not A(B, 95, 1) and not A(B, 94, 1):
            M.append((95, 93, ''))
    return M


def K(p, m):
    B, w, ca, ep = p
    s, t, pr = m
    B = B[:]
    c = B[s]
    e2 = 0
    if c in 'Kk':
        ca = ca.replace('K', '').replace('Q', '') if w else ca.replace('k', '').replace('q', '')
        if abs(t - s) == 2:
            if t > s:
                B[s + 1] = B[s + 3]
                B[s + 3] = '.'
            else:
                B[s - 1] = B[s - 4]
                B[s - 4] = '.'
    elif c in 'Pp':
        if t == ep:
            B[t + (S if w else N)] = '.'
        if abs(t - s) == 20:
            e2 = (s + t) // 2
    if B[t] in 'Kk':
        return None
    B[t] = (pr.upper() if w else pr) if pr else c
    B[s] = '.'
    for a, b in (21, 'Q'), (28, 'K'), (91, 'q'), (98, 'k'):
        if s == a or t == a:
            ca = ca.replace(b, '')
    return B, not w, ca, e2


KM = T['K']


def W(p):
    T['K'] = KM if 'Q' in p[0] or 'q' in p[0] else T['E']
    s = 0
    for i in range(21, 99):
        c = p[0][i]
        if c in V:
            s += V[c] + (q(c, i) if c.isupper() else -q(c, i))
    return s if p[1] else -s


def Y(p):
    return ''.join(p[0]), p[1], p[2], p[3]


NB = 400000
Z = [0]


def Q(p, a, b, d=0):
    Z[0] += 1
    if Z[0] > NB or d > 5:
        return W(p)
    s = W(p)
    if s >= b:
        return s
    if s > a:
        a = s
    for m in G(p, 1):
        if s + abs(V.get(p[0][m[1]], 0)) + 250 <= a:
            continue
        if abs(V.get(p[0][m[1]], 0)) + 60 < abs(V.get(p[0][m[0]], 0)):
            continue
        n = K(p, m)
        if not n:
            continue
        if A(n[0], n[0].index('K' if p[1] else 'k'), not p[1]):
            continue
        v = -Q(n, -b, -a, d + 1)
        if v > a:
            a = v
        if a >= b:
            break
    return a


KI = {}
HI = {}


def R(p, d, a, b, h):
    Z[0] += 1
    if Z[0] > NB:
        return W(p)
    if 'K' not in p[0]:
        return 9000 - d
    if 'k' not in p[0]:
        return -9000 + d
    ic = A(p[0], p[0].index('K' if p[1] else 'k'), not p[1])
    if d < 1:
        if ic:
            d = 1
        else:
            return Q(p, a, b)
    km = KI.get(d)
    if d > 2 and not ic:
        if -R((p[0], not p[1], p[2], 0), d - 3, -b, -b + 1, h) >= b:
            return b
    M = G(p)
    M.sort(key=lambda m: -abs(V.get(p[0][m[1]], 0)) * 10
            + abs(V.get(p[0][m[0]], 0)) // 10
            + (900 if m == km else 0)
            - HI.get(m[0] * 120 + m[1], 0))
    ok = 0
    bs = -1 << 30
    for m in M:
        n = K(p, m)
        if not n:
            continue
        if A(n[0], n[0].index('K' if p[1] else 'k'), not p[1]):
            continue
        ok = 1
        s = (25 if Y(n) in h else 0) - R(n, d - 1, -b, -a, h)
        if s > bs:
            bs = s
        if bs > a:
            a = bs
        if a >= b:
            if p[0][m[1]] == '.':
                KI[d] = m
                HI[m[0] * 120 + m[1]] = HI.get(m[0] * 120 + m[1], 0) + d * d
            break
    if not ok:
        return (-99999 - d) if ic else 0
    return bs


def C(m):
    return "abcdefgh"[m[0] % 10 - 1] + str(m[0] // 10 - 1) \
        + "abcdefgh"[m[1] % 10 - 1] + str(m[1] // 10 - 1) + m[2]


def X(fen, h, lg):
    p = P(fen)
    Z[0] = 0
    R0 = []
    for m in G(p):
        n = K(p, m)
        if C(m) in lg and not A(n[0], n[0].index('K' if p[1] else 'k'), not p[1]):
            R0.append((0, m))
    if not R0:
        return lg[0]
    bm = R0[0][1]
    for d in range(1, 8):
        sc = []
        a = -1 << 30
        for _, m in R0:
            n = K(p, m)
            v = (60 if Y(n) in h else 0) - R(n, d - 1, a, 1 << 30, h)
            if v > a and a > -1 << 30:
                v = (60 if Y(n) in h else 0) - R(n, d - 1, -1 << 30, 1 << 30, h)
            sc.append((v, m))
            if v > a:
                a = v
        if Z[0] > NB:
            break
        sc.sort(key=lambda x: -x[0])
        R0 = [(0, m) for _, m in sc]
        bm = sc[0][1]
        if Z[0] > NB * 3 // 4:
            break
    return C(bm)


def O(p, b):
    r = u.Request(E + p, data=json.dumps(b).encode(), headers={"content-type": "application/json"})
    with u.urlopen(r) as z:
        return json.load(z)


if __name__ == "__main__":
    if not E:
        sys.exit("MAKEFUN_ENV_URL is not set")
    while 1:
        g = O("/game", {})
        if g["status"] == "done":
            break
        h = {Y(P(g["fen"])): 1}
        while g["status"] == "your_move":
            try:
                m = X(g["fen"], h, g["legal_moves"])
            except Exception:
                m = g["legal_moves"][0]
            g = O("/move", {"game": g["game"], "move": m})
            if g["status"] != "done":
                y = Y(P(g["fen"]))
                h[y] = h.get(y, 0) + 1
        print(g["game"], g["outcome"], g["reason"], file=sys.stderr)
    print(g.get("wins"), g.get("draws"), g.get("losses"), file=sys.stderr)
