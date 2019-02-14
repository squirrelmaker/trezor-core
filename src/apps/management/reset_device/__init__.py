from trezor import config, wire, workflow
from trezor.messages.Success import Success
from trezor.pin import pin_to_int

from . import bip39_reset, layout

from apps.common import storage
from apps.management.change_pin import request_pin_confirm


async def reset_device(ctx, msg):
    # validate parameters and device state
    if msg.strength not in (128, 192, 256):
        raise wire.ProcessError("Invalid strength (has to be 128, 192 or 256 bits)")
    if msg.display_random and (msg.skip_backup or msg.no_backup):
        raise wire.ProcessError("Can't show internal entropy when backup is skipped")
    if storage.is_initialized():
        raise wire.UnexpectedMessage("Already initialized")

    await layout.show_intro(ctx)

    # request new PIN
    if msg.pin_protection:
        newpin = await request_pin_confirm(ctx)
    else:
        newpin = ""

    mnemonic = await bip39_reset.generate_mnemonic(ctx, msg)

    if not msg.skip_backup and not msg.no_backup:
        # require confirmation of the mnemonic safety
        await layout.show_warning(ctx)

        # show mnemonic and require confirmation of a random word
        while True:
            await layout.show_mnemonic(ctx, mnemonic)
            if await layout.check_mnemonic(ctx, mnemonic):
                break
            await layout.show_wrong_entry(ctx)

    # write PIN into storage
    if not config.change_pin(pin_to_int(""), pin_to_int(newpin)):
        raise wire.ProcessError("Could not change PIN")

    # write settings and mnemonic into storage
    storage.load_settings(label=msg.label, use_passphrase=msg.passphrase_protection)
    storage.load_mnemonic(
        mnemonic=mnemonic, needs_backup=msg.skip_backup, no_backup=msg.no_backup
    )

    # show success message.  if we skipped backup, it's possible that homescreen
    # is still running, uninterrupted.  restart it to pick up new label.
    if not msg.skip_backup and not msg.no_backup:
        await layout.show_success(ctx)
    else:
        workflow.restartdefault()

    return Success(message="Initialized")
