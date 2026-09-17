"""Real, execution-based tests for the Phase 9 Excel formula engine — every
assertion here runs the actual tokenizer/parser/evaluator, never a hand-typed
"expected" string standing in for what the engine would produce."""

from __future__ import annotations

from app.excel_lab.formula_engine import evaluate_workbook


def ev(sheet_cells: dict[str, str], sheet_name: str = "Sheet1") -> dict[str, object]:
    return evaluate_workbook({sheet_name: sheet_cells})[sheet_name]


class TestLiteralsAndArithmetic:
    def test_numeric_and_text_literals(self) -> None:
        result = ev({"A1": "42", "A2": "3.5", "A3": "Widget", "A4": "TRUE"})
        assert result["A1"] == 42.0
        assert result["A2"] == 3.5
        assert result["A3"] == "Widget"
        assert result["A4"] is True

    def test_basic_arithmetic_and_precedence(self) -> None:
        result = ev({"A1": "=2+3*4", "A2": "=(2+3)*4", "A3": "=2^3", "A4": "=10/4", "A5": "=-5+2"})
        assert result["A1"] == 14.0
        assert result["A2"] == 20.0
        assert result["A3"] == 8.0
        assert result["A4"] == 2.5
        assert result["A5"] == -3.0

    def test_division_by_zero(self) -> None:
        result = ev({"A1": "0", "A2": "=10/A1"})
        assert result["A2"] == "#DIV/0!"

    def test_cell_references(self) -> None:
        result = ev({"A1": "10", "A2": "20", "A3": "=A1+A2"})
        assert result["A3"] == 30.0

    def test_string_concatenation(self) -> None:
        result = ev({"A1": "Hello", "A2": "World", "A3": '=A1&" "&A2'})
        assert result["A3"] == "Hello World"

    def test_comparisons(self) -> None:
        result = ev({"A1": "5", "A2": "=A1>3", "A3": "=A1=5", "A4": "=A1<>5"})
        assert result["A2"] is True
        assert result["A3"] is True
        assert result["A4"] is False


class TestAggregateFunctions:
    def test_sum_average_count_min_max(self) -> None:
        result = ev(
            {
                "A1": "1",
                "A2": "2",
                "A3": "3",
                "A4": "4",
                "B1": "=SUM(A1:A4)",
                "B2": "=AVERAGE(A1:A4)",
                "B3": "=COUNT(A1:A4)",
                "B4": "=MIN(A1:A4)",
                "B5": "=MAX(A1:A4)",
            }
        )
        assert result["B1"] == 10.0
        assert result["B2"] == 2.5
        assert result["B3"] == 4.0
        assert result["B4"] == 1.0
        assert result["B5"] == 4.0

    def test_round_and_abs(self) -> None:
        result = ev({"A1": "=ROUND(3.14159,2)", "A2": "=ABS(-7)"})
        assert result["A1"] == 3.14
        assert result["A2"] == 7.0


class TestConditionals:
    def test_if(self) -> None:
        result = ev({"A1": "10", "A2": '=IF(A1>5,"big","small")'})
        assert result["A2"] == "big"

    def test_nested_if(self) -> None:
        result = ev({"A1": "72", "A2": '=IF(A1>=90,"A",IF(A1>=70,"B","C"))'})
        assert result["A2"] == "B"

    def test_if_never_evaluates_the_untaken_branch(self) -> None:
        # The FALSE branch divides by zero — if IF evaluated it anyway
        # (eager, not lazy, argument evaluation), this would blow up with
        # #DIV/0! instead of returning the TRUE branch's value.
        result = ev({"A1": "5", "A2": "0", "A3": "=IF(A1>1,999,10/A2)"})
        assert result["A3"] == 999.0

    def test_iferror_catches_division_by_zero(self) -> None:
        result = ev({"A1": "0", "A2": '=IFERROR(10/A1,"n/a")'})
        assert result["A2"] == "n/a"

    def test_iferror_passthrough_when_no_error(self) -> None:
        result = ev({"A1": "5", "A2": "=IFERROR(A1*2,-1)"})
        assert result["A2"] == 10.0

    def test_and_or_not(self) -> None:
        result = ev({"A1": "=AND(TRUE,TRUE)", "A2": "=OR(FALSE,TRUE)", "A3": "=NOT(TRUE)"})
        assert result["A1"] is True
        assert result["A2"] is True
        assert result["A3"] is False


