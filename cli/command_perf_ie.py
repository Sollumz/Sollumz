from pathlib import Path

CMD_ID = "sz_perf_ie"


def _print_stats(stats: dict[Path, dict[str, float]]):
    col_file = 30
    col = 10

    header1 = f"{'File':<{col_file}} {'IMPORT':^{col * 4}} {'EXPORT':^{col * 4}}"
    header2 = (
        f"{'':<{col_file}} "
        f"{'Avg':>{col}} {'Min':>{col}} {'Max':>{col}} {'σ':>{col}} "
        f"{'Avg':>{col}} {'Min':>{col}} {'Max':>{col}} {'σ':>{col}}"
    )

    print(header1)
    print(header2)
    print("-" * len(header2))

    for file in sorted(stats):
        v = stats[file]
        print(
            f"{file.name:<{col_file}} "
            f"{v['import_avg']:>{col}.6f} "
            f"{v['import_min']:>{col}.6f} "
            f"{v['import_max']:>{col}.6f} "
            f"{v['import_stdev']:>{col}.6f} "
            f"{v['export_avg']:>{col}.6f} "
            f"{v['export_min']:>{col}.6f} "
            f"{v['export_max']:>{col}.6f} "
            f"{v['export_stdev']:>{col}.6f}"
        )


def _save_stats_csv(stats: dict[Path, dict[str, float]], output: Path):
    import csv

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "file",
                "import_avg",
                "import_min",
                "import_max",
                "import_stdev",
                "export_avg",
                "export_min",
                "export_max",
                "export_stdev",
            ]
        )

        for file in sorted(stats):
            v = stats[file]
            writer.writerow(
                [
                    file.name,
                    v["import_avg"],
                    v["import_min"],
                    v["import_max"],
                    v["import_stdev"],
                    v["export_avg"],
                    v["export_min"],
                    v["export_max"],
                    v["export_stdev"],
                ]
            )


def _do_import_export(file: Path) -> tuple[float, float]:
    import bpy
    import time
    import tempfile

    bpy.ops.wm.read_homefile()

    t0 = time.perf_counter()
    bpy.ops.sollumz.import_assets(
        directory=str(file.parent.absolute()),
        files=[{"name": file.name}],
    )
    t1 = time.perf_counter()
    time_import = t1 - t0

    is_ytyp = ".ytyp" in file.name
    while file.suffix:
        file = file.with_suffix("")

    if is_ytyp:
        bpy.context.scene.ytyp_index = len(bpy.context.scene.ytyps) - 1

        export_op = bpy.ops.sollumz.export_ytyp_io
    else:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects[file.stem].select_set(True)

        export_op = bpy.ops.sollumz.export_assets

    with tempfile.TemporaryDirectory() as tmpdir:
        t0 = time.perf_counter()
        export_op(
            directory=str(tmpdir),
        )
        t1 = time.perf_counter()

    time_export = t1 - t0

    return time_import, time_export


def main(argv: list[str]) -> int:
    import sys
    import os
    import statistics
    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog=os.path.basename(sys.argv[0]) + " --command " + CMD_ID,
        description="Measure import/export performance.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Input asset files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output CSV file.",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--repeat",
        type=int,
        default=10,
        help="Number of import/export iterations per file.",
        required=False,
    )
    parser.add_argument(
        "-w",
        "--warmup",
        type=int,
        default=1,
        help="Number of warm-up iterations per file (not included in stats).",
        required=False,
    )
    args = parser.parse_args(argv)

    stats = {}
    for file in args.files:
        import_times = []
        export_times = []

        for _ in range(args.warmup):
            _do_import_export(file)

        for _ in range(args.repeat):
            timport, texport = _do_import_export(file)
            import_times.append(timport)
            export_times.append(texport)

        stats[file] = {
            "import_avg": sum(import_times) / len(import_times),
            "import_min": min(import_times),
            "import_max": max(import_times),
            "import_stdev": statistics.stdev(import_times),
            "export_avg": sum(export_times) / len(export_times),
            "export_min": min(export_times),
            "export_max": max(export_times),
            "export_stdev": statistics.stdev(export_times),
        }

    print()
    _print_stats(stats)

    if args.output:
        _save_stats_csv(stats, args.output)
        print(f"\nSaved CSV to {args.output}")

    return 0


CMD = (CMD_ID, main)
