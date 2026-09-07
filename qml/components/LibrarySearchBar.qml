import QtQuick
import QtQuick.Controls

import "../styles"


SearchField {
    property bool isVisible: true
    visible: isVisible

    clearIndicator.indicator: null
    searchIndicator.indicator: null

    width: parent.width * 0.7
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.verticalCenter: parent.verticalCenter

    font.pixelSize: 16

    padding: 8
    leftPadding: 16
    rightPadding: 30

    background: Rectangle { color: Theme.bg3; radius: 10; border.color: Theme.fg3; border.width: 1 }

    palette {
        buttonText: Theme.fg1
        text: Theme.fg1
    }

    Icon {
        icon: "search"

        anchors.right: parent.right
        anchors.rightMargin: 13
        anchors.top: parent.top
        anchors.topMargin: 7
    }

    onTextEdited: {
        backend.set_search_filter(text)
    }
}
