// Smacircle M0 BLE protocol — C++ port of protocol.py (itself a byte-exact
// port of the decompiled M0Protocol.java). Verified against real hardware.
// No crypto: "encode" is a keyless XOR chain; checksum is 0xFFFF^sum.
#pragma once
#include <QByteArray>
#include <QString>
#include <QtGlobal>
#include <initializer_list>

namespace M0 {

// Nordic UART Service UUIDs (the S1 uses these — confirmed via nRF Connect).
inline const char *SERVICE_UUID = "{6e400001-b5a3-f393-e0a9-e50e24dcca9e}";
inline const char *WRITE_UUID   = "{6e400002-b5a3-f393-e0a9-e50e24dcca9e}"; // app -> device
inline const char *NOTIFY_UUID  = "{6e400003-b5a3-f393-e0a9-e50e24dcca9e}"; // device -> app

struct Telemetry {
    bool   valid    = false;
    double speedKmh = 0;
    int    battery  = 0;
    bool   cruise = false, light = false, locked = true, error = false;
    int    gear     = 0;
    double tripKm   = 0, totalKm = 0;
};

// encode() + calcSum() from M0Protocol.java. `b` includes 2 trailing
// checksum-placeholder bytes which we overwrite.
inline QByteArray finalize(QByteArray b)
{
    for (int i = 3; i < b.size() - 2; ++i)
        b[i] = char((quint8(b[i]) ^ quint8(b[i - 1])) & 0xFF);
    int s = 0;
    for (int i = 2; i < b.size() - 2; ++i)
        s += quint8(b[i]);
    const int ck = 0xFFFF ^ (s & 0xFFFF);
    b[b.size() - 2] = char(ck & 0xFF);
    b[b.size() - 1] = char((ck >> 8) & 0xFF);
    return b;
}

inline QByteArray frame(std::initializer_list<int> bytes)
{
    QByteArray b;
    b.reserve(int(bytes.size()));
    for (int x : bytes)
        b.append(char(x & 0xFF));
    return finalize(b);
}

// Commands (each mirrors a build*() in M0Protocol.java).
inline QByteArray password(int value = 0) // default "0000"
{ return frame({0xA5, 0x5A, 0x05, 0x21, 0x04, 0x00, value & 0xFF, (value >> 8) & 0xFF, 0, 0}); }
inline QByteArray lock(bool on)   { return frame({0xA5, 0x5A, 0x05, 0x20, 0x03, 0x7F, on ? 1 : 0, 0x00, 0, 0}); }
inline QByteArray unlock()        { return lock(false); }   // app sends lock(false) to unlock
inline QByteArray light(bool on)  { return frame({0xA5, 0x5A, 0x05, 0x20, 0x03, 0xF2, on ? 1 : 0, 0x00, 0, 0}); }
inline QByteArray gear(int g)     { return frame({0xA5, 0x5A, 0x05, 0x20, 0x03, 0x7E, g & 0xFF, 0x00, 0, 0}); }
inline QByteArray cruise(bool on) { return frame({0xA5, 0x5A, 0x04, 0x20, 0x03, 0x7C, on ? 1 : 0, 0, 0}); }
inline QByteArray clearMileage()  { return frame({0xA5, 0x5A, 0x05, 0x20, 0x03, 0xF5, 0x43, 0x4C, 0, 0}); }
inline QByteArray checkControlVersion() { return frame({0xA5, 0x5A, 0x04, 0x20, 0x01, 0x1A, 0x06, 0, 0}); }
inline QByteArray checkBleVersion()     { return frame({0xA5, 0x5A, 0x04, 0x21, 0x01, 0x20, 0x02, 0, 0}); }
inline QByteArray getCardSN()           { return frame({0xA5, 0x5A, 0x05, 0x20, 0x01, 0x10, 0x0E, 0x00, 0, 0}); }

// Inverse of encode() — for parsing device->app frames.
inline QByteArray decode(QByteArray f)
{
    for (int i = f.size() - 3; i > 2; --i)
        f[i] = char((quint8(f[i]) ^ quint8(f[i - 1])) & 0xFF);
    return f;
}

// parserInfo() from M0Protocol.java — extract live telemetry.
inline Telemetry parse(const QByteArray &f)
{
    Telemetry t;
    if (f.size() < 8) return t;
    if (quint8(f[0]) != 0xA5 || quint8(f[1]) != 0x5A) return t;
    const QByteArray d = decode(f);
    const int typ = quint8(d[4]);
    const int ex  = quint8(d[5]);
    if (typ == 100 || ex == 0) {
        if (d.size() < 16) return t;
        auto u = [&](int i) { return int(quint8(d[i])); };
        const int flg = u(9);
        t.speedKmh = (u(6) | (u(7) << 8)) / 1000.0;
        t.battery  = u(8);
        t.cruise   = flg & 1;
        t.light    = (flg >> 1) & 1;
        t.locked   = (flg >> 2) & 1;
        t.error    = (flg >> 3) & 1;
        t.gear     = (flg >> 4) & 3;
        t.tripKm   = (u(10) | (u(11) << 8)) / 100.0;
        t.totalKm  = (u(12) | (u(13) << 8) | (u(14) << 16) | (u(15) << 24)) / 100.0;
        t.valid    = true;
    }
    return t;
}

// ---- richer classifier: status / version / serial / handshake-ack ---------
enum class FrameKind { Unknown, Status, ControlVersion, BleVersion, Serial,
                       HandshakeOk, HandshakeFail };

struct Frame {
    FrameKind kind = FrameKind::Unknown;
    Telemetry status;   // valid when kind == Status
    QString   text;     // version string or serial when applicable
};

inline Frame parseFrame(const QByteArray &f)
{
    Frame out;
    if (f.size() < 8) return out;
    if (quint8(f[0]) != 0xA5 || quint8(f[1]) != 0x5A) return out;
    const QByteArray d = decode(f);
    const int len  = d.size();
    const int addr = quint8(d[3]);
    const int typ  = quint8(d[4]);
    const int ex   = quint8(d[5]);

    if (typ == 7 || typ == 8 || typ == 9)        // firmware-update acks — ignore
        return out;

    if (typ == 1) {                              // reply to a query command
        if (ex == 0x10) {                        // getCardSN -> ASCII serial
            out.kind = FrameKind::Serial;
            out.text = QString::fromLatin1(d.mid(6, len - 8)).trimmed();
        } else {                                 // version -> decoded bytes 6,7
            out.kind = (addr == 0x21) ? FrameKind::BleVersion : FrameKind::ControlVersion;
            out.text = QString::asprintf("%02X%02X", quint8(d[7]), quint8(d[6]));
        }
        return out;
    }

    if (typ == 100 || ex == 0) {
        if (len < 16) {                          // short frame == handshake ack
            if (ex == 0)
                out.kind = (quint8(d[2]) == 3) ? FrameKind::HandshakeFail
                                               : FrameKind::HandshakeOk;
            return out;
        }
        out.status = parse(f);                   // reuse the status parser
        if (out.status.valid) out.kind = FrameKind::Status;
        return out;
    }
    return out;
}

} // namespace M0
