import QtQuick
import QtQuick.Controls

import "../styles"


Page {
    id: settingsPage

    Rectangle {
        anchors.fill: parent
        color: Theme.bg2

        Text {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            
            text: "Settings Page"
            font.pixelSize: 24
            color: Theme.fg1
        }
    }
}
