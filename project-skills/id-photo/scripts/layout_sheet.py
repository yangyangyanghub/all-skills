from PIL import Image, ImageDraw

SHEETS = {"5inch": (1050, 1500), "6inch": (1500, 1800)}


def plan_grid(sheet_size, photo_size, gap=20):
    sw, sh = sheet_size
    pw, ph = photo_size
    cols = (sw + gap) // (pw + gap)
    rows = (sh + gap) // (ph + gap)
    return max(1, cols), max(1, rows)


def make_sheet(photo, sheet_key, gap=20):
    SW, SH = SHEETS[sheet_key]
    sheet = Image.new("RGB", (SW, SH), "white")
    cols, rows = plan_grid((SW, SH), photo.size, gap)

    grid_w = cols * photo.width + (cols - 1) * gap
    grid_h = rows * photo.height + (rows - 1) * gap
    mx = (SW - grid_w) // 2
    my = (SH - grid_h) // 2

    draw = ImageDraw.Draw(sheet)
    for r in range(rows):
        for c in range(cols):
            x = mx + c * (photo.width + gap)
            y = my + r * (photo.height + gap)
            sheet.paste(photo, (x, y))
            draw.rectangle([x - 1, y - 1, x + photo.width, y + photo.height], outline=(190, 190, 190), width=1)
    return sheet
