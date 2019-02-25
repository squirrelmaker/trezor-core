from typing import *

from trezorcrypto import random

from .slip39_wordlist import words


def find_word(prefix: str) -> Optional[str]:
    """
    Return the first word from the wordlist starting with prefix.
    """
    raise NotImplementedError()


# extmod/modtrezorcrypto/modtrezorcrypto-bip39.h
def complete_word(prefix: str) -> int:
    """
    Return possible 1-letter suffixes for given word prefix.
    Result is a bitmask, with 'a' on the lowest bit, 'b' on the second lowest, etc.
    """
    raise NotImplementedError()


def generate(count: int, threshold: int, strength: int):
    """
    Generate a mnemonic of given strength (128 or 256 bits).
    ! TODO mocked
    """
    if strength not in (128, 256):
        raise ValueError("Invalid strength for SLIP-39")

    mnemonics = list()
    id = [words[random.uniform(1024)] for _ in range(3)]

    for index in range(count):
        t_i = words[threshold << 5 | index]
        share = [words[random.uniform(1024)] for _ in range(strength // 10 + 1)]
        checksum = [words[random.uniform(1024)] for _ in range(3)]
        mnemonic = id + [t_i] + share + checksum
        mnemonics.append(" ".join(mnemonic))

    return mnemonics


def from_data(data: bytes, count: int, threshold: int) -> str:
    """
    Generate a mnemonic from given data.
    """
    raise NotImplementedError()


def check(mnemonic: str) -> bool:
    """
    Check whether given mnemonic is valid.
    """
    raise NotImplementedError()


def seed(mnemonic: str, passphrase: str) -> bytes:
    """
    Generate seed from mnemonic and passphrase.
    """
    raise NotImplementedError()
