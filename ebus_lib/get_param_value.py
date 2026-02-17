from datetime import datetime, date
import asyncio
import logging

###############################################################################
# LOGGING
###############################################################################

_LOGGER = logging.getLogger(__name__)


###############################################################################
# Custom decoders 
# ###############################################################################

BOOSTER_NOMINAL_POWER = 3
booster_status = False

def decode_set_floor_loop_temp (value: str):
    set_value = int(value[14:16], base = 16)+int(value[12:14], base = 16)/256
    return f"{set_value:.1f}"

def parse_mixer_command (value: str):
    if " / " in value:  # if hex string, take only the Master part of the message
        value=value.split("/",1)[0].strip()
        if len(value) > 20:
            value = value [10:12] + " " + value [16:20] + " " + value [20:] 
    return value

def correct_th_power (value: str):    
    if "=" in value:
        value=value.split("=",1)[1].strip()  # if verbose, remove name
    try:
        val = float (value.split(" ",1)[0].strip())
        if booster_status and val > 6.5:
            val = val + 1.95 - BOOSTER_NOMINAL_POWER * 0.975
    except:
        return value
    
    return f"{val:.1f}"
    
def correct_el_power (value: str):
    if "=" in value:
        value = value.split("=",1)[1].strip()  # if verbose, remove name
    try:
        val= float (value.split(" ",1)[0].strip())
        if booster_status and val > 3.4:
            val = val + 2 - BOOSTER_NOMINAL_POWER
    except:
        return value
    
    return f"{val:.1f}"

def check_booster_status (value: str):
    global booster_status
    booster_status = 'Operation' in value
    if "=" in value:
        value=value.split("=",1)[1].strip()  # if verbose, remove name
        value=value.split("[",1)[0].strip()

    return value

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


DECODER_TABLE = {
    "decode_set_floor_loop_temp": decode_set_floor_loop_temp,
    "parse_mixer_command": parse_mixer_command,
    "correct_th_power": correct_th_power,
    "correct_el_power": correct_el_power,
    "check_booster_status": check_booster_status,
    "decode_wolf_date": decode_wolf_date,
}

###############################################################################
# Funtions to get the entities values
###############################################################################

async def find_by_tag (client, meta):
    
    f_tags = meta.get("ebus_find_tag")
    if f_tags is None: return None
    m_tags = f_tags.split(",")

    max_age = meta.get("max_age")

    selected_raw = None

    for tag in m_tags:

        # Request verbosity only if freshness is required
        cmd = f"f -vvv {tag}" if max_age else f"f {tag}"

        raw = await client.command(cmd)

        if raw.startswith("ERR:"):
            _LOGGER.warning("Ebusd find error for %s: %s", tag, raw)
            continue

        if "no data" in raw:
            continue

        if "=" not in raw:
            _LOGGER.debug("Unexpected find response for %s: %s", tag, raw)
            continue

        # Freshness check
        if max_age:
            if "lastup=" not in raw:
                _LOGGER.debug("Unable to parse timestamp for %s", tag)
                continue

            try:
                ts_str = raw.split("lastup=", 1)[1].split(",", 1)[0].strip()
                last_update = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                age = (datetime.now() - last_update).total_seconds()

                if age > max_age:
                    _LOGGER.debug("Stale value for %s (age %.1fs > %ss)", tag, age, max_age)
                    continue
            except Exception as err:
                _LOGGER.warning("Failed to parse timestamp for %s: %s", tag, err)
                continue

        # success
        selected_raw = raw
        break

    if selected_raw is None:
        return None

    raw = selected_raw

    # --- Parse values ---
    tags_part, values_part = raw.split("=", 1)
    values_part = values_part.strip()

    # Strip optional circuit prefix (bm, hc, bc, ...)
    if " " in tags_part:
        tags_part = tags_part.split(" ", 1)[1].strip()

    
    if ";" in values_part:  # Multi-value message
        tags = tags_part.split("_")
        values = [v.strip() for v in values_part.split(";")]

        try:
            idx = tags.index(tag)
            value = values[idx] if idx < len(values) else None
        
        except ValueError:
            return None
    else:
        value = values_part # Single-value message

    decoder = meta.get("decoder")
    if decoder is not None:
        try:
            func = DECODER_TABLE.get(decoder)
            if func:
                value = func(value)
                return value
        except Exception as err:
            _LOGGER.warning(
                "Decoder failed for %s: %s",
                meta.get("name"),
                err,
            )
            return None
    
    if "=" in value:
        value=value.split("=",1)[1].strip()  # if verbose, remove name
        value= value.split("[",1)[0].strip() # and comments
        if " " in value and meta.get("numeric"): value=value.split(" ",1)[0]  # and, if param is numeric, strip unit, if any
    
    return value

async def read_by_tag (client, meta):
    tag = meta.get("ebus_read_tag")
    if tag is None: return None
    _LOGGER.debug("reading on eBus for %s - %s", meta.get("name"), tag)
    max_age = meta.get("max_age")
    opt = meta.get("ebus_read_opt","")
    if max_age:
        opt = f"-m {max_age} {opt}" 
    value = await client.command(f"r {opt} {tag}")
    if value.startswith("ERR:"):
        _LOGGER.warning("ebusd read error for %s: %s", meta.get("name"), value)
        return None
    return value



async def get_val_by_tag (client, meta):    
    value = await find_by_tag(client, meta)
    if value is None:
        value = await read_by_tag(client, meta)
        await asyncio.sleep(0.1)
    if value is not None and meta.get("numeric"): 
        try:
            f_val = float(value)
        except ValueError:
            _LOGGER.warning("Invalid numeric value for %s: %s", meta.get("name"), value)
            return None

        vmin = meta.get("min")
        vmax = meta.get("max")

        if ((vmin is not None and f_val < vmin) or (vmax is not None and f_val > vmax)):
            _LOGGER.warning("Out-of-range value for %s: %s (expected %s–%s)",
                meta.get("name"), f_val, vmin, vmax, )
            return None             
    return value
