from typing import *

from trezorcrypto import random

from .slip39_wordlist import words

SHARE_LENGTHS = (20, 33)


class Slip39Share:
    def __init__(
        self, identifier: list, threshold: int, index: int, share: bytes, checksum: list
    ):
        self.identifier = identifier
        self.threshold = threshold
        self.index = index
        self.share = share
        self.checksum = checksum

    def get_identifier(self):
        return self.identifier

    def get_threshold(self):
        return self.threshold

    def get_share(self):
        return self.share


def find_word(prefix: str) -> Optional[str]:
    """
    Return the first word from the wordlist starting with prefix.
    """
    raise NotImplementedError()


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


def parse_share(mnemonic: list):
    # TODO validate checksum
    t_i = words.index(mnemonic[3])
    threshold = t_i >> 5
    print(threshold)
    index = t_i & 0x1F
    print(index)
    return Slip39Share(
        " ".join(mnemonic[:3]),
        threshold,
        index,
        mnemonic_to_bytes(mnemonic[4:-3]),
        mnemonic[-3:],
    )


def mnemonic_to_bytes(mnemonics: list) -> bytes:
    # TODO! THIS IS MOCK
    i = 0
    for m in mnemonics:
        i <<= 10
        i |= words.index(m)
    return i.to_bytes(len(mnemonics) * 10 // 8, "big")


def from_data(data: bytes, count: int, threshold: int) -> str:
    """
    Generate a mnemonic from given data.
    """
    raise NotImplementedError()


def check(mnemonic: str) -> bool:
    """
    Check whether given mnemonic is valid.
    """
    print("WARNING: SLIP39 check not implemented")


def seed(secret: bytes, passphrase: str) -> bytes:
    """
    Generate seed from mnemonic and passphrase.
    """
    # TODO
    return secret
