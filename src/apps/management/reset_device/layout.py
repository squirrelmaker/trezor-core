from micropython import const
from ubinascii import hexlify

from trezor import ui
from trezor.crypto import random
from trezor.messages import ButtonRequestType, MessageType
from trezor.messages.ButtonRequest import ButtonRequest
from trezor.ui.confirm import HoldToConfirmDialog
from trezor.ui.mnemonic import MnemonicKeyboard
from trezor.ui.scroll import Scrollpage, animate_swipe, paginate
from trezor.ui.text import Text
from trezor.utils import chunks, format_ordinal

from apps.common.confirm import require_confirm

if __debug__:
    from apps import debug


async def show_intro(ctx, slip39=False):
    text = Text("Create a new wallet", ui.ICON_RESET, new_lines=False)
    text.normal("Do you want to create")
    text.br()
    if slip39:
        text.normal("a new SLIP-39 wallet?")
    else:
        text.normal("a new wallet?")
    text.br()
    text.br_half()
    text.normal("By continuing you agree")
    text.br()
    text.normal("to")
    text.bold("https://trezor.io/tos")

    await require_confirm(ctx, text, code=ButtonRequestType.ResetDevice)


async def show_mnemonics(ctx, mnemonics):
    # require confirmation of the mnemonic safety
    await show_warning(ctx)

    for i, mnemonic in enumerate(mnemonics, 1):
        if len(mnemonics) == 1:
            i = None
        # show mnemonic and require confirmation of a random word
        while True:
            await show_mnemonic_words(ctx, mnemonic, i)
            if await check_mnemonic(ctx, mnemonic):
                break
            await show_wrong_entry(ctx)


async def show_warning(ctx):
    text = Text("Backup your seed", ui.ICON_NOCOPY)
    text.normal(
        "Never make a digital",
        "copy of your recovery",
        "seed and never upload",
        "it online!",
    )
    await require_confirm(
        ctx, text, ButtonRequestType.ResetDevice, confirm="I understand", cancel=None
    )


async def show_wrong_entry(ctx):
    text = Text("Wrong entry!", ui.ICON_WRONG, icon_color=ui.RED)
    text.normal("You have entered", "wrong seed word.", "Please check again.")
    await require_confirm(
        ctx, text, ButtonRequestType.ResetDevice, confirm="Check again", cancel=None
    )


async def show_success(ctx):
    text = Text("Backup is done!", ui.ICON_CONFIRM, icon_color=ui.GREEN)
    text.normal(
        "Never make a digital",
        "copy of your recovery",
        "seed and never upload",
        "it online!",
    )
    await require_confirm(
        ctx, text, ButtonRequestType.ResetDevice, confirm="Finish setup", cancel=None
    )


async def show_entropy(ctx, entropy: bytes):
    entropy_str = hexlify(entropy).decode()
    lines = chunks(entropy_str, 16)
    text = Text("Internal entropy", ui.ICON_RESET)
    text.mono(*lines)
    await require_confirm(ctx, text, ButtonRequestType.ResetDevice)


async def show_mnemonic_words(ctx, mnemonic: str, position: int):
    await ctx.call(
        ButtonRequest(code=ButtonRequestType.ResetDevice), MessageType.ButtonAck
    )
    first_page = const(0)
    words_per_page = const(4)
    words = list(enumerate(mnemonic.split()))
    pages = list(chunks(words, words_per_page))
    paginator = paginate(show_mnemonic_page, len(pages), first_page, pages, position)
    await ctx.wait(paginator)


@ui.layout
async def show_mnemonic_page(page: int, page_count: int, pages: list, position: int):
    if __debug__:
        debug.reset_current_words = [word for _, word in pages[page]]

    lines = ["%2d. %s" % (wi + 1, word) for wi, word in pages[page]]
    if position:
        text = Text("Recovery seed %d" % position, ui.ICON_RESET)
    else:
        text = Text("Recovery seed", ui.ICON_RESET)
    text.mono(*lines)
    content = Scrollpage(text, page, page_count)

    if page + 1 == page_count:
        await HoldToConfirmDialog(content)
    else:
        content.render()
        await animate_swipe()


async def check_mnemonic(ctx, mnemonic: str) -> bool:
    words = mnemonic.split()

    # check a word from the first half
    index = random.uniform(len(words) // 2)
    if not await check_word(ctx, words, index):
        return False

    # check a word from the second half
    index = random.uniform(len(words) // 2) + len(words) // 2
    if not await check_word(ctx, words, index):
        return False

    return True


@ui.layout
async def check_word(ctx, words: list, index: int):
    if __debug__:
        debug.reset_word_index = index

    keyboard = MnemonicKeyboard("Type the %s word:" % format_ordinal(index + 1))
    result = await ctx.wait(keyboard)
    return result == words[index]
