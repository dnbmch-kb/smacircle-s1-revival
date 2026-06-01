#include "blecontroller.h"
#include <QtBluetooth/QLowEnergyDescriptor>
#include <QCoreApplication>
#include <QPermissions>
#include <QTimer>
#include <QDebug>

namespace {
QBluetoothUuid uuid(const char *s) { return QBluetoothUuid(QString::fromLatin1(s)); }
const QString TARGET_PREFIX = QStringLiteral("SMACIRCLE");
}

BleController::BleController(QObject *parent) : QObject(parent)
{
    m_agent = new QBluetoothDeviceDiscoveryAgent(this);
    m_agent->setLowEnergyDiscoveryTimeout(10000);
    connect(m_agent, &QBluetoothDeviceDiscoveryAgent::deviceDiscovered,
            this, &BleController::onDeviceDiscovered);
    connect(m_agent, &QBluetoothDeviceDiscoveryAgent::finished,
            this, &BleController::onScanFinished);
    connect(m_agent, &QBluetoothDeviceDiscoveryAgent::canceled,
            this, &BleController::onScanFinished);
    connect(m_agent, &QBluetoothDeviceDiscoveryAgent::errorOccurred, this,
            [this](QBluetoothDeviceDiscoveryAgent::Error) {
                setStatus(QStringLiteral("Scan error: ") + m_agent->errorString());
                m_scanning = false; emit scanningChanged();
            });
    setStatus(QStringLiteral("Idle. Tap Scan & Connect."));
}

void BleController::setStatus(const QString &s)
{
    if (s != m_status) { m_status = s; emit statusChanged(); }
    qInfo().noquote() << s;
}

// ---- discovery ------------------------------------------------------------
void BleController::startScan()
{
    if (m_scanning) return;
#if QT_CONFIG(permissions)
    // Android 12+ / iOS require a runtime Bluetooth permission. On desktop this
    // resolves to Granted immediately (no-op).
    QBluetoothPermission permission;
    permission.setCommunicationModes(QBluetoothPermission::Access);
    switch (qApp->checkPermission(permission)) {
    case Qt::PermissionStatus::Undetermined:
        setStatus(QStringLiteral("Requesting Bluetooth permission…"));
        qApp->requestPermission(permission, this, [this](const QPermission &p) {
            if (p.status() == Qt::PermissionStatus::Granted)
                beginScan();
            else
                setStatus(QStringLiteral("Bluetooth permission denied — enable it in Settings."));
        });
        return;
    case Qt::PermissionStatus::Denied:
        setStatus(QStringLiteral("Bluetooth permission denied — enable it in Settings."));
        return;
    case Qt::PermissionStatus::Granted:
        break;
    }
#endif
    beginScan();
}

void BleController::beginScan()
{
    m_haveTarget = false;
    m_hasData = false; emit telemetryChanged();
    m_scanning = true; emit scanningChanged();
    setStatus(QStringLiteral("Scanning…"));
    m_agent->start(QBluetoothDeviceDiscoveryAgent::LowEnergyMethod);
}

void BleController::onDeviceDiscovered(const QBluetoothDeviceInfo &info)
{
    if (!(info.coreConfigurations() & QBluetoothDeviceInfo::LowEnergyCoreConfiguration))
        return;
    const bool nameMatch = info.name().contains(TARGET_PREFIX, Qt::CaseInsensitive);
    const bool svcMatch  = info.serviceUuids().contains(uuid(M0::SERVICE_UUID));
    if (nameMatch || svcMatch) {
        m_target = info;
        m_haveTarget = true;
        setStatus(QStringLiteral("Found %1").arg(info.name()));
        m_agent->stop();   // -> onScanFinished -> connect
    }
}

void BleController::onScanFinished()
{
    m_scanning = false; emit scanningChanged();
    if (m_haveTarget)
        connectToDevice(m_target);
    else
        setStatus(QStringLiteral("No scooter found. Power it on and rescan."));
}

