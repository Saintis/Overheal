"""Utility functions for splitting a log by raid"""


def _write_lines(file_name, lines):
    with open(file_name, "w", encoding="utf-8") as f:
        f.writelines(lines)


def split_log(log, year=None):
    if year is None:
        year = "-"
    else:
        year = "-" + year

    # split log into parts for MC / BWL / ZG / Ony
    f = open(log, "r", encoding="utf-8")
    lines = f.readlines()

    line_buffer = []
    month = 0
    day = 0

    for line in lines:
        line_buffer.append(line)

        if "ENCOUNTER_END" in line:
            line_parts = line.split(",")
            boss = line_parts[2].strip('"')
            win = line_parts[5] == "1\n"

            if not win:
                continue

            date = line_parts[0].split()[0].split("/")

            month = int(date[0])
            day = int(date[1])

            if boss == "Ragnaros":
                file_name = f"MC{year}-{month:02d}-{day:02d}.txt"
                print(f'Found Molten Core raid. Saving to "{file_name}"')
                _write_lines(file_name, line_buffer)
                line_buffer.clear()

            elif boss == "Onyxia":
                file_name = f"Ony{year}-{month:02d}-{day:02d}.txt"
                print(f'Found Onyxia raid. Saving to "{file_name}"')
                _write_lines(file_name, line_buffer)
                line_buffer.clear()

            elif boss == "Nefarian":
                file_name = f"BWL{year}-{month:02d}-{day:02d}.txt"
                print(f'Found Blackwing Lair raid. Saving to "{file_name}"')
                _write_lines(file_name, line_buffer)
                line_buffer.clear()

            elif boss == "Hakkar":
                file_name = f"ZG{year}-{month:02d}-{day:02d}.txt"
                print(f'Found Zul\'Gurub raid. Saving to "{file_name}"')
                _write_lines(file_name, line_buffer)
                line_buffer.clear()

    _write_lines(f"rem{year}-{month:02d}-{day:02d}.txt", line_buffer)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser("Script for splitting a log into parts.")
    parser.add_argument("log", help="The logfile to split.")
    parser.add_argument("-y", "--year", help="The year the log was produced in. Only for output file name.")

    args = parser.parse_args(argv)
    split_log(args.log, year=args.year)


if __name__ == "__main__":
    main()
