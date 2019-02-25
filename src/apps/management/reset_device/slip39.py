from trezor.ui.num_pad import NumPad
from trezor.crypto import slip39


def generate_mnemonic(count: int, threshold: int, strength: int):
    return slip39.generate(count, threshold, strength)


async def ask_counts(ctx):
    shares = await NumPad("Set number of shares", 1, 32)
    threshold = await NumPad("Set threshold", 1, shares + 1)

    return shares, threshold
