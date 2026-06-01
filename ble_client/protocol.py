"""
Smacircle BLE protocol — faithful Python port of the decompiled Android app.

Source of truth (decompiled from Smacircle_1.1.0 / 1.2.4, identical in both):
  work/src_1.1.0/sources/com/smacircle/android/ble/M0Protocol.java
  work/src_1.1.0/sources/com/smacircle/android/ble/C041Protocol.java

The S1 unit (confirmed via nRF Connect) speaks the **M0** protocol over the
Nordic UART Service. C041 is included for completeness / other models.

There is NO real cryptography here:
  * M0  "encode" is a keyless XOR chain (b[i] ^= b[i-1]); checksum is 0xFFFF^sum.
  * C041 challenge-response XORs the device nonce with a hardcoded 0x12345678.
Everything is reproducible offline; no server is involved in device control.
"""

# ---------------------------------------------------------------------------
# M0 protocol — Nordic UART Service (this is what the S1 uses)
# ---------------------------------------------------------------------------

class M0:
    # GATT UUIDs (M0Protocol.java lines 27-29)
    SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"   # Nordic UART Service
    WRITE   = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"   # app -> device  (RX)
    NOTIFY  = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"   # device -> app  (TX)

    DEFAULT_PASSWORD = "0000"

    # --- frame core (encode() / calcSum() from M0Protocol.java) -----------
    @staticmethod
    def _finalize(raw):
        """raw = full frame as a list of ints INCLUDING two trailing
        checksum-placeholder bytes. Mirrors: encode() then calcSum(),
        then write checksum little-endian into the last two bytes."""
        b = bytearray(raw)
        # encode(): XOR-chain bytes [3 .. len-3]
        for i in range(3, len(b) - 2):
            b[i] = (b[i] ^ b[i - 1]) & 0xFF
        # calcSum(): 0xFFFF ^ sum(bytes[2 .. len-3])
        s = sum(b[2:len(b) - 2]) & 0xFFFF
        ck = 0xFFFF ^ s
        b[-2] = ck & 0xFF
        b[-1] = (ck >> 8) & 0xFF
        return bytes(b)

    @staticmethod
    def decode(frame):
        """Inverse of encode() — for parsing device->app frames."""
        c = bytearray(frame)
        for i in range(len(c) - 3, 2, -1):
            c[i] = (c[i] ^ c[i - 1]) & 0xFF
        return bytes(c)

    # --- commands (each mirrors a build*() in M0Protocol.java) ------------
    @classmethod
    def password(cls, pw=DEFAULT_PASSWORD):
        """Handshake. pw is a numeric string (default '0000')."""
        val = int(pw)
        lo, hi = val & 0xFF, (val >> 8) & 0xFF
        return cls._finalize([0xA5, 0x5A, 0x05, 0x21, 0x04, 0x00, lo, hi, 0, 0])

    @classmethod
    def password_change(cls, pw):
        val = int(pw)
        lo, hi = val & 0xFF, (val >> 8) & 0xFF
        return cls._finalize([0xA5, 0x5A, 0x05, 0x21, 0x03, 0x1C, lo, hi, 0, 0])

    @classmethod
    def lock(cls, locked):
        """locked=True locks, locked=False UNLOCKS (app sends lock(False) on
        handshake success — HomeFragment2 line 330)."""
        return cls._finalize([0xA5, 0x5A, 0x05, 0x20, 0x03, 0x7F,
                              1 if locked else 0, 0x00, 0, 0])

    @classmethod
    def unlock(cls):
        return cls.lock(False)

    @classmethod
    def light(cls, on):
        return cls._finalize([0xA5, 0x5A, 0x05, 0x20, 0x03, 0xF2,
                              1 if on else 0, 0x00, 0, 0])

    @classmethod
    def gear(cls, level):
        return cls._finalize([0xA5, 0x5A, 0x05, 0x20, 0x03, 0x7E,
                              level & 0xFF, 0x00, 0, 0])

    @classmethod
    def cruise(cls, on):
        return cls._finalize([0xA5, 0x5A, 0x04, 0x20, 0x03, 0x7C,
                              1 if on else 0, 0, 0])

    @classmethod
    def check_control_version(cls):
        return cls._finalize([0xA5, 0x5A, 0x04, 0x20, 0x01, 0x1A, 0x06, 0, 0])

    @classmethod
    def check_ble_version(cls):
        return cls._finalize([0xA5, 0x5A, 0x04, 0x21, 0x01, 0x20, 0x02, 0, 0])

    @classmethod
    def get_card_sn(cls):
        return cls._finalize([0xA5, 0x5A, 0x05, 0x20, 0x01, 0x10, 0x0E, 0x00, 0, 0])

    # --- parse device telemetry (parserInfo in M0Protocol.java) -----------
    @classmethod
    def parse(cls, frame):
        """Return a dict of live telemetry, or None if not a status frame."""
        if not frame or len(frame) < 8:
            return None
        if frame[0] != 0xA5 or frame[1] != 0x5A:
            return None
        d = cls.decode(frame)
        typ, ex = d[4], d[5]
        if typ == 100 or ex == 0:
            if len(d) < 16:
                return None
            le = lambda *bs: sum((b & 0xFF) << (8 * i) for i, b in enumerate(bs))
            f = d[9]
            return {
                "speed_kmh":  le(d[6], d[7]) / 1000.0,
                "battery_pct": d[8] & 0xFF,
                "cruise":  bool(f & 1),
                "light":   bool((f >> 1) & 1),
                "locked":  bool((f >> 2) & 1),
                "error":   bool((f >> 3) & 1),
                "gear":    (f >> 4) & 3,
                "trip_km":  le(d[10], d[11]) / 100.0,
                "total_km": le(d[12], d[13], d[14], d[15]) / 100.0,
            }
        return None


