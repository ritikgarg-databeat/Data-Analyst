"""A real (not simulated) spreadsheet formula engine — the lightweight
"spreadsheet lab" spec section 13 asks for instead of a full Excel clone.

Covers cell references (same-sheet and `Sheet!A1` cross-sheet), ranges
(`A1:B10`), arithmetic (`+ - * / ^`), string concatenation (`&`), comparisons
(`= <> < > <= >=`), and a real, bounded function set: SUM, AVERAGE, COUNT,
COUNTA, MIN, MAX, ROUND, ABS, IF, IFERROR, AND, OR, NOT, SUMIF, SUMIFS,
COUNTIF, COUNTIFS, AVERAGEIF, VLOOKUP, INDEX, MATCH, XLOOKUP, CONCATENATE,
CONCAT, UPPER, LOWER, TRIM, LEN, LEFT, RIGHT, MID, TEXT, YEAR, MONTH, DAY,
DATE, TODAY, DATEDIF — deliberately NOT the whole Excel function library.

A `Workbook` is `dict[sheet_name, dict[cell_ref, raw_string]]`. Raw strings
are either a literal (`"42"`, `"Widget"`, `"TRUE"`) or a formula starting
with `=`. `evaluate_workbook` resolves every cell (recursively, following
references, with memoization and circular-reference detection) into a fully
computed `dict[sheet_name, dict[cell_ref, ExcelValue]]` — real evaluation,
not a hand-authored "expected output" the student's answer is text-matched
against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

Workbook = dict[str, dict[str, str]]
ExcelValue = float | str | bool | None
EvaluatedWorkbook = dict[str, dict[str, ExcelValue]]

_CELL_RE = re.compile(r"^\$?([A-Za-z]{1,3})\$?([0-9]+)$")
_EPOCH = date(1899, 12, 30)  # Excel's serial-date epoch (accounts for its leap-year bug)

_ERRORS = frozenset({"#DIV/0!", "#VALUE!", "#N/A", "#REF!", "#NAME?", "#CIRCULAR!", "#NUM!"})


class FormulaError(Exception):
    """Raised internally to unwind to the nearest IFERROR/top-level catch; its
    `code` (e.g. "#DIV/0!") becomes the cell's value when uncaught."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def is_error(value: ExcelValue) -> bool:
    return isinstance(value, str) and value in _ERRORS


def col_to_index(col: str) -> int:
    """"A" -> 0, "B" -> 1, ..., "Z" -> 25, "AA" -> 26."""
    index = 0
    for ch in col.upper():
        index = index * 26 + (ord(ch) - ord("A") + 1)
    return index - 1


def index_to_col(index: int) -> str:
    index += 1
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def parse_cell_ref(ref: str) -> tuple[int, int]:
    """"B12" -> (row_index=11, col_index=1), 0-indexed."""
    match = _CELL_RE.match(ref.strip())
    if not match:
        raise FormulaError("#REF!")
    col, row = match.groups()
    return int(row) - 1, col_to_index(col)


def make_cell_ref(row_index: int, col_index: int) -> str:
    return f"{index_to_col(col_index)}{row_index + 1}"


def expand_range(start_ref: str, end_ref: str) -> list[str]:
    r1, c1 = parse_cell_ref(start_ref)
    r2, c2 = parse_cell_ref(end_ref)
    refs = []
    for r in range(min(r1, r2), max(r1, r2) + 1):
        for c in range(min(c1, c2), max(c1, c2) + 1):
            refs.append(make_cell_ref(r, c))
    return refs


