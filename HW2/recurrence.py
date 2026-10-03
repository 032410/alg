import math
import sys

# 四個遞迴式的定義（照題目寫，用最直覺的遞迴）
def t1(n):  # T(n) = T(n-1) + 8,  T(1) = 1
    return 1 if n <= 1 else t1(n - 1) + 8


def t2(n):  # T(n) = 2 T(n-1) + 9,  T(1) = 1
    return 1 if n <= 1 else 2 * t2(n - 1) + 9


def t3(n):  # T(n) = 2 T(n/2) + 1,  T(1) = 1
    return 1 if n <= 1 else 2 * t3(n // 2) + 1


def t4(n):  # T(n) = T(n/2) + 1,  T(1) = 1
    return 1 if n <= 1 else t4(n // 2) + 1


# 同一個遞迴式改用迴圈算，n 很大時才不會爆遞迴深度
def t1_iter(n):
    t = 1
    for _ in range(n - 1):
        t += 8
    return t


def t2_iter(n):
    t = 1
    for _ in range(n - 1):
        t = 2 * t + 9
    return t


# 對應的精確解（通解）
def c1(n):
    return 8 * n - 7


def c2(n):
    return 5 * 2 ** n - 9


def c3(n):
    return 2 * n - 1


def c4(n):
    return math.log2(n) + 1


CASES = [
    ("T(n) = T(n-1) + 8", t1, c1, "8n - 7", "Theta(n)"),
    ("T(n) = 2T(n-1) + 9", t2, c2, "5*2^n - 9", "Theta(2^n)"),
    ("T(n) = 2T(n/2) + 1", t3, c3, "2n - 1", "Theta(n)"),
    ("T(n) = T(n/2) + 1", t4, c4, "log2(n) + 1", "Theta(log n)"),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=" * 72)
    print("HW2  遞迴式：精確解與 Big O")
    print("=" * 72)

    for title, rec, closed, formula, bigo in CASES:
        print(f"\n【{title}】  精確解 = {formula}   {bigo}")
        print(f"  {'n':>10}{'遞迴算出來':>22}{'精確解':>22}{'相符':>8}")
        print("  " + "-" * 62)
        for n in (1, 2, 4, 8, 16, 32, 64):
            if rec is t2 and n > 16:
                break
            a = rec(n)
            b = closed(n)
            same = abs(a - b) < 1e-9
            b_txt = f"{b:.4f}" if isinstance(b, float) else str(b)
            print(f"  {n:>10}{a:>22}{b_txt:>22}{'OK' if same else 'X':>8}")

    print("\n" + "=" * 72)
    print("Big O 驗證：看 T(n) 除以成長項後是否收斂成常數")
    print("  收斂成常數 = 剛好這個複雜度（Theta）；一直暴增 = 估得太小")
    print("-" * 72)
    print(f"  {'n':>10}{'#1 T(n)/n':>14}{'#2 T(n)/2^n':>14}"
          f"{'#3 T(n)/n':>14}{'#4 T(n)/log2(n)':>18}")
    print("  " + "-" * 70)
    for k in (4, 8, 12, 16):
        n = 2 ** k
        m = min(n, 20)
        r1 = t1_iter(n) / n
        r2 = t2_iter(m) / 2 ** m
        r3 = t3(n) / n
        r4 = t4(n) / math.log2(n)
        print(f"  {n:>10}{r1:>14.4f}{r2:>14.4f}{r3:>14.4f}{r4:>18.4f}")
    print(f"  （#2 的 n 只算到 {m}，因為 2^20 ≈ 100 萬次，再大就爆時間）")
    print("=" * 72)

    print("\n總結")
    print("  #1 T(n) = 8n - 7          = Theta(n)")
    print("  #2 T(n) = 5*2^n - 9       = Theta(2^n)")
    print("  #3 T(n) = 2n - 1          = Theta(n)")
    print("  #4 T(n) = log2(n) + 1     = Theta(log n)")


if __name__ == "__main__":
    main()
