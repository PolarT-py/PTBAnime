import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../styles"


Page {
    id: homePage

    Rectangle {
        anchors.fill: parent
        color: Theme.bg2

        Text {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter

            text: "Welcome to PTBAnime!"
            font.pixelSize: 24
            color: "white"
        }

        Button {
            text: "To Overview"
            onClicked: {
                pageStack.navigate("pages/Overview.qml", 2)
            }
        }
    }
}
