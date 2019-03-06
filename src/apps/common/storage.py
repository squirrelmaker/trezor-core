from micropython import const
from ubinascii import hexlify

from trezor import config
from trezor.crypto import random

from apps.common import cache

HOMESCREEN_MAXSIZE = 16384

_STORAGE_VERSION = b"\x02"
_FALSE_BYTE = b"\x00"
_TRUE_BYTE = b"\x01"
_COUNTER_HEAD_LEN = 4
_COUNTER_TAIL_LEN = 8
_MNEMONIC_STANDARD_BIP39 = b"\x00"
_MNEMONIC_STANDARD_SLIP39 = b"\x01"

# fmt: off
_APP                = const(0x01)  # app namespace
_DEVICE_ID          = const(0x00)  # bytes
_VERSION            = const(0x01)  # int
_MNEMONIC           = const(0x02)  # bytes
_LANGUAGE           = const(0x03)  # str
_LABEL              = const(0x04)  # str
_USE_PASSPHRASE     = const(0x05)  # bool (0x01 or empty)
_HOMESCREEN         = const(0x06)  # bytes
_NEEDS_BACKUP       = const(0x07)  # bool (0x01 or empty)
_FLAGS              = const(0x08)  # int
_U2F_COUNTER        = const(0x09)  # int
_PASSPHRASE_SOURCE  = const(0x0A)  # int
_UNFINISHED_BACKUP  = const(0x0B)  # bool (0x01 or empty)
_AUTOLOCK_DELAY_MS  = const(0x0C)  # int
_NO_BACKUP          = const(0x0D)  # bool (0x01 or empty)
_MNEMONIC_STANDARD  = const(0x0E)  # int (0x00 for BIP39, 0x01 for SLIP-39)

_SLIP39             = const(0x02)  # SLIP-39 namespace
_SLIP39_IN_PROGRESS = const(0x00)  # bool
_SLIP39_ID          = const(0x01)  # bytes
_SLIP39_THRESHOLD   = const(0x02)  # int
_SLIP39_REMAINING   = const(0x03)  # int
_SLIP39_SHARES      = const(0x04)  # bytes
# fmt: on


def set_slip39_in_progress(val: bool):
    _set_bool(_SLIP39, _SLIP39_IN_PROGRESS, val)


def is_slip39_in_progress():
    return _get_bool(_SLIP39, _SLIP39_IN_PROGRESS)


def set_slip39_id(id: bytes):
    config.set(_SLIP39, _SLIP39_ID, id)


def get_slip39_id() -> bytes:
    # TODO add 'set_str()' ?
    return config.get(_SLIP39, _SLIP39_ID).decode()


def set_slip39_threshold(threshold: int):
    # TODO add 'set_int()' or 'set_uint8' ?
    config.set(_SLIP39, _SLIP39_THRESHOLD, threshold.to_bytes(1, "big"))


def get_slip39_threshold() -> int:
    return int.from_bytes(config.get(_SLIP39, _SLIP39_THRESHOLD), "big")


def set_slip39_remaining(remaining: int):
    config.set(_SLIP39, _SLIP39_REMAINING, remaining.to_bytes(1, "big"))


def get_slip39_remaining() -> int:
    return int.from_bytes(config.get(_SLIP39, _SLIP39_REMAINING), "big")


def get_slip39_words_count() -> int:
    if not is_slip39_in_progress():
        raise RuntimeError("SLIP 39 not in progress")
    shares = get_slip39_shares()
    if len(shares[0]) == 16:
        return 20
    elif len(shares[0]) == 32:
        return 33
    else:
        raise RuntimeError("Unknown SLIP-39 share length")


def set_slip39_shares(data: bytes, threshold: int, remaining: int):
    current = [bytes([0xFF] * len(data))] * threshold
    index = threshold - remaining
    current[index] = data

    for i, s in enumerate(get_slip39_shares()):
        current[i] = s

    print("STORING:")
    to_store = b"".join(current)
    print(hexlify(to_store))
    config.set(_SLIP39, _SLIP39_SHARES, to_store, True)


def get_slip39_shares() -> list:
    shares = config.get(_SLIP39, _SLIP39_SHARES, True)
    if not shares:
        return []
    length = len(shares) // get_slip39_threshold()
    s = []
    for i in range(0, len(shares), length):
        share = shares[i : i + length]
        if share != b"\xFF" * 16:
            s.append(share)
    return s


def set_slip39_secret(secret: bytes):
    config.set(_APP, _MNEMONIC, secret)
    config.set(_APP, _MNEMONIC_STANDARD, _MNEMONIC_STANDARD_SLIP39)
    _init()


def clear_slip39_data():
    config.delete(_SLIP39, _SLIP39_IN_PROGRESS)
    config.delete(_SLIP39, _SLIP39_ID)
    config.delete(_SLIP39, _SLIP39_REMAINING)
    config.delete(_SLIP39, _SLIP39_THRESHOLD)
    config.delete(_SLIP39, _SLIP39_SHARES)


def _set_bool(app: int, key: int, value: bool, public: bool = False) -> None:
    if value:
        config.set(app, key, _TRUE_BYTE, public)
    else:
        config.set(app, key, _FALSE_BYTE, public)


