def prettyhex(num):
    hex_pretty = str(hex(num))[2:]
    if len(hex_pretty) == 1:
        hex_pretty = "000" + hex_pretty
    if len(hex_pretty) == 2:
        hex_pretty = "00" + hex_pretty
    if len(hex_pretty) == 3:
        hex_pretty = "0" + hex_pretty
    return hex_pretty

def prettyhex2(num):
    hex_pretty = str(hex(num))[2:]
    if len(hex_pretty) == 1:
        hex_pretty = "0" + hex_pretty
    return hex_pretty
