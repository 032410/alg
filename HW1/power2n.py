import sys
import time
from multiprocessing import Process, Queue

TIMEOUT = 5.0


# 方法 1：直接用 ** 運算子
def power2n_1(n):
    if n < 0:
        raise ValueError("n 必須 >= 0")
    return 2 ** n


# 方法 2a：用遞迴（左右兩邊各算一次）→ 呼叫次數 2^n，指數時間
def power2n_2a(n):
    if n < 0:
        raise ValueError("n 必須 >= 0")
    if n == 0:
        return 1
    # power2n_2a(n-1) + power2n_2a(n-1)
    return power2n_2a(n - 1) + power2n_2a(n - 1)


# 方法 2b：用遞迴（乘 2）→ n+1 層，線性時間，但會受遞迴深度限制
def power2n_2b(n):
    if n < 0:
        raise ValueError("n 必須 >= 0")
    if n == 0:
        return 1
    # 2 * power2n_2b(n-1)
    return 2 * power2n_2b(n - 1)


# 方法 3：用遞迴 + 查表（記憶化）→ 只呼叫 2n 次，線性時間
# 注意：只在函式外建表不夠，還要在函式內先查表，否則仍會呼叫 2^n 次
def power2n_3(n, table=None):
    if n < 0:
        raise ValueError("n 必須 >= 0")
    if table is None:
        table = [0] * (n + 1)
        table[0] = 1
        if n >= 1:
            table[1] = 2
    if n <= 1:
        return table[n]
    if table[n] == 0:  # if ...  還沒算過才遞迴，算過就直接查表
        table[n] = power2n_3(n - 1, table) + power2n_3(n - 1, table)
    return table[n]


def _worker(func, n, q):
    try:
        start = time.perf_counter()
        value = func(n)
        q.put(("ok", time.perf_counter() - start, value))
    except Exception as exc:
        q.put(("err", 0.0, f"{type(exc).__name__}: {exc}"))


def timed_call(func, n, timeout=TIMEOUT):
    """在獨立行程執行並加上逾時，避免指數時間的方法卡死主程式"""
    q = Queue()
    p = Process(target=_worker, args=(func, n, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return "timeout", timeout, None
    if q.empty():
        return "crash", 0.0, None
    return q.get()


def bench(func, n, repeat=2000):
    """在同一個行程重複計時，得到每次呼叫的平均耗時"""
    start = time.perf_counter()
    for _ in range(repeat):
        func(n)
    total = time.perf_counter() - start
    return total, total / repeat


def main():
    n = 100
    expected = 2 ** n
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"=" * 66)
    print(f"HW1  power2n   測試 n = {n}   (答案 {len(str(expected))}  位數)")
    print(f"Python {sys.version.split()[0]}   遞迴上限 sys.getrecursionlimit() = "
          f"{sys.getrecursionlimit()}")
    print("=" * 66)

    print("\n【1】四種方法在 n = 100 的速度比較")
    print(f"{'方法':<12}{'花費時間':>14}{'排序':>8}   說明")
    print("-" * 66)

    results = []
    for label, func in (("方法1 **", power2n_1),
                        ("方法2b 遞迴", power2n_2b),
                        ("方法3 查表", power2n_3)):
        total, each = bench(func, n)
        results.append((label, total, each))
        results.sort(key=lambda row: row[1])

    notes = {
        "方法1 **": "O(1) 層級，C 層大數運算",
        "方法2b 遞迴": "n+1 = 101 層 Python 遞迴",
        "方法3 查表": "n = 100 層，但只呼叫 200 次",
    }
    for rank, (label, total, each) in enumerate(results, 1):
        print(f"{label:<12}{total * 1000:>11.3f} ms{rank:>8}   "
              f"{notes[label]}（每次 {each * 1e6:.3f} us）")

    print("\n【2】方法 2a：指數時間，n = 100 跑不完")
    print(f"    n = 100 需要呼叫 2^100 ≈ {2 ** n:.3e} 次，就算每次只要 1 ns，")
    print("    光是呼叫本身也要花 10^22 年以上。")
    print("    實際用計時器驗證（逾時 %g 秒就放棄）：" % TIMEOUT)
    print(f"    {'n':>4}{'理論呼叫次數':>18}{'實測':>14}")
    print("    " + "-" * 36)
    for k in (10, 15, 20, 22, 24, 26, 30, 40, 100):
        status, elapsed, value = timed_call(power2n_2a, k)
        mark = f"{elapsed * 1000:.3f} ms" if status == "ok" else status
        ok = "" if status == "ok" else "  <- 超過 5 秒，放棄"
        calls = f"{2 ** k:,}" if k <= 40 else f"{2.0 ** k:.3e}"
        print(f"    {k:>4}{calls:>18}{mark:>14}{ok}")

    print("\n【3】誰算對？四種方法結果是否一致")
    print(f"    方法1 / 2b / 3 == 2**100 ? "
          f"{power2n_1(n) == power2n_2b(n) == power2n_3(n) == expected}")
    status, _, value = timed_call(power2n_2a, n, timeout=3.0)
    print(f"    方法2a 在 n = 100 : {status}")

    print("\n【4】另一個會出錯的地方：遞迴深度")
    for label, func in (("方法2b 遞迴", power2n_2b), ("方法3 查表", power2n_3)):
        status, _, value = timed_call(func, 5000, timeout=10.0)
        print(f"    {label} 在 n = 5000 (> 遞迴上限) : {value}")
    print(f"    方法1 在 n = 10000000 : "
          f"{power2n_1(10000000).bit_length()} 個 bit（沒有遞迴限制，照樣算得出來）")

    print("\n【結論】")
    print("    快：方法1（**）> 方法2b（遞迴乘 2）> 方法3（查表）")
    print("    慢到出不来：方法2a（指數時間），n = 100 需要 2^100 次呼叫")
    print("    呼叫次數：方法1 = 1 次、方法2b = n+1 次、方法3 = 2n 次、方法2a = 2^n 次")
    print("=" * 66)


if __name__ == "__main__":
    main()