class TestConditionalAggregates:
    def test_sumif(self) -> None:
        # Regions A/A/B/B with amounts 10/20/30/40 — SUMIF("A") = 30.
        result = ev(
            {
                "A1": "A",
                "A2": "A",
                "A3": "B",
                "A4": "B",
                "B1": "10",
                "B2": "20",
                "B3": "30",
                "B4": "40",
                "C1": '=SUMIF(A1:A4,"A",B1:B4)',
            }
        )
        assert result["C1"] == 30.0

    def test_sumifs_two_conditions(self) -> None:
        result = ev(
            {
                "A1": "A",
                "A2": "A",
                "A3": "B",
                "B1": "West",
                "B2": "East",
                "B3": "West",
                "C1": "10",
                "C2": "20",
                "C3": "30",
                "D1": '=SUMIFS(C1:C3,A1:A3,"A",B1:B3,"West")',
            }
        )
        assert result["D1"] == 10.0

    def test_countif_and_countifs(self) -> None:
        result = ev(
            {
                "A1": "5",
                "A2": "12",
                "A3": "8",
                "A4": "20",
                "B1": '=COUNTIF(A1:A4,">10")',
                "B2": '=COUNTIFS(A1:A4,">5",A1:A4,"<15")',
            }
        )
        assert result["B1"] == 2.0
        assert result["B2"] == 2.0  # 8 and 12 are both >5 and <15 (5 fails >5, 20 fails <15)

    def test_countifs_with_a_single_incomplete_range_criteria_pair_errors_not_crashes(self) -> None:
        """Regression test: COUNTIFS called with only a range and no
        criteria (e.g. a student typing =COUNTIFS(A2:A10), plausible since
        the range naturally comes before the criteria) used to raise an
        unhandled Python IndexError instead of a formula error, crashing
        the request (500) on both the live-preview and exercise-submit
        endpoints."""
        result = ev({"A1": "10", "A2": "20", "A3": "30", "B1": "=COUNTIFS(A1:A3)"})
        assert result["B1"] == "#VALUE!"

    def test_sumifs_with_no_criteria_pairs_errors_rather_than_summing_everything(self) -> None:
        """Regression test: SUMIFS with no criteria pairs used to silently
        sum the ENTIRE range with no filtering at all (a wrong but
        non-crashing result) instead of erroring."""
        result = ev({"A1": "10", "A2": "20", "A3": "30", "B1": "=SUMIFS(A1:A3)"})
        assert result["B1"] == "#VALUE!"

    def test_averageif(self) -> None:
        result = ev(
            {
                "A1": "A",
                "A2": "B",
                "A3": "A",
                "B1": "10",
                "B2": "999",
                "B3": "30",
                "C1": '=AVERAGEIF(A1:A3,"A",B1:B3)',
            }
        )
        assert result["C1"] == 20.0


class TestLookups:
    def test_vlookup_exact_match(self) -> None:
        result = ev(
            {
                "A1": "sku1",
                "A2": "sku2",
                "B1": "Widget",
                "B2": "Gadget",
                "C1": '=VLOOKUP("sku2",A1:B2,2,FALSE)',
            }
        )
        assert result["C1"] == "Gadget"

    def test_vlookup_not_found(self) -> None:
        result = ev({"A1": "sku1", "B1": "Widget", "C1": '=VLOOKUP("sku9",A1:B1,2,FALSE)'})
        assert result["C1"] == "#N/A"

    def test_vlookup_approximate_match_with_explicit_true(self) -> None:
        """Regression test: VLOOKUP's approximate/range-lookup mode was
        never implemented -- both the exact and "approximate" branches were
        pure equality tests. A tiered lookup (tax brackets, commission
        tiers, grade curves) always returned #N/A instead of the correct
        tier."""
        result = ev(
            {
                "A1": "0",
                "A2": "60",
                "A3": "70",
                "A4": "80",
                "A5": "90",
                "B1": "F",
                "B2": "D",
                "B3": "C",
                "B4": "B",
                "B5": "A",
                "C1": "=VLOOKUP(85,A1:B5,2,TRUE)",
            }
        )
        assert result["C1"] == "B"

    def test_vlookup_approximate_match_is_the_real_default_when_4th_arg_omitted(self) -> None:
        """Real Excel's own default (4th argument omitted) is approximate,
        not exact -- only an explicit FALSE means exact match."""
        result = ev(
            {
                "A1": "0",
                "A2": "60",
                "A3": "70",
                "A4": "80",
                "A5": "90",
                "B1": "F",
                "B2": "D",
                "B3": "C",
                "B4": "B",
                "B5": "A",
                "C1": "=VLOOKUP(85,A1:B5,2)",
            }
        )
        assert result["C1"] == "B"

    def test_index_match(self) -> None:
        result = ev(
            {
                "A1": "sku1",
                "A2": "sku2",
                "A3": "sku3",
                "B1": "10",
                "B2": "20",
                "B3": "30",
                "C1": '=INDEX(B1:B3,MATCH("sku2",A1:A3,0))',
            }
        )
        assert result["C1"] == 20.0

    def test_xlookup(self) -> None:
        result = ev(
            {
                "A1": "sku1",
                "A2": "sku2",
                "B1": "10",
                "B2": "20",
                "C1": '=XLOOKUP("sku2",A1:A2,B1:B2)',
                "C2": '=XLOOKUP("sku9",A1:A2,B1:B2,"missing")',
            }
        )
        assert result["C1"] == 20.0
        assert result["C2"] == "missing"


