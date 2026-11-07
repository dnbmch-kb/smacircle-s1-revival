"""M0 wire-format checks, no hardware: the frame codec of ble_client/protocol.py
(the hardware-proven reference) and byte parity of every command table in
qt_app/protocol.h against it.

Run from the repo root:  python -m unittest discover -s ble_client/tests
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ble_client"))
from protocol import M0  # noqa: E402

# Each C++ command, its Python twin, and the (C++ args, Python args) pairs to compare.
BOOL = [((True,), (True,)), ((False,), (False,))]
COMMANDS = {
    "password":            (M0.password, [((0,), ("0000",)), ((1234,), ("1234",)), ((9999,), ("9999",))]),
    "lock":                (M0.lock, BOOL),
    "light":               (M0.light, BOOL),
    "gear":                (M0.gear, [((g,), (g,)) for g in range(4)]),
    "cruise":              (M0.cruise, BOOL),
    "clearMileage":        (M0.clear_mileage, [((), ())]),
    "checkControlVersion": (M0.check_control_version, [((), ())]),
    "checkBleVersion":     (M0.check_ble_version, [((), ())]),
    "getCardSN":           (M0.get_card_sn, [((), ())]),
}


def cpp_tables():
    """name -> (parameter names, byte expressions) for every
    `inline QByteArray name(params) ... { return frame({...}); }` in protocol.h."""
    text = (ROOT / "qt_app" / "protocol.h").read_text(encoding="utf-8")
    pattern = re.compile(r"inline QByteArray (\w+)\(([^)]*)\)[^{]*\{\s*return frame\(\{([^}]*)\}\);")
    tables = {}
    for name, params, body in pattern.findall(text):
        names = [re.match(r"\s*\w+\s+(\w+)", p).group(1) for p in params.split(",") if p.strip()]
        tables[name] = (names, [e.strip() for e in body.split(",")])
    return tables


def cpp_bytes(params, exprs, args):
    env = dict(zip(params, args))
    out = []
    for e in exprs:
        e = re.sub(r"(\w+)\s*\?\s*(\w+)\s*:\s*(\w+)", r"(\2 if \1 else \3)", e)  # C ternary
        out.append(eval(e, {"__builtins__": {}}, env) & 0xFF)
    return out


class Codec(unittest.TestCase):
    def test_decode_inverts_finalize_and_checksum_closes(self):
        raw = [0xA5, 0x5A, 0x0C, 0x20, 0x64, 0x01, 0x10, 0x27, 0x55, 0x2D,
               0x34, 0x12, 0x78, 0x56, 0x34, 0x12, 0, 0]
        frame = M0._finalize(raw)
        self.assertEqual(list(M0.decode(frame))[:-2], raw[:-2])
        self.assertEqual(sum(frame[2:-2]) + (frame[-2] | frame[-1] << 8), 0xFFFF)

    def test_status_frame_parses(self):
        raw = [0xA5, 0x5A, 0x0C, 0x20, 0x64, 0x01, 0x10, 0x27, 0x55, 0x2D,
               0x34, 0x12, 0x78, 0x56, 0x34, 0x12, 0, 0]
        t = M0.parse(M0._finalize(raw))
        self.assertEqual(t["speed_kmh"], 10.0)                # 0x2710 / 1000
        self.assertEqual(t["battery_pct"], 0x55)
        self.assertEqual((t["cruise"], t["light"], t["locked"], t["error"], t["gear"]),
                         (True, False, True, True, 2))        # flags 0x2D
        self.assertEqual(t["trip_km"], 0x1234 / 100.0)
        self.assertEqual(t["total_km"], 0x12345678 / 100.0)


class QtParity(unittest.TestCase):
    def test_every_qt_command_has_a_python_twin(self):
        self.assertEqual(set(cpp_tables()), set(COMMANDS))

    def test_qt_tables_match_python_bytes(self):
        tables = cpp_tables()
        for name, (py, cases) in COMMANDS.items():
            params, exprs = tables[name]
            for cpp_args, py_args in cases:
                with self.subTest(command=name, args=cpp_args):
                    self.assertEqual(M0._finalize(cpp_bytes(params, exprs, cpp_args)), py(*py_args))


if __name__ == "__main__":
    unittest.main()
