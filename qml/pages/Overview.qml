import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../styles"


Page {
    id: overviewPage

    Rectangle {
        anchors.fill: parent
        color: Theme.bg2

        Text {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            
            text: "Overview Page"
            font.pixelSize: 24
            color: "white"
        }

        Button {
            text: "To Home"
            onClicked: {
                pageStack.navigate("pages/Home.qml", 1)
            }
        }
    }
}
