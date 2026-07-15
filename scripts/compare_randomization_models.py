import argparse
import csv
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "bot_comparison"
SEED_ENV_VAR = "TRUST_GAME_BOT_RANDOM_SEED"
CONFIGS = [
    ("current_period_level", "trust_game_randomized"),
]


def find_otree_executable():
    local_exe = ROOT / ".venv" / "Scripts" / "otree.exe"
    if local_exe.exists():
        return str(local_exe)
    found = shutil.which("otree")
    if found:
        return found
    raise RuntimeError("Could not find otree.exe or otree on PATH.")


def prepare_run_project(run_root):
    run_root.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "settings.py", run_root / "settings.py")
    shutil.copytree(
        ROOT / "trust_game",
        run_root / "trust_game",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(
        ROOT / "_static",
        run_root / "_static",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def run_otree_test(config_name, participants, export_dir, seed):
    export_dir.mkdir(parents=True, exist_ok=True)
    run_root = export_dir / "_run_project"
    data_dir = export_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    prepare_run_project(run_root)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env[SEED_ENV_VAR] = str(seed)
    cmd = [
        find_otree_executable(),
        "test",
        config_name,
        str(participants),
        "--export",
        str(data_dir),
    ]
    result = subprocess.run(
        cmd,
        cwd=run_root,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        tail = "\n".join((result.stdout + result.stderr).splitlines()[-80:])
        raise RuntimeError(f"Bot run failed for {config_name}:\n{tail}")


def find_custom_export(export_dir):
    matches = list(export_dir.rglob("trust_game_custom.csv"))
    if not matches:
        raise FileNotFoundError(f"No trust_game_custom.csv found in {export_dir}")
    return matches[0]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def as_decimal(value):
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal("0")


def is_true(value):
    return str(value).lower() in {"true", "1", "yes"}


def real_rows(rows):
    return [row for row in rows if not is_true(row.get("is_practice_round"))]


def metric_average(total, count):
    if not count:
        return Decimal("0")
    return total / Decimal(count)


def summarize_rows(rows):
    rows_real = real_rows(rows)
    real_count = len(rows_real)
    proposer_total = sum(as_decimal(r.get("proposer_payoff")) for r in rows_real)
    responder_total = sum(as_decimal(r.get("responder_payoff")) for r in rows_real)
    sent_total = sum(as_decimal(r.get("offer")) for r in rows_real)
    available_total = sum(as_decimal(r.get("multiplied_amount")) for r in rows_real)
    returned_total = sum(as_decimal(r.get("delivered_return")) for r in rows_real)
    multiplier_total = sum(as_decimal(r.get("realized_multiplier")) for r in rows_real)
    return {
        "all_export_rows": Decimal(len(rows)),
        "real_game_rows": Decimal(real_count),
        "practice_rows": Decimal(len(rows) - real_count),
        "total_proposer_payoff_real_rounds": proposer_total,
        "total_responder_payoff_real_rounds": responder_total,
        "average_proposer_payoff_real_rounds": metric_average(
            proposer_total, real_count
        ),
        "average_responder_payoff_real_rounds": metric_average(
            responder_total, real_count
        ),
        "total_points_sent_real_rounds": sent_total,
        "total_points_available_real_rounds": available_total,
        "total_points_returned_real_rounds": returned_total,
        "average_realized_multiplier_real_rounds": metric_average(
            multiplier_total, real_count
        ),
        "high_multiplier_rows_real_rounds": Decimal(
            sum(is_true(r.get("high_multiplier_applied")) for r in rows_real)
        ),
        "low_multiplier_rows_real_rounds": Decimal(
            sum(not is_true(r.get("high_multiplier_applied")) for r in rows_real)
        ),
        "random_multiplier_condition_rows_real_rounds": Decimal(
            sum(is_true(r.get("random_multiplier_condition")) for r in rows_real)
        ),
        "fixed_multiplier_condition_rows_real_rounds": Decimal(
            sum(not is_true(r.get("random_multiplier_condition")) for r in rows_real)
        ),
        "picture_condition_rows_real_rounds": Decimal(
            sum(is_true(r.get("picture_condition")) for r in rows_real)
        ),
    }


def summary_table(rows):
    summary = summarize_rows(rows)
    return [
        {
            "metric": metric,
            "current_period_level": str(value),
        }
        for metric, value in summary.items()
    ]


def comparison_key(row):
    return (
        row.get("otree_round", ""),
        row.get("proposer_name", ""),
        row.get("responder_name", ""),
    )


def round_rows(current_rows):
    current_by_key = {comparison_key(row): row for row in current_rows}
    rows = []
    for key in sorted(current_by_key, key=lambda k: (int(k[0]), k[1], k[2])):
        current = current_by_key.get(key, {})
        current_proposer = as_decimal(current.get("proposer_payoff"))
        current_responder = as_decimal(current.get("responder_payoff"))
        rows.append(
            {
                "otree_round": key[0],
                "period": current.get("period"),
                "round_in_period": current.get("round_in_period"),
                "is_practice_round": current.get("is_practice_round"),
                "proposer_name": key[1],
                "responder_name": key[2],
                "treatment": current.get("treatment_label", ""),
                "realized_multiplier": current.get("realized_multiplier", ""),
                "offer": current.get("offer"),
                "points_available": current.get("multiplied_amount", ""),
                "points_returned": current.get("delivered_return", ""),
                "proposer_payoff": str(current_proposer),
                "responder_payoff": str(current_responder),
            }
        )
    return rows


def column_name(index):
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def xlsx_value(value):
    if value is None:
        return "", None
    text = str(value)
    if text == "":
        return "", None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text, "string"
    return str(number), "number"


def worksheet_xml(rows):
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{column_name(col_index)}{row_index}"
            cleaned, cell_type = xlsx_value(value)
            if cell_type == "number":
                cells.append(f'<c r="{cell_ref}"><v>{cleaned}</v></c>')
            elif cell_type == "string":
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(cleaned)}</t></is></c>'
                )
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        "</worksheet>"
    )


