import pytest

from receipt import billable_units, format_pence, line_cost_pence, discount_pence, total_pence, format_pence, parse_manifest, parse_line, render

def test_billable_units():
    assert billable_units(25) == 1
    assert billable_units(26) == 2 
    assert billable_units(51) == 3

def test_billable_units_zero_or_negative():
    with pytest.raises(ValueError):
        billable_units(0)
    with pytest.raises(ValueError):
        billable_units(-5)

def test_billable_units_below_unit_size():
    assert billable_units(1) == 1


def test_line_cost_pence_for_loose_item():
    assert line_cost_pence("loose", 25) == 275
    assert line_cost_pence("loose", 50) == 550

def test_line_cost_pence_for_crated_item():
    assert line_cost_pence("crated", 25) == 430  
    assert line_cost_pence("crated", 50) == 700  

def test_discount_pence_below_threshold():
    assert discount_pence(10000, 9) == 0

def test_discount_pence_at_threshold():
    assert discount_pence(10000, 10) == 500
    assert discount_pence(20000, 10) == 1000

def test_discount_pence_above_threshold():
    assert discount_pence(10000, 15) == 500
    assert discount_pence(20000, 20) == 1000

def test_total_pence_empty():
    assert total_pence([]) == 0

def test_total_pence_one_row():
    row = [("north",   "crated", 120)]
    assert total_pence(row) == 1525  

def test_total_pence_multiple_rows():
    rows = [
        ("north",   "crated", 120),
        ("south",   "loose",   40),
        ("east",    "crated", 310),
    ]
    assert total_pence(rows) == 5800

def test_total_pence_multiple_rows_with_discount():
    rows = [
        ("north",   "crated", 120),
        ("south",   "loose",   40),
        ("east",    "crated", 310),
        ("west",    "crated",  75),
        ("north",   "loose",   12),
        ("south",   "crated", 250),
        ("east",    "loose",   95),
        ("west",    "loose",  180),
        ("north",   "crated",  25),
        ("south",   "loose",   60),
        ("east",    "crated",  33),
        ("west",    "crated", 410),
    ]
    assert total_pence(rows) == 19024

@pytest.mark.parametrize(
    "pence,expected", 
    [
        (0, "0.00"), # for zero values
        (1, "0.01"), # for single digit pence 
        (12, "0.12"), # for double digit pence
        (100, "1.00"),# for exact pound
        (1450, "14.50"), # for double digit pounds
        (-5, "-0.05"),  # for negative single digit pence
        (-123, "-1.23"), # for negative double digit pence
        (250000, "2500.00"), # for a large number of pence
    ],
)
def test_format_pence(pence, expected):
    assert format_pence(pence) == expected

def test_format_pence_invalid_type():
    with pytest.raises(TypeError):
        format_pence("123")  

def test_render_empty():
    assert render([]) == ["0 rows", "total 0.00"]

def test_render_single_row():
    rows = [("north", "crated", 120.0)]
    expected = [
        "north    crated   120.0kg     15.25",
        "1 rows",
        "total 15.25",
    ]
    assert render(rows) == expected

def test_parse_line_valid():
    line = "north, crated, 120.0"
    expected = ("north", "crated", 120.0)
    assert parse_line(line) == expected

def test_parse_line_invalid():
    with pytest.raises(ValueError):
        parse_line("north crated")

    with pytest.raises(ValueError):
        parse_line(", crated, 120.0")

    with pytest.raises(ValueError):
        parse_line("north, boxed, 120.0")

def test_parse_manifest():
    manifest_text = """
    # Manifest comment
    north, crated, 120

    south, loose, 40
    """
    expected = [
        ("north", "crated", 120.0),
        ("south", "loose", 40.0),
    ]
    assert parse_manifest(manifest_text) == expected

def test_parse_line_too_many_fields():
    with pytest.raises(ValueError):
        parse_line("north, crated, 120.0, extra")

def test_parse_line_non_numeric_weight():
    with pytest.raises(ValueError):
        parse_line("north, crated, abc")

def test_discount_pence_requires_floor_rounding():
    assert discount_pence(333, 10) == 16