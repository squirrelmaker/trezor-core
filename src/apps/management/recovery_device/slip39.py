from trezor import wire
from trezor.crypto import slip39
from trezor.crypto.slip39 import Slip39Share

from apps.common import storage


def process_mnemonic(words) -> bytes:
    slip39share = slip39.parse_share(words)

    if not storage.is_slip39_in_progress():
        _start_slip39(slip39share)
        if slip39share.get_threshold() != 1:
            return None
    else:
        remaining = _next_slip39(slip39share)
        if remaining != 0:
            return None

    # combine shares and returns
    result = _combine()
    storage.set_slip39_secret(result)
    return result


def _combine():
    # TODO:
    # - combine them by calling slip39 functions
    # - return final seed presentation
    shares = storage.get_slip39_shares()
    return shares[0]


def dry_run(mnemonic):
    raise NotImplementedError()


def check(mnemonic):
    if not slip39.check(mnemonic):
        raise wire.ProcessError("Mnemonic is not valid")


def _start_slip39(s: Slip39Share):
    storage.set_slip39_in_progress(True)
    storage.set_slip39_shares(s.get_share(), s.get_threshold(), s.get_threshold())
    storage.set_slip39_id(s.get_identifier())
    storage.set_slip39_remaining(s.get_threshold() - 1)
    storage.set_slip39_threshold(s.get_threshold())


def _next_slip39(s: Slip39Share):
    if s.get_identifier() != storage.get_slip39_id():
        raise ValueError(
            "Share identifiers do not match %s vs %s",
            s.get_identifier(),
            storage.get_slip39_id(),
        )
    remaining = storage.get_slip39_remaining()
    storage.set_slip39_shares(s.get_share(), s.get_threshold(), remaining)
    remaining -= 1
    storage.set_slip39_remaining(remaining)
    return remaining


def save_to_storage(secret: bytes):
    storage.set_slip39_secret(secret)
    storage.clear_slip39_data()
