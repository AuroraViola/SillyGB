def prettyhex(num):
    hex_pretty = str(hex(num))[2:]
    if len(hex_pretty) == 1:
        hex_pretty = "0" + hex_pretty
    return hex_pretty
