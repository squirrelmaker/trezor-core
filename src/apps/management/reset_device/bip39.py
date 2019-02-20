from trezor.crypto import bip39, hashlib, random
from trezor.messages import MessageType
from trezor.messages.EntropyRequest import EntropyRequest

from . import layout

if __debug__:
    from apps import debug


async def generate_mnemonic(ctx, msg):
    # generate and display internal entropy
    internal_ent = random.bytes(32)
    if __debug__:
        debug.reset_internal_entropy = internal_ent
    if msg.display_random:
        await layout.show_entropy(ctx, internal_ent)

    # request external entropy and compute mnemonic
    ent_ack = await ctx.call(EntropyRequest(), MessageType.EntropyAck)
    return _generate(msg.strength, internal_ent, ent_ack.entropy)


def _generate(strength: int, int_entropy: bytes, ext_entropy: bytes) -> bytes:
    ehash = hashlib.sha256()
    ehash.update(int_entropy)
    ehash.update(ext_entropy)
    entropy = ehash.digest()
    mnemonic = bip39.from_data(entropy[: strength // 8])
    return mnemonic
