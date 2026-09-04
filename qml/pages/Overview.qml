import QtQuick
import QtQuick.Controls

import "../components"
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
            color: Theme.fg1
        }

        NormalButton {
            text: "Back"
            fontSize: 20
            paddingAmount: 20

            onClicked: {
                pageStack.navigate("pages/Home.qml", 1)
            }
        }
    }
}
