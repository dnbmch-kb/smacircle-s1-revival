#include <QGuiApplication>
#include <QIcon>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "blecontroller.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("Smacircle S1"));
    app.setOrganizationName(QStringLiteral("Smacircle"));
    app.setWindowIcon(QIcon(QStringLiteral(":/icon/icon.png")));

    // Declare the controller BEFORE the engine so the engine (and its QML
    // bindings that reference `ble`) is destroyed first at shutdown —
    // otherwise teardown spews "Cannot read property of null" warnings.
    BleController ble;
    QQmlApplicationEngine engine;
    engine.rootContext()->setContextProperty(QStringLiteral("ble"), &ble);
    engine.loadFromModule("Smacircle", "Main");
    if (engine.rootObjects().isEmpty())
        return -1;
    return app.exec();
}
