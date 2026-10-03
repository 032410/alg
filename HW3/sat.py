"""SAT 求解器：用「系統性列舉真值表」找出所有滿足解 (models)。

用法:
    python sat.py "(a & b) | ~c"
    python sat.py "NOT (a AND b) OR c" --all
    python sat.py --demo
"""

import argparse
import re
import sys
import time

KEYWORDS = [(r"\bAND\b", "&&"), (r"\bOR\b", "||"), (r"\bXOR\b", "^"),
            (r"\bNOT\b", "!"), (r"\bTRUE\b", "1"), (r"\bFALSE\b", "0")]

TOKEN_RE = re.compile(r"""
      (?P<lpar>\()
    | (?P<rpar>\))
    | (?P<op>&&|\|\||[!~^&|])
    | (?P<num>\d+)
    | (?P<var>[A-Za-z_][A-Za-z_0-9]*)
    | (?P<bad>\S)
""", re.VERBOSE)


class ParseError(Exception):
    pass


def tokenize(text):
    tokens, pos = [], 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        match = TOKEN_RE.match(text, pos)
        if match is None:
            raise ParseError(f"第 {pos} 個字元 '{text[pos]}' 不合法")
        kind = match.lastgroup
        if kind == "bad":
            raise ParseError(f"不认识的符號 '{match.group()}'（位置 {pos}）")
        tokens.append((kind, match.group()))
        pos = match.end()
    return tokens


