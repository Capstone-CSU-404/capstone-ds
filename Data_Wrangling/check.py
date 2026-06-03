import csv
INPUT_FILE  = "C:\Users\asus3\Documents\CPSTNPROJECT\capstone-ds\Data_Wrangling\Data_Fixed\linkedin_dsatscdelim.csv"
# Cek berapa baris yang bermasalah
bad_lines = []
with open(INPUT_FILE, encoding="utf-8-sig", errors="replace") as f:
    reader = csv.reader(f)
    header = next(reader)
    n_cols = len(header)
    print(f"Jumlah kolom header: {n_cols}")
    print(f"Kolom: {header}")
    for i, row in enumerate(reader, start=2):
        if len(row) != n_cols:
            bad_lines.append((i, len(row), row[:5]))  # tampilkan 5 field pertama

print(f"\nTotal baris bermasalah: {len(bad_lines)}")
for line_num, n_fields, preview in bad_lines[:10]:
    print(f"  Line {line_num}: punya {n_fields} fields | preview: {preview}")