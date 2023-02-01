from itertools import groupby


def longest(lst, string):
    lst = [[*g]
           for k, g in groupby(enumerate(lst), key=lambda x: x[1]) if k == string]
    if len(lst) > 0:
        group = max(lst, key=len)
        return group[0][0], 1 + group[-1][0]
    else:
        return [0, 0]


def remove_ff(row):
    target = longest(row, "FF")
    start = target[0] + 1
    end = target[1]
    length = end - start
    if length > 1:
        row[start:end] = ["--"] * length
    return row


def image_to_shattermap(img):
    width = img.size[0]
    values = []
    row = []
    for idx in range(int(len(img.pixels) / 4) + 1):
        if idx % width == 0:
            row = remove_ff(row)
            values.append(row)
            row = []
        try:
            value = int(img.pixels[idx * 4] * 255)
            if value == 0:
                value = "##"
            elif value <= 15:
                value = "0{0:X}".format(value)
            else:
                value = "{0:X}".format(value)
            row.append(value)
        except:
            continue

    return reversed(values)