def write_xlsx(path, sheets):
    workbook_sheets = []
    workbook_rels = []
    content_overrides = []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(1, len(sheets) + 1)
            )
            + "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        )

        for index, (sheet_name, rows) in enumerate(sheets, start=1):
            safe_name = sheet_name[:31]
            workbook_sheets.append(
                f'<sheet name={quoteattr(safe_name)} sheetId="{index}" r:id="rId{index}"/>'
            )
            workbook_rels.append(
                f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
            )
            content_overrides.append(index)
            zf.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml(rows))

        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(workbook_sheets)}</sheets>'
            "</workbook>",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(workbook_rels)
            + "</Relationships>",
        )


def table_to_sheet(headers, rows):
    return [headers] + [[row.get(header, "") for header in headers] for row in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--participants", type=int, default=10)
    parser.add_argument("--seed", default="20260715")
    args = parser.parse_args()

    if args.participants % 2:
        raise SystemExit("Participant count must be even.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"comparison_{timestamp}"
    export_root = output_dir / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {}
    for label, config_name in CONFIGS:
        config_export_dir = export_root / label
        print(f"Running {config_name} with {args.participants} participants...")
        run_otree_test(config_name, args.participants, config_export_dir, args.seed)
        export_path = find_custom_export(config_export_dir)
        data[label] = read_csv(export_path)
        shutil.copy(export_path, output_dir / f"{label}_full_data.csv")

    current_rows = data["current_period_level"]
    summary = summary_table(current_rows)
    rounds = round_rows(current_rows)

    summary_headers = [
        "metric",
        "current_period_level",
    ]
    round_headers = list(rounds[0].keys()) if rounds else []
    current_headers = list(current_rows[0].keys())

    write_csv(output_dir / "summary.csv", summary_headers, summary)
    write_csv(output_dir / "round_data.csv", round_headers, rounds)

    workbook_path = output_dir / "trust_game_bot_comparison.xlsx"
    write_xlsx(
        workbook_path,
        [
            ("Summary", table_to_sheet(summary_headers, summary)),
            ("Round Data", table_to_sheet(round_headers, rounds)),
            (
                "Current Full Data",
                table_to_sheet(current_headers, current_rows),
            ),
        ],
    )

    print(f"Created {workbook_path}")
    print(f"Created {output_dir / 'summary.csv'}")
    print(f"Created {output_dir / 'round_data.csv'}")


if __name__ == "__main__":
    main()