def _get_bool(app: int, key: int, public: bool = False) -> bool:
    return config.get(app, key, public) == _TRUE_BYTE


def _new_device_id() -> str:
    return hexlify(random.bytes(12)).decode().upper()


def get_device_id() -> str:
    dev_id = config.get(_APP, _DEVICE_ID, True)  # public
    if not dev_id:
        dev_id = _new_device_id().encode()
        config.set(_APP, _DEVICE_ID, dev_id, True)  # public
    return dev_id.decode()


def is_initialized() -> bool:
    return bool(config.get(_APP, _VERSION)) and not bool(
        config.get(_SLIP39, _SLIP39_IN_PROGRESS)
    )


def get_label() -> str:
    label = config.get(_APP, _LABEL, True)  # public
    if label is None:
        return None
    return label.decode()


def get_mnemonic() -> bytes:
    mnemonic = config.get(_APP, _MNEMONIC)
    if mnemonic is None:
        return None
    return mnemonic


def get_mnemonic_standard() -> int:
    result = config.get(_APP, _MNEMONIC_STANDARD)
    return result


def has_passphrase() -> bool:
    return _get_bool(_APP, _USE_PASSPHRASE)


def get_homescreen() -> bytes:
    return config.get(_APP, _HOMESCREEN, True)  # public


def set_bip39_mnemonic(mnemonic: bytes, needs_backup: bool, no_backup: bool) -> None:
    config.set(_APP, _MNEMONIC, mnemonic)
    config.set(_APP, _MNEMONIC_STANDARD, _MNEMONIC_STANDARD_BIP39)
    _init(needs_backup, no_backup)


def _init(needs_backup=False, no_backup=False):
    config.set(_APP, _VERSION, _STORAGE_VERSION)
    _set_bool(_APP, _NO_BACKUP, no_backup)
    if not no_backup:
        _set_bool(_APP, _NEEDS_BACKUP, needs_backup)


def needs_backup() -> bool:
    return _get_bool(_APP, _NEEDS_BACKUP)


def set_backed_up() -> None:
    config.set(_APP, _NEEDS_BACKUP, b"")


def unfinished_backup() -> bool:
    return _get_bool(_APP, _UNFINISHED_BACKUP)


def set_unfinished_backup(state: bool) -> None:
    _set_bool(_APP, _UNFINISHED_BACKUP, state)


def no_backup() -> bool:
    return _get_bool(_APP, _NO_BACKUP)


def get_passphrase_source() -> int:
    b = config.get(_APP, _PASSPHRASE_SOURCE)
    if b == b"\x01":
        return 1
    elif b == b"\x02":
        return 2
    else:
        return 0


def load_settings(
    label: str = None,
    use_passphrase: bool = None,
    homescreen: bytes = None,
    passphrase_source: int = None,
) -> None:
    if label is not None:
        config.set(_APP, _LABEL, label.encode(), True)  # public
    if use_passphrase is not None:
        _set_bool(_APP, _USE_PASSPHRASE, use_passphrase)
    if homescreen is not None:
        if homescreen[:8] == b"TOIf\x90\x00\x90\x00":
            if len(homescreen) <= HOMESCREEN_MAXSIZE:
                config.set(_APP, _HOMESCREEN, homescreen, True)  # public
        else:
            config.set(_APP, _HOMESCREEN, b"", True)  # public
    if passphrase_source is not None:
        if passphrase_source in [0, 1, 2]:
            config.set(_APP, _PASSPHRASE_SOURCE, bytes([passphrase_source]))


def get_flags() -> int:
    b = config.get(_APP, _FLAGS)
    if b is None:
        return 0
    else:
        return int.from_bytes(b, "big")


def set_flags(flags: int) -> None:
    b = config.get(_APP, _FLAGS)
    if b is None:
        b = 0
    else:
        b = int.from_bytes(b, "big")
    flags = (flags | b) & 0xFFFFFFFF
    if flags != b:
        config.set(_APP, _FLAGS, flags.to_bytes(4, "big"))


def get_autolock_delay_ms() -> int:
    b = config.get(_APP, _AUTOLOCK_DELAY_MS)
    if b is None:
        return 10 * 60 * 1000
    else:
        return int.from_bytes(b, "big")


def set_autolock_delay_ms(delay_ms: int) -> None:
    if delay_ms < 60 * 1000:
        delay_ms = 60 * 1000
    config.set(_APP, _AUTOLOCK_DELAY_MS, delay_ms.to_bytes(4, "big"))


def next_u2f_counter() -> int:
    return config.next_counter(_APP, _U2F_COUNTER, True)  # writable when locked


def set_u2f_counter(cntr: int) -> None:
    config.set_counter(_APP, _U2F_COUNTER, cntr, True)  # writable when locked


def wipe():
    config.wipe()
    cache.clear()


def init_unlocked():
    # Check for storage version upgrade.
    version = config.get(_APP, _VERSION)
    if version == b"\x01":
        # Make the U2F counter public and writable even when storage is locked.
        counter = config.get(_APP, _U2F_COUNTER)
        if counter is not None:
            config.set_counter(
                _APP, _U2F_COUNTER, counter, True
            )  # writable when locked
            config.delete(_APP, _U2F_COUNTER)
        config.set(_APP, _VERSION, _STORAGE_VERSION)
