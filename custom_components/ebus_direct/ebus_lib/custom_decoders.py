# file custom_decoders.py

###############################################################################
# Custom decoders 
###############################################################################

###############################################################################

def decode_set_floor_loop_temp (value: str):
    """
    Parses the Hex command sent to the mixer module to extract the 
    floor temperature setting.
    """
    if len(value) < 18: return None # if the hex string is too short, return with None
    # extract the temp as D2B encoded in lEnd in the master part of the MS message    
    set_value = int(value[14:16], base=16) + int(value[12:14], base=16) / 256
    return f"{set_value:.1f}"

###############################################################################

def decode_wolf_date(value):
    """
    Decodes a 16-bit integer into a Wolf date string (DD.MM.YYYY).
    Format: Bits 0-4: Day, Bits 5-8: Month, Bits 9-15: Year offset from 2000.
    """

    if "=" in value:
        value = value.split("=",1)[1].strip()  # if verbose, remove name

    try:
        val = int (value.split(" ",1)[0].strip())
    
        day = (val & 0x1F) + 1               # Mask first 5 bits
        month = ((val >> 5) & 0x0F) + 1      # Shift 5, mask 4 bits
        year = ((val >> 9) & 0x7F) + 2000    # Shift 9, mask 7 bits

        d = date(year, month, day)

    except:
        return None  # if not a good date, swallow the value
    
    return d.strftime("%d/%m/%Y")

###############################################################################

def parse_mixer_command (value: str):
    """
    Returns only relevant portion of the Hex command sent by the BM-2
    unit to the mixer module.
    """
    if " / " in value:  # if hex string, take only the Master part of the message
        value=value.split("/",1)[0].strip()
        if len(value) > 20:
            value = value [10:12] + " " + value [16:20] + " " + value [20:] 
    return value

###############################################################################

BOOSTER_NOMINAL_POWER = 3
BOOSTER_ACTUAL_POWER = 2
booster_status = False

def check_booster_status (value: str):
    """
    Registers in booster_status whether the electric booster is in operation
    No change of the message returned, other than stripping the comment.
    """
    global booster_status
    booster_status = 'Operation' in value
    if "=" in value:
        value=value.split("=",1)[1].strip()  # if verbose, remove name
        value=value.split("[",1)[0].strip()

    return value

###############################################################################

def correct_th_power (value: str):    
    """
    Corrects the thermal power reported by the FHA unit when the electric
    booster is in operation. The efficiency is assumed as 95%.
    """
    if "=" in value:
        value=value.split("=",1)[1].strip()  # if verbose, remove name
    try:
        val = float (value.split(" ",1)[0].strip())
        if booster_status and val > 6.5:
            val = val + (BOOSTER_ACTUAL_POWER - BOOSTER_NOMINAL_POWER) * 0.95
    except:
        return value
    
    return f"{val:.1f}"

###############################################################################
    
def correct_el_power (value: str):
    """
    Corrects the electric power reported by the FHA unit when the electric
    booster is in operation.
    """
    if "=" in value:
        value = value.split("=",1)[1].strip()  # if verbose, remove name
    try:
        val= float (value.split(" ",1)[0].strip())
        if booster_status and val > 3.4:
            val = val + BOOSTER_ACTUAL_POWER - BOOSTER_NOMINAL_POWER
    except:
        return value
    
    return f"{val:.1f}"

###############################################################################

DECODER_TABLE = {
    "decode_set_floor_loop_temp": decode_set_floor_loop_temp,
    "parse_mixer_command": parse_mixer_command,
    "correct_th_power": correct_th_power,
    "correct_el_power": correct_el_power,
    "check_booster_status": check_booster_status,
    "decode_wolf_date": decode_wolf_date,
}

