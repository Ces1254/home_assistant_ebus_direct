# file get_param_value.py

from datetime import datetime, date
import asyncio
import logging

from .custom_decoders import DECODER_TABLE

###############################################################################
# LOGGING
###############################################################################

_LOGGER = logging.getLogger(__name__)

###############################################################################
# Funtions to get/set the entities values
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

    # Call to a custom decoder, if defined
    decoder = meta.get("decoder")
    if decoder is not None:
        try:
            func = DECODER_TABLE.get(decoder)
            if func:
                return func(value)
        except Exception as err:
            _LOGGER.warning(
                "Decoder failed for %s: %s",
                meta.get("name"),
                err,
            )
            return None
    
    if "=" in value:
        value = value.split("=",1)[1].strip()  # if verbose, remove name
        value = value.split("[",1)[0].strip()  # and comments
        if " " in value and meta.get("numeric"): value=value.split(" ",1)[0]  # and, if param is numeric, strip unit, if any
    
    return value

async def read_by_tag (client, meta):
    tag = meta.get("ebus_read_tag") or meta.get("ebus_rw_tag")
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

async def write_by_tag (client, meta, value):
    tag = meta.get("ebus_rw_tag")
    circuit = meta.get("circuit")
    if (tag is None) or (circuit is None): return None
    _LOGGER.debug("writing on eBus for %s - %s", meta.get("name"), tag)
    opt = meta.get("ebus_write_cmd","")
    raw = await client.command(f"w -c {circuit} {tag} '{value}{opt}'")
    if ("done" in raw) or ("read timeout" in raw):
        return value
    
    _LOGGER.warning("ebusd write error for %s: %s", meta.get("name"), raw)
    return None

async def get_val_by_tag (client, meta):    
    value = await find_by_tag(client, meta)
    if value is None:
        value = await read_by_tag(client, meta)
        await asyncio.sleep(0.1)

    if value is None: 
        return None
    
    if meta.get("numeric"): 
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

async def set_val_by_tag (client, meta, value):
    
    raw = await write_by_tag(client, meta, value)

    if raw is None:
        return None

    meta["ebus_read_opt"] =" -f"
    await asyncio.sleep(0.5)
    raw = await read_by_tag(client, meta)
    await asyncio.sleep(0.1)

    if raw is not None and (meta.get("numeric") or (meta.get("options","") == "")): 
        try:
            read_back = float(raw)
        except ValueError:
            _LOGGER.warning("Error updating setpoint %s: %s", meta.get("name"), raw)
            return None

        step = meta.get("step", 0)

        min = value - step * .4
        max = value + step * .4
        if (read_back >= min) and (read_back <= max):
            return read_back
        else:
            _LOGGER.warning("Setpoint %s update failed", meta.get("name"))
            return None
    else:
        if value in raw:
            return raw
        else:
            _LOGGER.warning("Setpoint %s update failed", meta.get("name"))
            return None
