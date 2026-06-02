// BleController — single class that merges the heart-rate example's
// DeviceFinder (discovery) + DeviceHandler (central connection) and adds the
// write/control path the Smacircle needs. Exposed to QML as `ble`.
#pragma once
#include <QObject>
#include <QtBluetooth/QBluetoothDeviceDiscoveryAgent>
#include <QtBluetooth/QBluetoothDeviceInfo>
#include <QtBluetooth/QLowEnergyController>
#include <QtBluetooth/QLowEnergyService>
#include <QtBluetooth/QLowEnergyCharacteristic>
#include "protocol.h"

class BleController : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString status    READ status    NOTIFY statusChanged)
    Q_PROPERTY(bool    scanning  READ scanning  NOTIFY scanningChanged)
    Q_PROPERTY(bool    connected READ connected NOTIFY connectedChanged)
    Q_PROPERTY(bool    ready     READ ready     NOTIFY readyChanged)
    Q_PROPERTY(bool    hasData   READ hasData   NOTIFY telemetryChanged) // true only once live telemetry has arrived
    Q_PROPERTY(QString deviceName READ deviceName NOTIFY connectedChanged)
    Q_PROPERTY(double  speed   READ speed   NOTIFY telemetryChanged)
    Q_PROPERTY(int     battery READ battery NOTIFY telemetryChanged)
    Q_PROPERTY(bool    locked  READ locked  NOTIFY telemetryChanged)
    Q_PROPERTY(int     gear    READ gear    NOTIFY telemetryChanged)
    Q_PROPERTY(bool    light   READ light   NOTIFY telemetryChanged)
    Q_PROPERTY(bool    cruise  READ cruise  NOTIFY telemetryChanged)
    Q_PROPERTY(bool    fault   READ fault   NOTIFY telemetryChanged)
    Q_PROPERTY(double  trip    READ trip    NOTIFY telemetryChanged)
    Q_PROPERTY(double  total   READ total   NOTIFY telemetryChanged)
    Q_PROPERTY(QString serial         READ serial         NOTIFY infoChanged)
    Q_PROPERTY(QString controlVersion READ controlVersion NOTIFY infoChanged)
    Q_PROPERTY(QString bleVersion     READ bleVersion     NOTIFY infoChanged)
    Q_PROPERTY(QString password       READ password WRITE setPassword NOTIFY passwordChanged)
    Q_PROPERTY(bool    wrongPassword  READ wrongPassword  NOTIFY wrongPasswordChanged)
    Q_PROPERTY(bool    demoBuild      READ demoBuild      CONSTANT) // true only in SMACIRCLE_DEMO builds

public:
    explicit BleController(QObject *parent = nullptr);

    QString status() const     { return m_status; }
    bool    scanning() const   { return m_scanning; }
    bool    connected() const  { return m_connected; }
    bool    ready() const      { return m_ready; }
    bool    hasData() const    { return m_hasData; }
    QString deviceName() const { return m_deviceName; }
    double  speed() const      { return m_t.speedKmh; }
    int     battery() const    { return m_t.battery; }
    bool    locked() const     { return m_t.locked; }
    int     gear() const       { return m_t.gear; }
    bool    light() const      { return m_t.light; }
    bool    cruise() const     { return m_t.cruise; }
    bool    fault() const      { return m_t.error; }
    double  trip() const       { return m_t.tripKm; }
    double  total() const      { return m_t.totalKm; }
    QString serial() const         { return m_serial; }
    QString controlVersion() const { return m_ctrlVer; }
    QString bleVersion() const     { return m_bleVer; }
    QString password() const       { return m_password; }
    bool    wrongPassword() const  { return m_wrongPassword; }
    bool    demoBuild() const;

    Q_INVOKABLE void startScan();
    Q_INVOKABLE void disconnectScooter();
    Q_INVOKABLE void unlock();
    Q_INVOKABLE void lock();
    Q_INVOKABLE void setGear(int g);
    Q_INVOKABLE void setLight(bool on);
    Q_INVOKABLE void setCruise(bool on);
    Q_INVOKABLE void resetMileage();
    Q_INVOKABLE void setPassword(const QString &pw);
    Q_INVOKABLE void retryHandshake();   // re-send the (possibly new) password
    Q_INVOKABLE void startDemo();        // simulated S1 (no-op unless built with SMACIRCLE_DEMO)

signals:
    void statusChanged();
    void scanningChanged();
    void connectedChanged();
    void readyChanged();
    void telemetryChanged();
    void infoChanged();
    void passwordChanged();
    void wrongPasswordChanged();
    void notify(const QString &message, bool error);   // transient toast (snackbar)

private:
    enum class Toast { None, Info, Error };
    void setStatus(const QString &s, Toast toast = Toast::None);
    void beginScan();   // actual discovery, after permission is granted
    void connectToDevice(const QBluetoothDeviceInfo &info);
    void writeCommand(const QByteArray &cmd);
    void sendHandshake();
    void onReady();          // once handshake is confirmed / first telemetry seen
    void queryDeviceInfo();  // serial + controller/BLE firmware versions

    void onDeviceDiscovered(const QBluetoothDeviceInfo &info);
    void onScanFinished();
    void onServiceDiscovered(const QBluetoothUuid &uuid);
    void onDiscoveryFinished();
    void onServiceStateChanged(QLowEnergyService::ServiceState s);
    void onCharacteristicChanged(const QLowEnergyCharacteristic &c, const QByteArray &v);

    QBluetoothDeviceDiscoveryAgent *m_agent   = nullptr;
    QLowEnergyController           *m_control = nullptr;
    QLowEnergyService             *m_service = nullptr;
    QLowEnergyCharacteristic       m_writeChar;
    QBluetoothDeviceInfo           m_target;
    bool m_haveTarget = false;

    QString m_status;
    QString m_deviceName;
    bool m_scanning  = false;
    bool m_connected = false;
    bool m_ready     = false;
    bool m_hasData   = false;
    M0::Telemetry m_t;

    QString m_serial, m_ctrlVer, m_bleVer;
    QString m_password = QStringLiteral("0000");
    bool m_wrongPassword = false;
    bool m_infoQueried   = false;
    bool m_userDisconnect = false;   // true while a user-initiated disconnect is in flight

#ifdef SMACIRCLE_DEMO
    void demoTick();                 // synthetic telemetry, driven by m_demoTimer
    QTimer *m_demoTimer = nullptr;
    int  m_demoCount = 0;
    bool m_demo = false;
#endif
};
