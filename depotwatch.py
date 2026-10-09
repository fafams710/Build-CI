"""Report on the shipments the depot API is holding.

Needs the section 4 sandbox server running:

    cd python/http/sandbox && python depot_api.py

then, in another terminal:

    python depotwatch.py 100
"""

import sys

import requests

BASE_URL = "http://localhost:8420"
DEFAULT_THRESHOLD_KG = 100
TIMEOUT_SECONDS = 5


def fetch_shipments(base_url=BASE_URL):
    """Ask the depot for every shipment it holds.

    Raises requests.HTTPError if the depot answers with an error status, and
    requests.RequestException if the call never got that far.
    """
    response = requests.get(base_url + "/shipments", timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def heavy_shipments(shipments, threshold_kg):
    """Those shipments at or above a weight, heaviest first.

    A shipment with no recorded weight is not heavy.
    """
    weighed = [s for s in shipments
               if isinstance(s.get("weight_kg"), (int, float))
               and s["weight_kg"] >= threshold_kg]
    return sorted(weighed, key=lambda s: s["weight_kg"], reverse=True)


def unweighed(shipments):
    """The ids of shipments the depot has no weight for."""
    return [s["id"] for s in shipments
            if not isinstance(s.get("weight_kg"), (int, float))]


def describe(shipment):
    """One line about one shipment."""
    return "#%d %-6s %-7s %5.0fkg" % (shipment["id"], shipment["destination"],
                                      shipment["packing"], shipment["weight_kg"])


def report(threshold_kg, base_url=BASE_URL):
    """Print the report. Returns the exit code the process should use."""
    try:
        shipments = fetch_shipments(base_url)
    except requests.HTTPError as error:
        print("the depot answered with an error: %s" % error.response.status_code)
        return 1
    except requests.RequestException as error:
        print("could not reach the depot: %s" % error.__class__.__name__)
        return 1

    heavy = heavy_shipments(shipments, threshold_kg)
    if not heavy:
        print("nothing at or above %dkg" % threshold_kg)
    else:
        print("%d at or above %dkg" % (len(heavy), threshold_kg))
        for shipment in heavy:
            print("  " + describe(shipment))

    missing = unweighed(shipments)
    if missing:
        print("no weight recorded for: %s" % ", ".join(str(i) for i in missing))
    return 0


def main(argv):
    threshold = DEFAULT_THRESHOLD_KG
    if len(argv) > 2:
        print("usage: depotwatch.py [threshold_kg]")
        return 2
    if len(argv) == 2:
        try:
            threshold = int(argv[1])
        except ValueError:
            print("threshold must be a whole number of kg")
            return 2
    return report(threshold)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
