import re
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding='utf-8')

# Read playlist_curated.m3u
with open('playlist_curated.m3u', 'r', encoding='utf-8') as f:
    lines = f.readlines()

channels = []
seen = set()

stream_counts = {}

# First pass: count streams per base name
for line in lines:
    if line.startswith('#EXTINF:'):
        m_grp = re.search(r'group-title="([^"]+)"', line)
        category = m_grp.group(1) if m_grp else 'General'
        full_name = line.split(',')[-1].strip()
        base_name = re.sub(r'\s+\d+$', '', full_name).strip()
        key = (category, base_name)
        stream_counts[key] = stream_counts.get(key, 0) + 1

# Second pass: preserve exact playlist order of distinct channels
for line in lines:
    if line.startswith('#EXTINF:'):
        m_grp = re.search(r'group-title="([^"]+)"', line)
        m_logo = re.search(r'tvg-logo="([^"]+)"', line)
        category = m_grp.group(1) if m_grp else 'General'
        full_name = line.split(',')[-1].strip()
        base_name = re.sub(r'\s+\d+$', '', full_name).strip()
        key = (category, base_name)
        if key not in seen:
            seen.add(key)
            channels.append({
                'category': category,
                'name': base_name,
                'streams': stream_counts[key],
                'logo': m_logo.group(1) if m_logo else ''
            })

print(f"Total unique channels found: {len(channels)}")

# Create Excel Workbook
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Curated Channels"

# Styling definitions
header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid") # Dark Navy
header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

zebra_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

headers = ["Serial", "Category", "Channel Name", "Total Streams", "Logo URL"]
ws.append(headers)

# Apply header formatting
for col_idx in range(1, len(headers) + 1):
    cell = ws.cell(row=1, column=col_idx)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
ws.row_dimensions[1].height = 28

# Populate data
for sl, ch in enumerate(channels, 1):
    row_idx = sl + 1
    row_data = [
        sl,
        ch['category'],
        ch['name'],
        ch['streams'],
        ch['logo']
    ]
    ws.append(row_data)

    fill = zebra_fill if sl % 2 == 0 else white_fill
    
    # Serial
    c_sl = ws.cell(row=row_idx, column=1)
    c_sl.alignment = Alignment(horizontal="center", vertical="center")
    c_sl.font = Font(name="Segoe UI", size=10, bold=True)
    c_sl.fill = fill
    c_sl.border = thin_border

    # Category
    c_cat = ws.cell(row=row_idx, column=2)
    c_cat.alignment = Alignment(horizontal="left", vertical="center")
    c_cat.font = Font(name="Segoe UI", size=10)
    c_cat.fill = fill
    c_cat.border = thin_border

    # Channel Name
    c_name = ws.cell(row=row_idx, column=3)
    c_name.alignment = Alignment(horizontal="left", vertical="center")
    c_name.font = Font(name="Segoe UI", size=10, bold=True)
    c_name.fill = fill
    c_name.border = thin_border

    # Streams count
    c_st = ws.cell(row=row_idx, column=4)
    c_st.alignment = Alignment(horizontal="center", vertical="center")
    c_st.font = Font(name="Segoe UI", size=10)
    c_st.fill = fill
    c_st.border = thin_border

    # Logo URL
    c_logo = ws.cell(row=row_idx, column=5)
    c_logo.alignment = Alignment(horizontal="left", vertical="center")
    c_logo.font = Font(name="Segoe UI", size=9, color="595959")
    c_logo.fill = fill
    c_logo.border = thin_border

    ws.row_dimensions[row_idx].height = 22

# Auto-adjust column widths
ws.column_dimensions['A'].width = 10
ws.column_dimensions['B'].width = 44
ws.column_dimensions['C'].width = 36
ws.column_dimensions['D'].width = 16
ws.column_dimensions['E'].width = 65

# Freeze header row
ws.freeze_panes = "A2"

excel_path = "curated_channels.xlsx"
wb.save(excel_path)
print(f"Successfully saved clean channel list to: {excel_path}")

# Also save CSV
import csv
csv_path = "curated_channels.csv"
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for sl, ch in enumerate(channels, 1):
        writer.writerow([sl, ch['category'], ch['name'], ch['streams'], ch['logo']])
print(f"Successfully saved clean channel CSV to: {csv_path}")
