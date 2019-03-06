from trezor import ui, wire
from trezor.crypto import bip32, bip39, slip39

from apps.common import cache, storage
from apps.common.request_passphrase import protect_by_passphrase

allow = list


class Keychain:
    """
    Keychain provides an API for deriving HD keys from previously allowed
    key-spaces.
    """

    def __init__(self, seed: bytes, namespaces: list):
        self.seed = seed
        self.namespaces = namespaces
        self.roots = [None] * len(namespaces)

    def __del__(self):
        for root in self.roots:
            if root is not None:
                root.__del__()
        del self.roots
        del self.seed

    def derive(self, node_path: list, curve_name: str = "secp256k1") -> bip32.HDNode:
        # find the root node index
        root_index = 0
        for curve, *path in self.namespaces:
            prefix = node_path[: len(path)]
            suffix = node_path[len(path) :]
            if curve == curve_name and path == prefix:
                break
            root_index += 1
        else:
            raise wire.DataError("Forbidden key path")

        # create the root node if not cached
        root = self.roots[root_index]
        if root is None:
            root = bip32.from_seed(self.seed, curve_name)
            root.derive_path(path)
            self.roots[root_index] = root

        # derive child node from the root
        node = root.clone()
        node.derive_path(suffix)
        return node


async def get_keychain(ctx: wire.Context, namespaces: list) -> Keychain:
    if not storage.is_initialized():
        raise wire.ProcessError("Device is not initialized")
    seed = cache.get_seed()
    if seed is None:
        seed = await _compute_seed(ctx)
    keychain = Keychain(seed, namespaces)
    return keychain


@ui.layout_no_slide
async def _compute_seed(ctx: wire.Context) -> bytes:
    passphrase = cache.get_passphrase()
    if passphrase is None:
        passphrase = await protect_by_passphrase(ctx)
        cache.set_passphrase(passphrase)
    _start_progress()
    seed = _get_seed(passphrase)
    cache.set_seed(seed)
    return seed


def _start_progress():
    ui.backlight_slide_sync(ui.BACKLIGHT_DIM)
    ui.display.clear()
    ui.header("Please wait")
    ui.display.refresh()
    ui.backlight_slide_sync(ui.BACKLIGHT_NORMAL)


def _render_progress(progress: int, total: int):
    p = int(1000 * progress / total)
    ui.display.loader(p, 18, ui.WHITE, ui.BG)
    ui.display.refresh()


def derive_node_without_passphrase(
    path: list, curve_name: str = "secp256k1"
) -> bip32.HDNode:
    if not storage.is_initialized():
        raise Exception("Device is not initialized")
    seed = _get_seed("")
    node = bip32.from_seed(seed, curve_name)
    node.derive_path(path)
    return node


def remove_ed25519_prefix(pubkey: bytes) -> bytes:
    # 0x01 prefix is not part of the actual public key, hence removed
    return pubkey[1:]


def _get_seed(passphrase: str) -> bytes:
    if storage.get_mnemonic_standard() == storage._MNEMONIC_STANDARD_BIP39:
        return bip39.seed(storage.get_mnemonic().decode(), passphrase, _render_progress)
    elif storage.get_mnemonic_standard() == storage._MNEMONIC_STANDARD_SLIP39:
        return slip39.seed(storage.get_mnemonic(), passphrase)  # TODO render progress?
    else:
        raise RuntimeError("Unknown mnemonic standard")