# --- Tokenizer ---------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""\s*(?:
    (?P<NUMBER>\d+\.\d+|\d+)
  | (?P<STRING>"(?:[^"]|"")*")
  | (?P<NAME>[A-Za-z_][A-Za-z0-9_.]*)
  | (?P<LE><=) | (?P<GE>>=) | (?P<NE><>)
  | (?P<OP>[+\-*/^&=<>(),:!])
    )""",
    re.VERBOSE,
)


@dataclass
class Token:
    kind: str
    value: str


def tokenize(formula: str) -> list[Token]:
    # "$" only ever marks an absolute reference ("$A$1", "A$1", "$A1") in
    # real Excel syntax — this engine has no fill-down/copy-paste concept for
    # relative-vs-absolute to matter to, so it's dropped before tokenizing
    # rather than taught to the grammar, and "$A$1" just parses as "A1".
    formula = formula.replace("$", "")
    tokens: list[Token] = []
    pos = 0
    while pos < len(formula):
        if formula[pos].isspace():
            pos += 1
            continue
        match = _TOKEN_RE.match(formula, pos)
        if not match:
            raise FormulaError("#NAME?")
        kind = match.lastgroup
        value = match.group(kind)
        tokens.append(Token(kind, value))
        pos = match.end()
    tokens.append(Token("EOF", ""))
    return tokens


# --- Parser + evaluator (combined recursive descent — grids are tiny, so
# re-parsing a formula on each dependency traversal costs nothing real) ------


@dataclass
class RangeValue:
    """A rectangular range's resolved cell values, kept 2D-flat for the
    aggregate functions (SUM/AVERAGE/...) and re-exposed as `refs` for the
    lookup functions (VLOOKUP/INDEX/MATCH/...) that need positions, not just
    values."""

    refs: list[str]
    sheet: str
    values: list[ExcelValue] = field(default_factory=list)


class Parser:
    def __init__(self, tokens: list[Token], sheet: str, resolve_ref) -> None:
        self.tokens = tokens
        self.pos = 0
        self.sheet = sheet
        self.resolve_ref = resolve_ref  # (sheet, cell_ref) -> ExcelValue, recursive+memoized

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _expect_op(self, op: str) -> None:
        token = self._advance()
        if token.kind != "OP" or token.value != op:
            raise FormulaError("#NAME?")

    def parse(self):
        value = self.parse_comparison()
        if self._peek().kind != "EOF":
            raise FormulaError("#NAME?")
        return value

    def parse_comparison(self):
        left = self.parse_concat()
        while self._peek().kind in ("LE", "GE", "NE") or (
            self._peek().kind == "OP" and self._peek().value in ("=", "<", ">")
        ):
            op_token = self._advance()
            right = self.parse_concat()
            left = _scalar(left)
            right_val = _scalar(right)
            op = {"LE": "<=", "GE": ">=", "NE": "<>"}.get(op_token.kind, op_token.value)
            left = _compare(left, right_val, op)
        return left

    def parse_concat(self):
        left = self.parse_additive()
        while self._peek().kind == "OP" and self._peek().value == "&":
            self._advance()
            right = self.parse_additive()
            left = _to_text(_scalar(left)) + _to_text(_scalar(right))
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self._peek().kind == "OP" and self._peek().value in ("+", "-"):
            op = self._advance().value
            right = self.parse_multiplicative()
            a, b = _to_number(_scalar(left)), _to_number(_scalar(right))
            left = a + b if op == "+" else a - b
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self._peek().kind == "OP" and self._peek().value in ("*", "/"):
            op = self._advance().value
            right = self.parse_unary()
            a, b = _to_number(_scalar(left)), _to_number(_scalar(right))
            if op == "*":
                left = a * b
            else:
                if b == 0:
                    raise FormulaError("#DIV/0!")
                left = a / b
        return left

    def parse_unary(self):
        if self._peek().kind == "OP" and self._peek().value == "-":
            self._advance()
            return -_to_number(_scalar(self.parse_unary()))
        return self.parse_power()

    def parse_power(self):
        left = self.parse_primary()
        while self._peek().kind == "OP" and self._peek().value == "^":
            self._advance()
            right = self.parse_primary()
            left = _to_number(_scalar(left)) ** _to_number(_scalar(right))
        return left

    def parse_primary(self):
        token = self._peek()

        if token.kind == "NUMBER":
            self._advance()
            return float(token.value)

        if token.kind == "STRING":
            self._advance()
            return token.value[1:-1].replace('""', '"')

        if token.kind == "OP" and token.value == "(":
            self._advance()
            value = self.parse_comparison()
            self._expect_op(")")
            return value

        if token.kind == "NAME":
            return self._parse_name_led()

        raise FormulaError("#NAME?")

    def _parse_name_led(self):
        name_token = self._advance()
        name = name_token.value

        # Sheet-qualified reference: NAME "!" (cellref [":" cellref])
        if self._peek().kind == "OP" and self._peek().value == "!":
            self._advance()
            return self._parse_ref_or_range(sheet=name)

        # Function call: NAME "(" ... ")"
        if self._peek().kind == "OP" and self._peek().value == "(":
            return self._parse_function_call(name.upper())

        upper = name.upper()
        if upper == "TRUE":
            return True
        if upper == "FALSE":
            return False

        # A bare cell reference or range in the current sheet.
        if _CELL_RE.match(name):
            if self._peek().kind == "OP" and self._peek().value == ":":
                self._advance()
                end_token = self._advance()
                return self._range(self.sheet, name, end_token.value)
            return self.resolve_ref(self.sheet, name)

        raise FormulaError("#NAME?")

    def _parse_ref_or_range(self, sheet: str):
        start_token = self._advance()
        start = start_token.value
        if not _CELL_RE.match(start):
            raise FormulaError("#REF!")
        if self._peek().kind == "OP" and self._peek().value == ":":
            self._advance()
            end_token = self._advance()
            return self._range(sheet, start, end_token.value)
        return self.resolve_ref(sheet, start)

    def _range(self, sheet: str, start: str, end: str) -> RangeValue:
        refs = expand_range(start, end)
        values = [self.resolve_ref(sheet, ref) for ref in refs]
        return RangeValue(refs=refs, sheet=sheet, values=values)

    def _parse_args(self) -> list:
        self._expect_op("(")
        args = []
        if not (self._peek().kind == "OP" and self._peek().value == ")"):
            args.append(self.parse_comparison())
            while self._peek().kind == "OP" and self._peek().value == ",":
                self._advance()
                args.append(self.parse_comparison())
        self._expect_op(")")
        return args

    def _parse_function_call(self, name: str):
        # IF/IFERROR need lazy argument evaluation (Excel never evaluates
        # IF's untaken branch, and IFERROR must catch an error *raised while
        # evaluating* its first argument, not one already thrown before the
        # function is even reached) — captured as raw token slices and
        # wrapped in thunks, rather than evaluated eagerly like every other
        # function's arguments.
        if name in ("IF", "IFERROR"):
            thunks = [self._make_thunk(tokens) for tokens in self._capture_arg_token_slices()]
            return self._eval_if(thunks) if name == "IF" else self._eval_iferror(thunks)

        args = self._parse_args()
        if name not in FUNCTIONS:
            raise FormulaError("#NAME?")
        return FUNCTIONS[name](args)

    def _capture_arg_token_slices(self) -> list[list[Token]]:
        """Captures each comma-separated argument's raw tokens (respecting
        nested parens) without evaluating anything — the caller decides
        which slices actually need evaluating, and when."""
        self._expect_op("(")
        if self._peek().kind == "OP" and self._peek().value == ")":
            self._advance()
            return []

        slices: list[list[Token]] = []
        current: list[Token] = []
        depth = 0
        while True:
            token = self._peek()
            if token.kind == "EOF":
                raise FormulaError("#NAME?")
            if token.kind == "OP" and token.value == "(":
                depth += 1
                current.append(self._advance())
            elif token.kind == "OP" and token.value == ")":
                if depth == 0:
                    self._advance()
                    slices.append(current)
                    return slices
                depth -= 1
                current.append(self._advance())
            elif token.kind == "OP" and token.value == "," and depth == 0:
                slices.append(current)
                current = []
                self._advance()
            else:
                current.append(self._advance())

    def _make_thunk(self, tokens: list[Token]):
        def thunk():
            return Parser([*tokens, Token("EOF", "")], self.sheet, self.resolve_ref).parse()

        return thunk

    def _eval_if(self, thunks: list):
        condition = _to_bool(_scalar(thunks[0]()))
        if condition:
            return _scalar(thunks[1]()) if len(thunks) > 1 else True
        return _scalar(thunks[2]()) if len(thunks) > 2 else False

    def _eval_iferror(self, thunks: list):
        try:
            value = _scalar(thunks[0]())
            if is_error(value):
                raise FormulaError(value)  # type: ignore[arg-type]
            return value
        except FormulaError:
            return _scalar(thunks[1]()) if len(thunks) > 1 else None


# --- Value coercion helpers ---------------------------------------------------


def _scalar(value):
    """A RangeValue used where a scalar is expected takes its first cell —
    the same "implicit intersection" leniency real spreadsheets apply."""
    if isinstance(value, RangeValue):
        return value.values[0] if value.values else None
    return value


def _flatten(args: list) -> list[ExcelValue]:
    out: list[ExcelValue] = []
    for arg in args:
        if isinstance(arg, RangeValue):
            out.extend(arg.values)
        else:
            out.append(arg)
    return out


def _to_number(value: ExcelValue) -> float:
    if is_error(value):
        raise FormulaError(value)  # type: ignore[arg-type]
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise FormulaError("#VALUE!") from None
    raise FormulaError("#VALUE!")


def _to_text(value: ExcelValue) -> str:
    if is_error(value):
        raise FormulaError(value)  # type: ignore[arg-type]
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _to_bool(value: ExcelValue) -> bool:
    if is_error(value):
        raise FormulaError(value)  # type: ignore[arg-type]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().upper() == "TRUE"
    return False


def _compare(a: ExcelValue, b: ExcelValue, op: str) -> bool:
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        pass
    else:
        a, b = _to_text(a), _to_text(b)
    if op == "=":
        return a == b
    if op == "<>":
        return a != b
    if op == "<":
        return a < b  # type: ignore[operator]
    if op == ">":
        return a > b  # type: ignore[operator]
    if op == "<=":
        return a <= b  # type: ignore[operator]
    if op == ">=":
        return a >= b  # type: ignore[operator]
    raise FormulaError("#VALUE!")


def _excel_serial_to_date(serial: float) -> date:
    return _EPOCH + timedelta(days=serial)


def _date_to_excel_serial(d: date) -> float:
    return float((d - _EPOCH).days)


# --- Criteria matching for *IF/*IFS functions --------------------------------


def _matches_criterion(value: ExcelValue, criterion: ExcelValue) -> bool:
    """Excel's SUMIF/COUNTIF-style criterion: a bare value means equality; a
    string starting with a comparison operator (">10", "<=5", "<>0") is a
    comparison; anything else is a case-insensitive equality/substring-free
    exact match on text."""
    if isinstance(criterion, str):
        for op in (">=", "<=", "<>", ">", "<"):
            if criterion.startswith(op):
                try:
                    threshold = float(criterion[len(op) :])
                except ValueError:
                    break
                try:
                    return _compare(_to_number(value), threshold, op)
                except FormulaError:
                    return False
        if criterion.startswith("="):
            criterion = criterion[1:]
    if isinstance(value, str) or isinstance(criterion, str):
        return _to_text(value).casefold() == _to_text(criterion).casefold()
    return _to_number(value) == _to_number(criterion)  # type: ignore[arg-type]


# --- Function implementations -------------------------------------------------


def _fn_sum(args: list) -> float:
    return sum(_to_number(v) for v in _flatten(args) if v is not None)


def _fn_average(args: list) -> float:
    values = [_to_number(v) for v in _flatten(args) if v is not None]
    if not values:
        raise FormulaError("#DIV/0!")
    return sum(values) / len(values)


def _fn_count(args: list) -> float:
    for v in _flatten(args):
        if is_error(v):
            # Every other aggregate (SUM/AVERAGE/MIN/MAX/SUMIF/...) routes its
            # values through _to_number, which already re-raises an error
            # string (including "#CIRCULAR!") via is_error. COUNT tested
            # `isinstance(v, (int, float))` directly on the raw value, so a
            # still-in-progress "#CIRCULAR!" placeholder was just silently
            # treated as "not a number" and excluded -- a self-referencing
            # range inside COUNT produced a plausible-looking but wrong
            # count instead of surfacing the circular-reference error.
            raise FormulaError(v)  # type: ignore[arg-type]
    return float(sum(1 for v in _flatten(args) if isinstance(v, (int, float)) and not isinstance(v, bool)))


def _fn_counta(args: list) -> float:
    for v in _flatten(args):
        if is_error(v):
            raise FormulaError(v)  # type: ignore[arg-type]
    return float(sum(1 for v in _flatten(args) if v is not None and v != ""))


def _fn_min(args: list) -> float:
    values = [_to_number(v) for v in _flatten(args) if v is not None]
    return min(values) if values else 0.0


def _fn_max(args: list) -> float:
    values = [_to_number(v) for v in _flatten(args) if v is not None]
    return max(values) if values else 0.0


def _fn_round(args: list) -> float:
    value = _to_number(_scalar(args[0]))
    digits = int(_to_number(_scalar(args[1]))) if len(args) > 1 else 0
    return round(value, digits)


def _fn_abs(args: list) -> float:
    return abs(_to_number(_scalar(args[0])))


def _fn_and(args: list) -> bool:
    return all(_to_bool(v) for v in _flatten(args))


def _fn_or(args: list) -> bool:
    return any(_to_bool(v) for v in _flatten(args))


def _fn_not(args: list) -> bool:
    return not _to_bool(_scalar(args[0]))


def _sumif_pairs(range_arg, criterion) -> list[tuple[ExcelValue, ExcelValue]]:
    values = range_arg.values if isinstance(range_arg, RangeValue) else [range_arg]
    return [(v, v) for v in values if _matches_criterion(v, criterion)]


def _fn_sumif(args: list) -> float:
    check_range, criterion = args[0], _scalar(args[1])
    sum_range = args[2] if len(args) > 2 else check_range
    check_values = check_range.values if isinstance(check_range, RangeValue) else [check_range]
    sum_values = sum_range.values if isinstance(sum_range, RangeValue) else [sum_range]
    total = 0.0
    for check_value, sum_value in zip(check_values, sum_values, strict=False):
        if _matches_criterion(check_value, criterion):
            total += _to_number(sum_value) if sum_value is not None else 0.0
    return total


def _fn_sumifs(args: list) -> float:
    sum_range = args[0]
    sum_values = sum_range.values if isinstance(sum_range, RangeValue) else [sum_range]
    condition_pairs = list(zip(args[1::2], args[2::2], strict=False))
    if not condition_pairs:
        # SUMIFS requires at least one range/criteria pair -- without this
        # guard, an incomplete formula like =SUMIFS(A1:A3) silently summed
        # the ENTIRE range with no filtering at all, instead of erroring.
        raise FormulaError("#VALUE!")
    total = 0.0
    for i, sum_value in enumerate(sum_values):
        if all(
            _matches_criterion((cr.values if isinstance(cr, RangeValue) else [cr])[i], _scalar(crit))
            for cr, crit in condition_pairs
        ):
            total += _to_number(sum_value) if sum_value is not None else 0.0
    return total


def _fn_countif(args: list) -> float:
    check_range, criterion = args[0], _scalar(args[1])
    check_values = check_range.values if isinstance(check_range, RangeValue) else [check_range]
    return float(sum(1 for v in check_values if _matches_criterion(v, criterion)))


def _fn_countifs(args: list) -> float:
    condition_pairs = list(zip(args[0::2], args[1::2], strict=False))
    if not condition_pairs:
        # COUNTIFS requires at least one range/criteria pair -- e.g. a
        # student typing an incomplete =COUNTIFS(A2:A10) (easy to do, since
        # a range naturally comes before its criteria). Without this guard,
        # `condition_pairs[0]` below raised an unhandled IndexError instead
        # of a formula error, crashing both the live-preview grid (on every
        # keystroke) and exercise-submission grading with a raw 500.
        raise FormulaError("#VALUE!")
    first_range = condition_pairs[0][0]
    length = len(first_range.values) if isinstance(first_range, RangeValue) else 1
    count = 0
    for i in range(length):
        if all(
            _matches_criterion((cr.values if isinstance(cr, RangeValue) else [cr])[i], _scalar(crit))
            for cr, crit in condition_pairs
        ):
            count += 1
    return float(count)


def _fn_averageif(args: list) -> float:
    check_range, criterion = args[0], _scalar(args[1])
    avg_range = args[2] if len(args) > 2 else check_range
    check_values = check_range.values if isinstance(check_range, RangeValue) else [check_range]
    avg_values = avg_range.values if isinstance(avg_range, RangeValue) else [avg_range]
    matched = [
        _to_number(v) for cv, v in zip(check_values, avg_values, strict=False) if _matches_criterion(cv, criterion)
    ]
    if not matched:
        raise FormulaError("#DIV/0!")
    return sum(matched) / len(matched)


def _fn_vlookup(args: list):
    lookup_value = _scalar(args[0])
    table = args[1]
    col_index = int(_to_number(_scalar(args[2])))
    # Excel's 4th argument is `range_lookup`: TRUE or omitted means
    # APPROXIMATE match; only an explicit FALSE means exact. The previous
    # code named this variable `exact` but assigned it the RAW range_lookup
    # value with no inversion -- backwards from its own name, though this
    # was masked before since both of the OLD branches were pure equality
    # tests either way. Naming it for what it actually holds and inverting
    # once, here, is what makes the two branches below correct.
    range_lookup = _to_bool(_scalar(args[3])) if len(args) > 3 else True
    exact = not range_lookup
    if not isinstance(table, RangeValue):
        raise FormulaError("#REF!")
    row_refs, row_cols = _range_dims(table)

    if exact:
        for row in range(row_refs):
            key = table.values[row * row_cols]
            if _matches_criterion(key, lookup_value):
                target = row * row_cols + (col_index - 1)
                if target >= len(table.values):
                    raise FormulaError("#REF!")
                return table.values[target]
        raise FormulaError("#N/A")

    # Approximate/range match -- the real Excel default. Previously
    # unimplemented: both branches here were pure equality tests, so any
    # tiered-lookup use (tax brackets, commission tiers, grade curves — a
    # classic, extremely common real-world VLOOKUP pattern, and the default
    # behavior whenever a student omits the 4th argument) always returned
    # #N/A instead of the correct tier. Mirrors _fn_match's match_type=1
    # algorithm exactly: assumes the first column is sorted ascending,
    # returns the row with the largest key <= lookup_value.
    best_row = None
    for row in range(row_refs):
        key = table.values[row * row_cols]
        try:
            ok = _compare(_to_number(key), _to_number(lookup_value), "<=")
        except FormulaError:
            continue
        if ok:
            best_row = row
    if best_row is None:
        raise FormulaError("#N/A")
    target = best_row * row_cols + (col_index - 1)
    if target >= len(table.values):
        raise FormulaError("#REF!")
    return table.values[target]


def _range_dims(table: RangeValue) -> tuple[int, int]:
    r1, c1 = parse_cell_ref(table.refs[0])
    r2, c2 = parse_cell_ref(table.refs[-1])
    return (abs(r2 - r1) + 1, abs(c2 - c1) + 1)


def _fn_index(args: list):
    table = args[0]
    if not isinstance(table, RangeValue):
        raise FormulaError("#REF!")
    rows, cols = _range_dims(table)
    row_num = int(_to_number(_scalar(args[1]))) if len(args) > 1 else 1
    col_num = int(_to_number(_scalar(args[2]))) if len(args) > 2 else 1
    if rows == 1 and len(args) <= 2:
        col_num, row_num = row_num, 1
    idx = (row_num - 1) * cols + (col_num - 1)
    if idx < 0 or idx >= len(table.values):
        raise FormulaError("#REF!")
    return table.values[idx]


def _fn_match(args: list):
    lookup_value = _scalar(args[0])
    table = args[1]
    match_type = int(_to_number(_scalar(args[2]))) if len(args) > 2 else 1
    values = table.values if isinstance(table, RangeValue) else [table]
    if match_type == 0:
        for i, v in enumerate(values):
            if _matches_criterion(v, lookup_value):
                return float(i + 1)
        raise FormulaError("#N/A")
    # Approximate match (assumes sorted ascending for 1, descending for -1) —
    # last value satisfying the comparison, matching Excel's own behavior.
    best = None
    for i, v in enumerate(values):
        try:
            ok = _compare(_to_number(v), _to_number(lookup_value), "<=" if match_type == 1 else ">=")
        except FormulaError:
            continue
        if ok:
            best = i + 1
    if best is None:
        raise FormulaError("#N/A")
    return float(best)


def _fn_xlookup(args: list):
    lookup_value = _scalar(args[0])
    lookup_range = args[1]
    return_range = args[2]
    if_not_found = args[3] if len(args) > 3 else None
    lookup_values = lookup_range.values if isinstance(lookup_range, RangeValue) else [lookup_range]
    return_values = return_range.values if isinstance(return_range, RangeValue) else [return_range]
    for lv, rv in zip(lookup_values, return_values, strict=False):
        if _matches_criterion(lv, lookup_value):
            return rv
    if if_not_found is not None:
        return _scalar(if_not_found)
    raise FormulaError("#N/A")


def _fn_concatenate(args: list) -> str:
    return "".join(_to_text(v) for v in _flatten(args))


def _fn_upper(args: list) -> str:
    return _to_text(_scalar(args[0])).upper()


def _fn_lower(args: list) -> str:
    return _to_text(_scalar(args[0])).lower()


def _fn_trim(args: list) -> str:
    return " ".join(_to_text(_scalar(args[0])).split())


def _fn_len(args: list) -> float:
    return float(len(_to_text(_scalar(args[0]))))


def _fn_left(args: list) -> str:
    text = _to_text(_scalar(args[0]))
    n = int(_to_number(_scalar(args[1]))) if len(args) > 1 else 1
    return text[:n]


def _fn_right(args: list) -> str:
    text = _to_text(_scalar(args[0]))
    n = int(_to_number(_scalar(args[1]))) if len(args) > 1 else 1
    return text[-n:] if n > 0 else ""


def _fn_mid(args: list) -> str:
    text = _to_text(_scalar(args[0]))
    start = int(_to_number(_scalar(args[1])))
    length = int(_to_number(_scalar(args[2])))
    return text[start - 1 : start - 1 + length]


def _fn_text(args: list) -> str:
    value = _scalar(args[0])
    fmt = _to_text(_scalar(args[1])) if len(args) > 1 else ""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and fmt:
        if fmt.lower() == "yyyy-mm-dd":
            return _excel_serial_to_date(value).isoformat()
        if fmt.endswith("%"):
            digits = max(fmt.count("0") - 1, 0)
            return f"{value * 100:.{digits}f}%"
        # A simple numeric format like "0" / "0.00"
        digits = len(fmt.split(".")[1]) if "." in fmt else 0
        return f"{value:.{digits}f}"
    return _to_text(value)


def _fn_year(args: list) -> float:
    return float(_excel_serial_to_date(_to_number(_scalar(args[0]))).year)


def _fn_month(args: list) -> float:
    return float(_excel_serial_to_date(_to_number(_scalar(args[0]))).month)


def _fn_day(args: list) -> float:
    return float(_excel_serial_to_date(_to_number(_scalar(args[0]))).day)


def _fn_date(args: list) -> float:
    y, m, d = (int(_to_number(_scalar(a))) for a in args[:3])
    return _date_to_excel_serial(date(y, m, d))


def _fn_today(_args: list) -> float:
    return _date_to_excel_serial(datetime.now().date())


def _fn_datedif(args: list) -> float:
    start = _excel_serial_to_date(_to_number(_scalar(args[0])))
    end = _excel_serial_to_date(_to_number(_scalar(args[1])))
    unit = _to_text(_scalar(args[2])).upper() if len(args) > 2 else "D"
    if unit == "D":
        return float((end - start).days)
    if unit == "M":
        return float((end.year - start.year) * 12 + (end.month - start.month))
    if unit == "Y":
        return float(end.year - start.year - (1 if (end.month, end.day) < (start.month, start.day) else 0))
    raise FormulaError("#NUM!")


FUNCTIONS = {
    "SUM": _fn_sum,
    "AVERAGE": _fn_average,
    "COUNT": _fn_count,
    "COUNTA": _fn_counta,
    "MIN": _fn_min,
    "MAX": _fn_max,
    "ROUND": _fn_round,
    "ABS": _fn_abs,
    "AND": _fn_and,
    "OR": _fn_or,
    "NOT": _fn_not,
    "SUMIF": _fn_sumif,
    "SUMIFS": _fn_sumifs,
    "COUNTIF": _fn_countif,
    "COUNTIFS": _fn_countifs,
    "AVERAGEIF": _fn_averageif,
    "VLOOKUP": _fn_vlookup,
    "INDEX": _fn_index,
    "MATCH": _fn_match,
    "XLOOKUP": _fn_xlookup,
    "CONCATENATE": _fn_concatenate,
    "CONCAT": _fn_concatenate,
    "UPPER": _fn_upper,
    "LOWER": _fn_lower,
    "TRIM": _fn_trim,
    "LEN": _fn_len,
    "LEFT": _fn_left,
    "RIGHT": _fn_right,
    "MID": _fn_mid,
    "TEXT": _fn_text,
    "YEAR": _fn_year,
    "MONTH": _fn_month,
    "DAY": _fn_day,
    "DATE": _fn_date,
    "TODAY": _fn_today,
    "DATEDIF": _fn_datedif,
}


# --- Literal (non-formula) cell coercion -------------------------------------


def _coerce_literal(raw: str) -> ExcelValue:
    stripped = raw.strip()
    if stripped == "":
        return None
    if stripped.upper() == "TRUE":
        return True
    if stripped.upper() == "FALSE":
        return False
    try:
        return float(stripped) if ("." in stripped or "e" in stripped.lower()) else float(int(stripped))
    except ValueError:
        return raw  # preserve whitespace exactly as entered — TRIM() exists precisely to clean this up


# --- Workbook evaluation driver ----------------------------------------------


class _CIRCULAR:
    """Sentinel placed while a cell is mid-evaluation, to detect cycles."""


def evaluate_workbook(workbook: Workbook) -> EvaluatedWorkbook:
    """Fully resolves every cell in every sheet. A formula cell that raises
    (bad ref, div/0, etc.) stores the Excel-style error string as its value —
    grading compares against the solution's own evaluated value at the same
    cell, so a solution's intentional `#N/A` (e.g. a deliberately unmatched
    XLOOKUP) is a valid, checkable expected value too."""
    resolved: dict[tuple[str, str], ExcelValue] = {}
    in_progress: set[tuple[str, str]] = set()

    def resolve_ref(sheet: str, ref: str) -> ExcelValue:
        if sheet not in workbook:
            return "#REF!"
        key = (sheet, ref.upper())
        if key in resolved:
            return resolved[key]
        if key in in_progress:
            return "#CIRCULAR!"

        raw = workbook[sheet].get(ref.upper()) or workbook[sheet].get(ref)
        if raw is None:
            resolved[key] = None
            return None

        in_progress.add(key)
        try:
            if isinstance(raw, str) and raw.startswith("="):
                try:
                    tokens = tokenize(raw[1:])
                    value = Parser(tokens, sheet, resolve_ref).parse()
                    value = _scalar(value)
                except FormulaError as exc:
                    value = exc.code
            else:
                value = _coerce_literal(raw) if isinstance(raw, str) else raw
        finally:
            in_progress.discard(key)

        resolved[key] = value
        return value

    output: EvaluatedWorkbook = {}
    for sheet, cells in workbook.items():
        output[sheet] = {}
        for ref in cells:
            output[sheet][ref.upper()] = resolve_ref(sheet, ref)
    return output


def get_evaluated_cell(evaluated: EvaluatedWorkbook, sheet: str, ref: str) -> ExcelValue:
    return evaluated.get(sheet, {}).get(ref.upper())