# ---------------------------------------------------------------------------
# C041 protocol — different service UUID (older / other models). Not the S1.
# ---------------------------------------------------------------------------

class C041:
    SERVICE = "a0a1a2a3-a4a5-a6a7-a8a9-aaabacadaeaf"
    WRITE   = "b0a1a2a3-a4a5-a6a7-a8a9-aaabacadaeaf"
    NOTIFY  = "b1a1a2a3-a4a5-a6a7-a8a9-aaabacadaeaf"
    DEFAULT_PASSWORD = "888888"

    FE, EF = 0xFE, 0xEF

    @classmethod
    def _cmd(cls, code, value):
        b = bytearray(13)
        b[0] = cls.FE
        b[1] = code & 0xFF
        b[2] = value & 0xFF
        b[11] = sum(b[1:11]) & 0xFF        # checkSum(b, 1, 10)
        b[12] = cls.EF
        return bytes(b)

    @classmethod
    def lock(cls, locked):  return cls._cmd(0xA4, 1 if locked else 0)
    @classmethod
    def unlock(cls):        return cls.lock(False)
    @classmethod
    def gear(cls, n):       return cls._cmd(0xA1, n)
    @classmethod
    def max_speed(cls, n):  return cls._cmd(0xA5, n)
    @classmethod
    def light(cls, on):     return cls._cmd(0xA6, 1 if on else 0)
    @classmethod
    def cruise(cls, on):    return cls._cmd(0xA3, 1 if on else 0)
    @classmethod
    def auto_off(cls, n):   return cls._cmd(0xA2, n)
    @classmethod
    def start_power(cls, n): return cls._cmd(0xA7, n)

    @classmethod
    def password(cls, pw=DEFAULT_PASSWORD):
        bs = pw.encode()
        if len(bs) != 6:
            raise ValueError("C041 password must be 6 bytes")
        return bytes([0x02, cls.FE, 0x02, *bs, cls.EF])

    @classmethod
    def random_auth(cls, nonce4):
        """Keyless challenge-response: XOR nonce with 0x12345678 + bit shuffle."""
        x = sum((nonce4[i] & 0xFF) << (8 * i) for i in range(4))  # bytesToInt (LE)
        out = 0
        for _ in range(32):
            t = (x ^ 0x12345678) & 0xFFFFFFFF
            out = ((out | (0x80000000 & t)) & 0xFFFFFFFF) >> 1
            x = (t << 1) & 0xFFFFFFFF
        ob = [(out >> (8 * i)) & 0xFF for i in range(4)]
        return bytes([0x02, cls.FE, 0x04, *ob, cls.EF])


if __name__ == "__main__":
    # Quick self-check: print the exact bytes we'll send to the S1.
    for name, frame in [
        ("password('0000')", M0.password("0000")),
        ("unlock()",         M0.unlock()),
        ("lock()",           M0.lock(True)),
        ("gear(1)",          M0.gear(1)),
        ("light(on)",        M0.light(True)),
        ("cruise(on)",       M0.cruise(True)),
    ]:
        print(f"{name:18} -> {frame.hex(' ')}")
