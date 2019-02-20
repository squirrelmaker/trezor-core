from trezor import config, wire, workflow
from trezor.messages.Success import Success
from trezor.pin import pin_to_int

from . import bip39, layout, slip39

from apps.common import storage
from apps.management.change_pin import request_pin_confirm


async def reset_device(ctx, msg):
    _validate(msg, msg.slip39)

    await layout.show_intro(ctx, msg.slip39)

    # request new PIN
    if msg.pin_protection:
        newpin = await request_pin_confirm(ctx)
    else:
        newpin = ""

    if msg.slip39:
        shares_count, threshold = await slip39.ask_counts(ctx)
        mnemonics = slip39.generate_mnemonic(shares_count, threshold, msg.strength)
    else:
        mnemonics = (await bip39.generate_mnemonic(ctx, msg),)

    if not msg.skip_backup and not msg.no_backup:
        await layout.show_mnemonics(ctx, mnemonics)

    # write PIN into storage
    if not config.change_pin(pin_to_int(""), pin_to_int(newpin)):
        raise wire.ProcessError("Could not change PIN")

    # write settings and mnemonic into storage
    storage.load_settings(label=msg.label, use_passphrase=msg.passphrase_protection)
    if msg.slip39:
        # TODO save to storage
        raise NotImplementedError("TODO")
    else:
        storage.load_mnemonic(
            mnemonic=mnemonics[0], needs_backup=msg.skip_backup, no_backup=msg.no_backup
        )

    # show success message.  if we skipped backup, it's possible that homescreen
    # is still running, uninterrupted.  restart it to pick up new label.
    if not msg.skip_backup and not msg.no_backup:
        await layout.show_success(ctx)
    else:
        workflow.restartdefault()

    return Success(message="Initialized")


def _validate(msg, is_slip39):
    # validate parameters and device state
    if msg.strength not in (128, 256):
        if is_slip39:
            raise wire.ProcessError("Invalid strength (has to be 128 or 256 bits)")
        elif msg.strength != 192:
            raise wire.ProcessError("Invalid strength (has to be 128, 192 or 256 bits)")

    if msg.display_random and (msg.skip_backup or msg.no_backup):
        raise wire.ProcessError("Can't show internal entropy when backup is skipped")
    if storage.is_initialized():
        raise wire.UnexpectedMessage("Already initialized")
    if (msg.skip_backup or msg.no_backup) and is_slip39:
        raise wire.ProcessError("Both no/skip backup flag and Shamir SLIP-39 required.")