class TestTextFunctions:
    def test_upper_lower_trim_len(self) -> None:
        result = ev(
            {
                "A1": "  hello  ",
                "B1": "=UPPER(A1)",
                "B2": "=TRIM(A1)",
                "B3": "=LEN(A1)",
            }
        )
        assert result["B1"] == "  HELLO  "
        assert result["B2"] == "hello"
        assert result["B3"] == 9.0

    def test_left_right_mid(self) -> None:
        result = ev({"A1": "Analytics", "B1": "=LEFT(A1,3)", "B2": "=RIGHT(A1,3)", "B3": "=MID(A1,2,4)"})
        assert result["B1"] == "Ana"
        assert result["B2"] == "ics"
        assert result["B3"] == "naly"

    def test_concatenate(self) -> None:
        result = ev({"A1": "Data", "A2": "Analyst", "B1": '=CONCATENATE(A1," ",A2)'})
        assert result["B1"] == "Data Analyst"


class TestDateFunctions:
    def test_year_month_day(self) -> None:
        result = ev({"A1": "=DATE(2026,3,15)", "B1": "=YEAR(A1)", "B2": "=MONTH(A1)", "B3": "=DAY(A1)"})
        assert result["B1"] == 2026.0
        assert result["B2"] == 3.0
        assert result["B3"] == 15.0

    def test_datedif_days(self) -> None:
        result = ev({"A1": "=DATE(2026,1,1)", "A2": "=DATE(2026,1,31)", "B1": '=DATEDIF(A1,A2,"D")'})
        assert result["B1"] == 30.0


class TestAbsoluteReferencesAndTextFormatting:
    def test_dollar_sign_absolute_references_parse_like_plain_refs(self) -> None:
        # $A$1 -> A1 (10), A$2 -> A2 (20), $A1 -> A1 (10) again: 10+20+10=40.
        result = ev({"A1": "10", "A2": "20", "B1": "=$A$1+A$2+$A1"})
        assert result["B1"] == 40.0

    def test_text_percent_format(self) -> None:
        result = ev({"A1": "0.256", "B1": '=TEXT(A1,"0%")'})
        assert result["B1"] == "26%"


class TestCrossSheetAndErrors:
    def test_cross_sheet_reference(self) -> None:
        result = evaluate_workbook(
            {
                "Data": {"A1": "100"},
                "Summary": {"A1": "=Data!A1*2"},
            }
        )
        assert result["Summary"]["A1"] == 200.0

    def test_circular_reference_detected(self) -> None:
        result = ev({"A1": "=A2", "A2": "=A1"})
        assert result["A1"] == "#CIRCULAR!"

    def test_count_over_a_self_including_circular_range_surfaces_the_error(self) -> None:
        """Regression test: COUNT/COUNTA tested the raw value's Python type
        directly instead of routing through _to_number/is_error like every
        other aggregate (SUM/AVERAGE/MIN/MAX/...) does, so the in-progress
        "#CIRCULAR!" placeholder for a still-being-computed cell was
        silently treated as "not a number" and excluded from the count --
        a self-referencing COUNT(A1:A3) range (A1's own formula is itself
        inside the range it counts) returned a plausible-looking but wrong
        number with no error, instead of surfacing #CIRCULAR!."""
        result = ev({"A1": "=COUNT(A1:A3)", "A2": "5", "A3": "10"})
        assert result["A1"] == "#CIRCULAR!"

    def test_counta_over_a_self_including_circular_range_surfaces_the_error(self) -> None:
        result = ev({"A1": "=COUNTA(A1:A3)", "A2": "5", "A3": "10"})
        assert result["A1"] == "#CIRCULAR!"

    def test_bad_reference_in_missing_sheet(self) -> None:
        result = evaluate_workbook({"Sheet1": {"A1": "=Nope!A1"}})
        assert result["Sheet1"]["A1"] == "#REF!"

    def test_empty_cell_is_none_and_treated_as_zero_in_sum(self) -> None:
        result = ev({"A1": "5", "A2": "", "A3": "=SUM(A1:A2)"})
        assert result["A3"] == 5.0
