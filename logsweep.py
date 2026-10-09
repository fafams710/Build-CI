"""Summarise a directory of log files.

    python logsweep.py samples/logs
"""

import os
import sys

LEVELS = ("INFO", "WARN", "ERROR")


def sweep(directory):
    """Print a per-file report for every .log file in a directory.

    Returns the total number of ERROR lines found.
    """
    total_errors = 0
    files_read = 0
    worst = None
    print("sweeping %s" % directory)
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".log"):
            continue
        path = os.path.join(directory, name)
        counts = {level: 0 for level in LEVELS}
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                for level in LEVELS:
                    if line.startswith(level):
                        counts[level] += 1
                        break
        files_read += 1
        total_errors += counts["ERROR"]
        print("  %-16s %3d info %3d warn %3d error"
              % (name, counts["INFO"], counts["WARN"], counts["ERROR"]))
        if worst is None or counts["ERROR"] > worst[1]:
            worst = (name, counts["ERROR"])
    if files_read == 0:
        print("no log files here")
        return 0
    print("%d errors across %d files" % (total_errors, files_read))
    if worst is not None and worst[1] > 0:
        print("worst file: %s" % worst[0])
    return total_errors


def main(argv):
    if len(argv) != 2:
        print("usage: logsweep.py <directory>")
        return 2
    if not os.path.isdir(argv[1]):
        print("not a directory: %s" % argv[1])
        return 1
    errors = sweep(argv[1])
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
