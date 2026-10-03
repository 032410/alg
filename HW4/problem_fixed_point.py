"""HW4-1 用「迭代法」求解自訂問題：求 x^3 - x - 1 = 0 的實根。

問題選在 (1, 2) 區間，因為 f(x) = x^3 - x - 1 連續且 f(1) = -1 < 0、f(2) = 5 > 0，
由介值定理知該區間必有一個實根（此根稱為 plastic number / 塑膠常數）。

同一個問題可以寫出很多種「迭代式」，有的收斂、有的發散，收斂速度差很多，
這正是本章想說明的事：迭代法能不能用，取決於 |g'(x*)| 是否小於 1。
"""

import math
import sys

ALPHA = 1.3247179572447458  # 真值（塑膠常數），用來算誤差
TOL = 1e-12
MAX_ITER = 60
SHOW = 8  # 印出前幾步


def f(t):
    return t ** 3 - t - 1


# ---------------------------------------------------------------------------
# 各種迭代法：全部解同一個 x^3 - x - 1 = 0
# ---------------------------------------------------------------------------
def g1(x):
    """x^3 = x + 1  ->  g(x) = x + 1（最直觀的寫法，但會發散）"""
    return x + 1


def g2(x):
    """x^3 = x + 1  ->  g(x) = cbrt(x + 1)（線性收斂，慢但會收斂）"""
    return math.cbrt(x + 1)


def g3(x):
    """x^3 - x = 1  ->  x(x^2 - 1) = 1  ->  g(x) = 1 / (x^2 - 1)（會發散）"""
    return 1.0 / (x * x - 1.0)


def g4(x):
    """牛頓法：x - f(x)/f'(x)，二次收斂"""
    return x - f(x) / (3 * x * x - 1)


def _grow(step, values, count):
    """從 values 最後一項開始反覆套用 step，直到湊滿 count 項"""
    while len(values) < count:
        values.append(step(values[-1]))
    return values


def seq_from(g, start):
    """單一函數 g 組成的迭代序列"""
    return _grow(g, [start], SHOW)


def seq_secant(x0, x1, count):
    """真正的割線法：用最近兩點決定斜率（階數約 1.618）"""
    values = [x0, x1]
    while len(values) < count:
        a, b = values[-2], values[-1]
        values.append(b - f(b) * (b - a) / (f(b) - f(a)))
    return values


def run_single(g, x0, tol=TOL, max_iter=MAX_ITER):
    """單一函數 g 的迭代跑到收斂為止"""
    x = x0
    for k in range(1, max_iter + 1):
        try:
            nxt = g(x)
        except (ValueError, ZeroDivisionError, OverflowError):
            return False, k, x
        if not math.isfinite(nxt):
            return False, k, nxt
        if abs(nxt - x) < tol:
            return True, k, nxt
        x = nxt
    return False, max_iter, x


def run_secant(x0, x1, tol=TOL, max_iter=MAX_ITER):
    a, b = x0, x1
    for k in range(2, max_iter + 1):
        try:
            nxt = b - f(b) * (b - a) / (f(b) - f(a))
        except (ValueError, ZeroDivisionError, OverflowError):
            return False, k, b
        if not math.isfinite(nxt):
            return False, k, nxt
        if abs(nxt - b) < tol:
            return True, k - 1, nxt
        a, b = b, nxt
    return False, max_iter, b


METHODS = [
    # 名稱, 起始值, 產生前 SHOW 步, 跑到收斂, 改造自, |g'(alpha)| 文字
    ("g1 x+1", 1.0, lambda s: seq_from(g1, s), lambda: run_single(g1, 1.0),
     "x^3 = x+1", "1.0000"),
    ("g2 cbrt(x+1)", 1.0, lambda s: seq_from(g2, s), lambda: run_single(g2, 1.0),
     "x^3 = x+1", "0.1899"),
    ("g3 1/(x^2-1)", 1.5, lambda s: seq_from(g3, s), lambda: run_single(g3, 1.5),
     "x(x^2-1)=1", "4.6494"),
    ("g4 牛頓法", 1.0, lambda s: seq_from(g4, s), lambda: run_single(g4, 1.0),
     "x - f/f'", "0（極小）"),
    ("g5 割線法", 1.0, lambda s: seq_secant(1.5, s, SHOW), lambda: run_secant(1.5, 1.0),
     "割線法", "0（但無導數）"),
]


