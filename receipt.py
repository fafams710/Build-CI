"""Work out what a depot run costs to send.

Reads a manifest file of comma-separated lines and prints a costed receipt.

    python receipt.py samples/manifest.csv
"""

import sys

RATE_PER_UNIT_PENCE = 275
CRATE_SURCHARGE_PENCE = 150
UNIT_KG = 25
BULK_DISCOUNT_FROM = 10
BULK_DISCOUNT_PERCENT = 5


def parse_line(line):
    """Turn one manifest line into a (destination, packing, weight_kg) tuple."""
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 3:
        raise ValueError("expected three fields, got %d" % len(parts))
    destination, packing, weight = parts
    if not destination:
        raise ValueError("destination is empty")
    if packing not in ("crated", "loose"):
        raise ValueError("unknown packing: %s" % packing)
    return destination, packing, float(weight)


def parse_manifest(text):
    """Turn the text of a manifest file into a list of rows.

    Blank lines and lines beginning with # are skipped.
    """
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append(parse_line(stripped))
    return rows


def billable_units(weight_kg):
    """The number of whole 25kg units this weight is charged as, rounding up."""
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    whole, remainder = divmod(weight_kg, UNIT_KG)
    return int(whole) + (1 if remainder else 0)


def line_cost_pence(packing, weight_kg):
    """What one manifest row costs, before any discount."""
    cost = billable_units(weight_kg) * RATE_PER_UNIT_PENCE
    if packing == "crated":
        cost += CRATE_SURCHARGE_PENCE
    return cost


def discount_pence(subtotal_pence, row_count):
    """The discount a run of this many rows earns on this subtotal."""
    if row_count < BULK_DISCOUNT_FROM:
        return 0
    return subtotal_pence * BULK_DISCOUNT_PERCENT // 100


def total_pence(rows):
    """The full cost of a run, discount applied."""
    subtotal = sum(line_cost_pence(packing, weight) for _, packing, weight in rows)
    return subtotal - discount_pence(subtotal, len(rows))


def format_pence(pence):
    """Render a whole number of pence as pounds and pence."""
    sign = "-" if pence < 0 else ""
    pence = abs(pence)
    return "%s%d.%02d" % (sign, pence // 100, pence % 100)


def render(rows):
    """The receipt, as a list of lines."""
    lines = []
    for destination, packing, weight in rows:
        cost = line_cost_pence(packing, weight)
        lines.append("%-8s %-7s %6.1fkg  %8s" % (destination, packing, weight, format_pence(cost)))
    lines.append("%d rows" % len(rows))
    lines.append("total %s" % format_pence(total_pence(rows)))
    return lines


def main(argv):
    if len(argv) != 2:
        print("usage: receipt.py <manifest>")
        return 2
    try:
        with open(argv[1], encoding="utf-8") as handle:
            rows = parse_manifest(handle.read())
    except OSError as error:
        print("cannot read manifest: %s" % error)
        return 1
    except ValueError as error:
        print("bad manifest: %s" % error)
        return 1
    for line in render(rows):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
