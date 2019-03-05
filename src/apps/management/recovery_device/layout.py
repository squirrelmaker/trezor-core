from trezor import ui
from trezor.messages.ButtonRequest import ButtonRequest
from trezor.messages.ButtonRequestType import MnemonicInput
from trezor.messages.MessageType import ButtonAck
from trezor.ui.mnemonic import MnemonicKeyboard
from trezor.utils import format_ordinal


@ui.layout
async def request_mnemonic(ctx, count: int) -> str:
    await ctx.call(ButtonRequest(code=MnemonicInput), ButtonAck)

    words = []
    board = MnemonicKeyboard()
    for i in range(count):
        board.prompt = "Type the %s word:" % format_ordinal(i + 1)
        word = await ctx.wait(board)
        words.append(word)

    return words