def collect_errors(seq):
    return [abs(v - ALPHA) for v in seq]


def estimate_order(errors):
    """用連續三個誤差估收斂階數 p：e_{k+1} ≈ C · e_k^p，取中位數較穩"""
    ps = []
    for i in range(1, len(errors) - 1):
        e1, e2, e3 = errors[i - 1], errors[i], errors[i + 1]
        if e1 <= 0 or e2 <= 0 or e3 <= 0 or e3 < 1e-14:
            continue
        if e1 == e2:
            continue
        ps.append(math.log(e3 / e2) / math.log(e2 / e1))
    if not ps:
        return float("nan")
    return sorted(ps)[len(ps) // 2]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 82)
    print("HW4-1  迭代法求解：x^3 - x - 1 = 0  (區間 (1, 2) 的實根)")
    print(f"真值（塑膠常數）alpha = {ALPHA}")
    print("初始值：g1~g4、g5 從 1.0 開始；g3 用 1.5 避開 1/(1-1)、g5 固定點用 1.5")
    print("=" * 82)

    # 第一步：各種迭代式的前 8 步並排比較（對應題目範例三種 x 並排印的寫法）
    print(f"\n【第一步】各種迭代式的前 {SHOW} 步")
    header = "  k  " + "".join(f"{name:>18}" for name, *_ in METHODS)
    print(header)
    print("  " + "-" * (len(header) - 2))
    sequences = [make_seq(start) for _, start, make_seq, _, _, _ in METHODS]
    for k in range(SHOW):
        row = f"  {k:>2}  "
        for seq in sequences:
            value = seq[k]
            row += f"{value:>18.10f}" if isinstance(value, float) and math.isfinite(value) \
                else f"{value!s:>18}"
        print(row)

    # 第二步：收斂性與速度比較
    print(f"\n【第二步】收斂性與速度（|x_(k+1) - x_k| < {TOL:g} 就停）")
    print(f"  {'迭代式':<16}{'改造自':<14}{'|g\'(a)|':>11}{'收斂':>5}"
          f"{'次數':>5}{'誤差':>12}{'階數 p':>8}")
    print("  " + "-" * 70)
    for (name, _, _, run, origin, slope), seq in zip(METHODS, sequences):
        converged, steps, x = run()
        order = estimate_order(collect_errors(seq + [x] * 2)) if converged else float("nan")
        order_txt = "—" if math.isnan(order) else f"{order:.3f}"
        print(f"  {name:<16}{origin:<14}{slope:>11}{'是' if converged else '否':>5}"
              f"{steps:>5}{abs(x - ALPHA):>12.3e}{order_txt:>8}")

    # 第三步：結論
    print("\n【第三步】結論")
    print("  1. g1 x+1        |g'| = 1，每步固定加 1 → 永遠到不了根，發散")
    print("  2. g2 cbrt(x+1)  |g'| = 0.19 < 1 → 收斂，但階數只有 1，需要 17 步")
    print("  3. g3 1/(x^2-1)  |g'| = 4.65 > 1 → 在根附近被推開，發散")
    print("  4. g4 牛頓法     |g'(alpha)| = 0 → 二次收斂，6 步就到位")
    print("  5. g5 割線法     不用導數，階數約 1.618（黃金比例），比牛頓法慢")
    print()
    print("  重點一：同一個方程可以寫出很多迭代式，只有 |g'(x*)| < 1 才會收斂，")
    print("          |g'(x*)| > 1 會被推開、|g'(x*)| = 1 可能停滯或震盪。")
    print("  重點二：|g'(x*)| = 0 代表誤差被平方，牛頓法就是把一次收斂升級成二次收斂。")
    print("  重點三：收斂階數 p 決定速度，誤差要小 n 位時，步數約為 log(n)/log(p)。")
    print("=" * 82)

    converged, steps, x = run_single(g4, 1.0)
    print(f"\n答案：x = {x:.15f}（牛頓法 {steps} 步，與真值差 {abs(x - ALPHA):.2e}）")


if __name__ == "__main__":
    main()