class Parser:
    """遞迴下降解析：expr := term ('|' term)* ; term := factor ('&' factor)*"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def eat(self, kind, text=None):
        k, t = self.peek()
        if k == kind and (text is None or t == text):
            self.pos += 1
            return t
        return None

    def parse(self):
        node = self.expr()
        if self.pos != len(self.tokens):
            raise ParseError(f"多餘的 token：{self.tokens[self.pos:]}")
        return node

    def expr(self):
        node = self.term()
        while True:
            if self.eat("op", "|") or self.eat("op", "||"):
                node = ("or", node, self.term())
            elif self.eat("op", "^"):
                node = ("xor", node, self.term())
            else:
                return node

    def term(self):
        node = self.factor()
        while self.eat("op", "&") or self.eat("op", "&&"):
            node = ("and", node, self.factor())
        return node

    def factor(self):
        if self.eat("op", "!") or self.eat("op", "~"):
            return ("not", self.factor())
        if self.eat("lpar"):
            node = self.expr()
            if not self.eat("rpar"):
                raise ParseError("缺少右括號 )")
            return node
        kind, text = self.peek()
        if kind == "var":
            self.pos += 1
            return ("var", text)
        if kind == "num":
            self.pos += 1
            return ("const", int(text))
        if kind is None:
            raise ParseError("公式意外結束")
        raise ParseError(f"不該出現的 token {text!r}")


def parse_formula(text):
    for pattern, replacement in KEYWORDS:
        text = re.sub(pattern, replacement, text)
    return Parser(tokenize(text)).parse()


def collect_variables(node, found=None):
    """依公式中出現的順序收集變數（dict 保持插入順序）"""
    if found is None:
        found = {}
    kind = node[0]
    if kind == "var":
        found.setdefault(node[1], None)
    elif kind == "not":
        collect_variables(node[1], found)
    elif kind == "const":
        pass
    else:
        collect_variables(node[1], found)
        collect_variables(node[2], found)
    return found


def evaluate(node, env):
    """逐列求值：回傳 True / False"""
    kind = node[0]
    if kind == "const":
        return bool(node[1])
    if kind == "var":
        return env[node[1]]
    if kind == "not":
        return not evaluate(node[1], env)
    if kind == "and":
        return evaluate(node[1], env) and evaluate(node[2], env)
    if kind == "or":
        return evaluate(node[1], env) or evaluate(node[2], env)
    if kind == "xor":
        return evaluate(node[1], env) != evaluate(node[2], env)
    raise ParseError(f"不支援的節點 {kind}")


def assignment_of(index, variables):
    """第 index 列的真值指派：第 i 個變數取 (index >> i) & 1"""
    return {name: bool(index >> i & 1) for i, name in enumerate(variables)}


def format_assignment(env, order):
    return "".join("1" if env[name] else "0" for name in order)


def column_bits(var_index, rows):
    """用一個大整數存整欄真值表：bit r = 該變數在第 r 列的值（bit-parallel）"""
    width = 1 << var_index
    column = ((1 << width) - 1) << width      # 低 width 個 bit = 0，高 width 個 bit = 1
    shift = width * 2
    while shift < rows:
        column |= column << shift
        shift *= 2
    return column


def evaluate_bitmap(node, columns, mask):
    """整份真值表一次算完：回傳 2^n bits，bit r = 公式在第 r 列的值"""
    kind = node[0]
    if kind == "const":
        return mask if node[1] else 0
    if kind == "var":
        return columns[node[1]]
    if kind == "not":
        return ~evaluate_bitmap(node[1], columns, mask) & mask
    left = evaluate_bitmap(node[1], columns, mask)
    if kind == "and":
        return left & evaluate_bitmap(node[2], columns, mask)
    right = evaluate_bitmap(node[2], columns, mask)
    if kind == "or":
        return left | right
    if kind == "xor":
        return left ^ right
    raise ParseError(f"不支援的節點 {kind}")


def set_bits(bitmap, rows):
    """取出所有為 1 的 bit 編號；用位元組掃描，避免逐 bit shift 造成 O(rows^2)"""
    models = []
    data = bitmap.to_bytes((rows + 7) // 8, "little")
    for index, byte in enumerate(data):
        if byte:
            base = index * 8
            for bit in range(8):
                if byte >> bit & 1:
                    models.append(base + bit)
    return models


def print_truth_table(node, variables, rows, bitmap, limit):
    if rows > limit:
        print(f"  （{rows} 列超過 {limit} 列，不列印；用 --all 強制全部列印）")
        return
    header = "  列  " + "".join(f"{name:>4}" for name in variables) + "  |  結果"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in range(rows):
        env = assignment_of(r, variables)
        cells = "".join(f"{'1' if env[name] else '0':>4}" for name in variables)
        mark = "1" if (bitmap >> r) & 1 else "0"
        print(f"  {r:>3}  {cells}  |   {mark}   {'<- 滿足解' if mark == '1' else ''}")


def brute_force_solve(text, show_all=False, table_limit=64, max_models=20):
    start = time.perf_counter()
    node = parse_formula(text)
    variables = list(collect_variables(node))
    n = len(variables)
    rows = 1 << n
    mask = (1 << rows) - 1

    print("=" * 72)
    print(f"公式：{text}")
    print(f"變數（{n} 個）：{', '.join(variables) if variables else '（無）'}")
    print(f"真值表列數 = 2^{n} = {rows:,}")
    print("=" * 72)

    if rows > table_limit:
        print(f"\n  2^{n} = {rows:,} 列太多，表格不列印（超過 {table_limit} 列）")

    columns = {name: column_bits(i, rows) for i, name in enumerate(variables)}
    bitmap = evaluate_bitmap(node, columns, mask)
    models = set_bits(bitmap, rows)
    elapsed = time.perf_counter() - start

    print("\n【真值表】第 i 個變數對應位元 i（0 = 假，1 = 真）")
    print_truth_table(node, variables, rows, bitmap,
                      rows if show_all else table_limit)

    # 用最笨的逐列 enumerate 再算一次，確認結果一致
    verified = None
    if rows <= 65536:
        verified = []
        for r in range(rows):
            env = assignment_of(r, variables)
            if evaluate(node, env):
                verified.append(r)

    print("\n【結果】")
    if not models:
        print("  UNSAT —— 沒有任何指派能讓公式為真。")
    else:
        print(f"  SAT —— 共有 {len(models):,} 組滿足解（全部都要 SAT 才算 UNSAT）")
        shown = models if show_all else models[:max_models]
        print(f"  {'列':>6}  {'指派':<10} 為真的變數")
        for r in shown:
            env = assignment_of(r, variables)
            trues = [name for name in variables if env[name]]
            print(f"  {r:>6}  {format_assignment(env, variables):<10} "
                  f"{', '.join(trues) if trues else '（無）'}")
        if len(models) > len(shown):
            print(f"  ... 還有 {len(models) - len(shown):,} 組（用 --all 全部列出）")

    if verified is not None:
        same = verified == models
        print(f"\n【驗證】逐列 enumerate 的結果與真值表一致：{same}")
    print(f"【時間】{elapsed * 1000:.3f} ms（{rows:,} 列）")
    print("=" * 72)
    return models


DEMOS = [
    "a & b",
    "a | ~a",
    "(a & b) | (~a & c)",
    "(a | b) & (a | ~b) & (~a | b)",
    "(a & ~b) | (b & ~c) | (c & ~a)",
]


def main():
    parser = argparse.ArgumentParser(description="以列舉真值表的方式求解 SAT 問題")
    parser.add_argument("formula", nargs="?", help="布林公式，例如 \"(a & b) | ~c\"")
    parser.add_argument("--all", action="store_true", help="列印全部真值表與全部滿足解")
    parser.add_argument("--demo", action="store_true", help="跑內建的 5 個範例")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if args.demo or not args.formula:
        for demo in DEMOS:
            brute_force_solve(demo)
            print()
        return

    try:
        brute_force_solve(args.formula, show_all=args.all)
    except ParseError as exc:
        print(f"公式語法錯誤：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
