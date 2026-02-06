from pathlib import Path
import csv
from .shared import asset_path


def test_cli_perf_ie(tmp_path: Path):
    from ..cli.command_perf_ie import main

    output_csv = tmp_path / "times.csv"
    main(
        [
            "-r",
            "2",
            "-w",
            "1",
            "-o",
            str(output_csv),
            str(asset_path("sollumz_cube.ydr.xml")),
            str(asset_path("sollumz_cube.yft.xml")),
        ]
    )

    assert output_csv.is_file()
    with output_csv.open(newline="") as f:
        rows = list(csv.reader(f))

    assert len(rows) == 3, "CSV should have 3 rows (header + 2 files)"
    assert rows[0][0] == "file"
    assert rows[1][0] == "sollumz_cube.ydr.xml"
    assert rows[2][0] == "sollumz_cube.yft.xml"