// ---- connection -----------------------------------------------------------
void BleController::connectToDevice(const QBluetoothDeviceInfo &info)
{
    if (m_control) { m_control->deleteLater(); m_control = nullptr; }

    m_control = QLowEnergyController::createCentral(info, this);
    m_deviceName = info.name();

    connect(m_control, &QLowEnergyController::connected, this, [this]() {
        setStatus(QStringLiteral("Connected, discovering services…"));
        m_control->discoverServices();
    });
    connect(m_control, &QLowEnergyController::disconnected, this, [this]() {
        m_connected = false; m_ready = false; m_hasData = false;
        emit connectedChanged(); emit readyChanged(); emit telemetryChanged();
        setStatus(QStringLiteral("Disconnected"));
    });
    connect(m_control, &QLowEnergyController::errorOccurred, this,
            [this](QLowEnergyController::Error) {
                setStatus(QStringLiteral("BLE error: ") + m_control->errorString());
            });
    connect(m_control, &QLowEnergyController::serviceDiscovered,
            this, &BleController::onServiceDiscovered);
    connect(m_control, &QLowEnergyController::discoveryFinished,
            this, &BleController::onDiscoveryFinished);

    setStatus(QStringLiteral("Connecting to %1…").arg(m_deviceName));
    m_control->connectToDevice();
}

void BleController::onServiceDiscovered(const QBluetoothUuid &u)
{
    if (u == uuid(M0::SERVICE_UUID))
        setStatus(QStringLiteral("Found Nordic UART service"));
}

void BleController::onDiscoveryFinished()
{
    if (m_service) { m_service->deleteLater(); m_service = nullptr; }
    m_service = m_control->createServiceObject(uuid(M0::SERVICE_UUID), this);
    if (!m_service) {
        setStatus(QStringLiteral("Nordic UART service not found!"));
        return;
    }
    connect(m_service, &QLowEnergyService::stateChanged,
            this, &BleController::onServiceStateChanged);
    connect(m_service, &QLowEnergyService::characteristicChanged,
            this, &BleController::onCharacteristicChanged);
    connect(m_service, &QLowEnergyService::errorOccurred, this,
            [this](QLowEnergyService::ServiceError e) { qWarning() << "service error" << e; });
    m_service->discoverDetails();
}

void BleController::onServiceStateChanged(QLowEnergyService::ServiceState s)
{
    if (s != QLowEnergyService::RemoteServiceDiscovered)
        return;

    m_writeChar = m_service->characteristic(uuid(M0::WRITE_UUID));
    const QLowEnergyCharacteristic notifyChar = m_service->characteristic(uuid(M0::NOTIFY_UUID));
    if (!m_writeChar.isValid() || !notifyChar.isValid()) {
        setStatus(QStringLiteral("Missing NUS characteristics"));
        return;
    }
    // Enable notifications: write 0x0100 to the CCCD (0x2902).
    const QLowEnergyDescriptor cccd =
        notifyChar.descriptor(QBluetoothUuid::DescriptorType::ClientCharacteristicConfiguration);
    if (cccd.isValid())
        m_service->writeDescriptor(cccd, QByteArray::fromHex("0100"));

    m_connected = true; emit connectedChanged();
    setStatus(QStringLiteral("Connected — sending handshake…"));

    // Mirror the app: brief pause, then send the default 0000 password.
    QTimer::singleShot(800, this, [this]() {
        writeCommand(M0::password(0));
        m_ready = true; emit readyChanged();
        setStatus(QStringLiteral("Ready. Unlock, then kick-start to ride."));
    });
}

void BleController::onCharacteristicChanged(const QLowEnergyCharacteristic &, const QByteArray &v)
{
    const M0::Telemetry t = M0::parse(v);
    if (t.valid) { m_t = t; m_hasData = true; emit telemetryChanged(); }
}

// ---- commands -------------------------------------------------------------
void BleController::writeCommand(const QByteArray &cmd)
{
    if (!m_service || !m_writeChar.isValid()) {
        setStatus(QStringLiteral("Not connected"));
        return;
    }
    const auto mode = (m_writeChar.properties() & QLowEnergyCharacteristic::WriteNoResponse)
                          ? QLowEnergyService::WriteWithoutResponse
                          : QLowEnergyService::WriteWithResponse;
    m_service->writeCharacteristic(m_writeChar, cmd, mode);
}

void BleController::unlock()          { writeCommand(M0::unlock());     setStatus(QStringLiteral("Unlock sent")); }
void BleController::lock()            { writeCommand(M0::lock(true));   setStatus(QStringLiteral("Lock sent")); }
void BleController::setGear(int g)    { writeCommand(M0::gear(g)); }
void BleController::setLight(bool on) { writeCommand(M0::light(on)); }
void BleController::setCruise(bool on){ writeCommand(M0::cruise(on)); }
void BleController::resetMileage()    { writeCommand(M0::clearMileage()); setStatus(QStringLiteral("Mileage reset sent")); }

void BleController::disconnectScooter()
{
    // Just drop the BLE link — do NOT lock. Whatever state the scooter is in
    // (e.g. unlocked) is left as-is, so you can ride on without the app.
    if (m_control)
        m_control->disconnectFromDevice();
}
