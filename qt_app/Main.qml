import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: win
    visible: true
    width: 440
    height: 820
    title: "Smacircle S1"
    color: bg

    readonly property color bg:     "#0f1116"
    readonly property color card:   "#1a1d27"
    readonly property color line:   "#2a2e3a"
    readonly property color accent: "#2ecc71"
    readonly property color danger: "#e74c3c"
    readonly property color txt:    "#eef1f6"
    readonly property color dim:    "#7e8595"
    readonly property string unk:   "—"   // shown whenever the value is genuinely unknown

    // ---------- reusable styled button ----------
    component Btn: Button {
        id: b
        property color fill: win.card
        property color fg: win.txt
        property color edge: win.line
        implicitHeight: 52
        font.pixelSize: 15
        font.bold: true
        background: Rectangle {
            radius: 12
            color: !b.enabled ? "#181b23" : (b.down ? Qt.darker(b.fill, 1.25) : b.fill)
            border.color: b.enabled ? b.edge : "transparent"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 90 } }
        }
        contentItem: Text {
            text: b.text
            color: b.enabled ? b.fg : "#4b5160"
            font: b.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    // ---------- one status row ----------
    component Stat: RowLayout {
        property string label
        property string value
        property color valueColor: win.txt
        Layout.fillWidth: true
        Label { text: parent.label; color: win.dim; font.pixelSize: 14 }
        Item { Layout.fillWidth: true }
        Label { text: parent.value; color: parent.valueColor; font.pixelSize: 14; font.bold: true }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14

        // ---- header ----
        RowLayout {
            Layout.fillWidth: true
            Label { text: "Smacircle S1"; color: win.txt; font.pixelSize: 24; font.bold: true }
            Item { Layout.fillWidth: true }
            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                width: 9; height: 9; radius: 4.5
                color: ble.connected ? win.accent : "#4b5160"
            }
            Label {
                text: ble.connected ? "online" : "offline"
                color: ble.connected ? win.accent : win.dim
                font.pixelSize: 12; leftPadding: 6
            }
        }
        Label {
            text: ble.status; color: win.dim; font.pixelSize: 12
            wrapMode: Text.WordWrap; Layout.fillWidth: true
        }

        // ---- hero tiles: battery + speed (— until telemetry arrives) ----
        RowLayout {
            Layout.fillWidth: true; spacing: 14
            Repeater {
                model: [
                    { big: ble.hasData ? ble.battery + "%" : win.unk, sub: "BATTERY",
                      col: !ble.hasData ? win.dim : (ble.battery <= 15 ? win.danger : win.accent) },
                    { big: ble.hasData ? ble.speed.toFixed(1) : win.unk, sub: "SPEED · km/h",
                      col: ble.hasData ? win.txt : win.dim }
                ]
                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true; Layout.preferredHeight: 132
                    radius: 16; color: win.card; border.color: win.line; border.width: 1
                    ColumnLayout {
                        anchors.centerIn: parent; spacing: 4
                        Label { text: modelData.big; color: modelData.col
                                font.pixelSize: 44; font.bold: true
                                Layout.alignment: Qt.AlignHCenter }
                        Label { text: modelData.sub; color: win.dim
                                font.pixelSize: 11; font.letterSpacing: 1.5
                                Layout.alignment: Qt.AlignHCenter }
                    }
                }
            }
        }

        // ---- status card (all "—" until we actually know) ----
        Rectangle {
            Layout.fillWidth: true; radius: 16; color: win.card
            border.color: win.line; border.width: 1
            Layout.preferredHeight: statusCol.implicitHeight + 32
            ColumnLayout {
                id: statusCol
                anchors.fill: parent; anchors.margins: 16; spacing: 11
                Stat { label: "State"
                       value: ble.hasData ? (ble.locked ? "LOCKED" : "UNLOCKED") : win.unk
                       valueColor: !ble.hasData ? win.dim : (ble.locked ? win.danger : win.accent) }
                Stat { label: "Mode"
                       value: ble.hasData ? (ble.gear === 1 ? "SPORT" : "NORMAL") : win.unk
                       valueColor: ble.hasData ? win.txt : win.dim }
                Stat { label: "Light"
                       value: ble.hasData ? (ble.light ? "ON" : "OFF") : win.unk
                       valueColor: !ble.hasData ? win.dim : (ble.light ? win.accent : win.dim) }
                Stat { label: "Cruise"
                       value: ble.hasData ? (ble.cruise ? "ON" : "OFF") : win.unk
                       valueColor: !ble.hasData ? win.dim : (ble.cruise ? win.accent : win.dim) }
                Stat { label: "Trip"
                       value: ble.hasData ? ble.trip.toFixed(2) + " km" : win.unk
                       valueColor: ble.hasData ? win.txt : win.dim }
                Stat { label: "Total"
                       value: ble.hasData ? ble.total.toFixed(1) + " km" : win.unk
                       valueColor: ble.hasData ? win.txt : win.dim }
                Stat { label: "Fault"
                       value: ble.hasData ? (ble.fault ? "⚠ CHECK" : "none") : win.unk
                       valueColor: ble.fault && ble.hasData ? win.danger : win.dim }
            }
        }

        // ---- connect (shown until connected) ----
        Btn {
            Layout.fillWidth: true
            visible: !ble.connected
            enabled: !ble.scanning
            text: ble.scanning ? "Scanning…" : "Scan & Connect"
            fill: win.accent; fg: "#0a0c10"; edge: "transparent"
            onClicked: ble.startScan()
        }

        // ---- primary unlock / lock (neutral until status known) ----
        Btn {
            Layout.fillWidth: true; implicitHeight: 64
            visible: ble.connected
            enabled: ble.hasData
            text: ble.hasData ? (ble.locked ? "UNLOCK" : "LOCK") : "Reading status…"
            font.pixelSize: 21
            fill: !ble.hasData ? win.card : (ble.locked ? win.accent : win.danger)
            fg: "#0a0c10"; edge: "transparent"
            onClicked: ble.locked ? ble.unlock() : ble.lock()
        }

        // ---- mode / light ----
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Btn {
                Layout.fillWidth: true; enabled: ble.hasData
                text: ble.hasData ? (ble.gear === 1 ? "● SPORT" : "○ NORMAL") : "Mode"
                fill: (ble.hasData && ble.gear === 1) ? win.accent : win.card
                fg: (ble.hasData && ble.gear === 1) ? "#0a0c10" : win.txt
                onClicked: ble.setGear(ble.gear === 1 ? 0 : 1)
            }
            Btn {
                Layout.fillWidth: true; enabled: ble.hasData
                text: ble.hasData ? (ble.light ? "Light ON" : "Light OFF") : "Light"
                fill: (ble.hasData && ble.light) ? win.accent : win.card
                fg: (ble.hasData && ble.light) ? "#0a0c10" : win.txt
                onClicked: ble.setLight(!ble.light)
            }
        }

        // ---- cruise / reset ----
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Btn {
                Layout.fillWidth: true; enabled: ble.hasData
                text: ble.hasData ? (ble.cruise ? "Cruise ON" : "Cruise OFF") : "Cruise"
                fill: (ble.hasData && ble.cruise) ? win.accent : win.card
                fg: (ble.hasData && ble.cruise) ? "#0a0c10" : win.txt
                onClicked: ble.setCruise(!ble.cruise)
            }
            Btn {
                Layout.fillWidth: true; enabled: ble.connected
                text: "Reset trip"
                onClicked: ble.resetMileage()
            }
        }

        Item { Layout.fillHeight: true }

        // ---- disconnect (leaves the scooter as-is, does NOT lock) ----
        Btn {
            Layout.fillWidth: true; implicitHeight: 44
            visible: ble.connected
            text: "Disconnect"
            fill: win.card; fg: win.dim
            onClicked: ble.disconnectScooter()
        }
    }
}
