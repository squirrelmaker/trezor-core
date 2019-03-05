from trezor import config, crypto, ui, wire
from trezor.messages.ButtonRequest import ButtonRequest
from trezor.messages.ButtonRequestType import MnemonicWordCount, ProtectCall
from trezor.messages.MessageType import ButtonAck
from trezor.messages.RecoveryDeviceInProgress import RecoveryDeviceInProgress
from trezor.messages.Success import Success
from trezor.pin import pin_to_int
from trezor.ui.text import Text
from trezor.ui.word_select import WordSelector

from . import bip39, layout, slip39

from apps.common import storage
from apps.common.confirm import require_confirm
from apps.homescreen.homescreen import display_homescreen
from apps.management.change_pin import request_pin_ack, request_pin_confirm


async def recovery_device(ctx, msg):
    """
    Recover BIP39/SLIP39 seed into empty device.

    1. Ask for the number of words in recovered seed.
    2. Let user type in the mnemonic words one by one.
    3. Optionally check the seed validity.
    4. Optionally ask for the PIN, with confirmation.
    5. Save into storage.
    """
    if not msg.dry_run and storage.is_initialized():
        raise wire.UnexpectedMessage("Already initialized")

    if not storage.is_slip39_in_progress():
        text = Text("Device recovery", ui.ICON_RECOVERY)
        text.normal("Do you really want to", "recover the device?", "")

        await require_confirm(ctx, text, code=ProtectCall)

        if msg.dry_run and config.has_pin():
            curpin = await request_pin_ack(ctx, "Enter PIN", config.get_pin_rem())
            if not config.check_pin(pin_to_int(curpin)):
                raise wire.PinInvalid("PIN invalid")

        # ask for the number of words
        wordcount = await request_wordcount(ctx)
        if wordcount in crypto.slip39.SHARE_LENGTHS:  # SLIP39 lengths
            standard = slip39
        else:
            standard = bip39
    else:
        wordcount = storage.get_slip39_words_count()
        standard = slip39

    # ask for mnemonic words one by one
    words = await layout.request_mnemonic(ctx, wordcount)

    premaster_secret = standard.process_mnemonic(words)
    if premaster_secret is None:  # not finished
        return RecoveryDeviceInProgress()

    # check validity
    if standard == bip39 and (msg.enforce_wordlist or msg.dry_run):
        if not standard.check(premaster_secret):
            raise wire.ProcessError("Mnemonic is not valid")

    # ask for pin repeatedly
    if msg.pin_protection:
        newpin = await request_pin_confirm(ctx, cancellable=False)

    # dry run
    if msg.dry_run:
        if standard == slip39:
            raise NotImplementedError("Dry run not yet implemented for SLIP-39")
        else:
            if not standard.dry_run(premaster_secret):
                return Success(
                    message="The seed is valid and matches the one in the device"
                )

    # save into storage
    if msg.pin_protection:
        config.change_pin(pin_to_int(""), pin_to_int(newpin))
    storage.set_u2f_counter(msg.u2f_counter)
    storage.load_settings(label=msg.label, use_passphrase=msg.passphrase_protection)
    standard.save_to_storage(premaster_secret)

    display_homescreen()

    return Success(message="Device recovered")


@ui.layout
async def request_wordcount(ctx):
    await ctx.call(ButtonRequest(code=MnemonicWordCount), ButtonAck)

    text = Text("Device recovery", ui.ICON_RECOVERY)
    text.normal("Number of words?")
    count = await ctx.wait(WordSelector(text))

    return count
