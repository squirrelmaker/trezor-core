from trezor import wire
from trezor.crypto import bip39
from trezor.crypto.hashlib import sha256
from trezor.utils import consteq

from apps.common import storage


def dry_run(mnemonic: bytes):
    # TODO: this has changed, now we re comparing bytes instead of str
    digest_input = sha256(mnemonic).digest()
    digest_stored = sha256(storage.get_mnemonic()).digest()
    if consteq(digest_stored, digest_input):
        return True
    else:
        raise wire.ProcessError(
            "The seed is valid but does not match the one in the device"
        )


def process_mnemonic(words: list) -> bytes:
    words = " ".join(words)
    return words.encode()


def save_to_storage(mnemonic: bytes):
    storage.set_bip39_mnemonic(mnemonic=mnemonic, needs_backup=False, no_backup=False)


def check(mnemonic: bytes):
    return bip39.check(mnemonic.decode())
