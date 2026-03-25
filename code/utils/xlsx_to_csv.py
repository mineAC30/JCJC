import csv, re, openpyxl
from pathlib import Path

src = Path("model-motor/motor/mini4wd_motor_templates_by_motor.xlsx")
out_dir = Path("model-motor/motor")
out_dir.mkdir(parents=True, exist_ok=True)

wb = openpyxl.load_workbook(src, read_only=True)
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    safe_name = re.sub(r'[\\/:*?"<>|]', "_", sheet_name)
    out_path = out_dir / f"{safe_name}.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for row in ws.iter_rows(values_only=True):
            writer.writerow(["" if v is None else v for v in row])
    print(f"  written: {out_path.name}")
print("Done.")
