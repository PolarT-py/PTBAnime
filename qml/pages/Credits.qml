import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../styles"


Page {
    id: creditsPage

    Rectangle {
        anchors.fill: parent
        color: Theme.bg2

        Text {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter

            text: "Credits screen"
            font.pixelSize: 24
            color: "white"
        }
    }
}
