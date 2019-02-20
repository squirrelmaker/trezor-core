from trezor.ui.num_pad import NumPad


def generate_mnemonic(count: int, threshold: int, strength: int):
    # TODO mocked for the time being
    if strength == 128:  # 20 words
        return (
            "surprise resource december north more vague alcohol vibrant gate method remove never surface trim route culture knife innocent arrow among",
        ) * count
    elif strength == 256:  # 33 words
        return (
            "wet grunt success merit sure message name potato jazz bracket disagree sword decline clarify analyst learn what foot age dance play brain thrive bunker west oppose spray inject hazard sustain monster glare south",
        ) * count
    raise RuntimeError("Invalid strength for SLIP-39 generation")


async def ask_counts(ctx):
    shares = await NumPad("Set number of shares", 1, 32)
    threshold = await NumPad("Set threshold", 1, shares + 1)

    return shares, threshold
