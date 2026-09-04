import QtQuick
import QtQuick.Controls

import "../styles"


Row {
    spacing: 10

    property string optionText: "Option Text Field"
    property string placeholderText: "Placeholder Text"
    property int fieldWidth: 400

    Text {
        text: parent.optionText
        font.pixelSize: 16
        color: Theme.fg1

        anchors.verticalCenter: parent.verticalCenter
    }

    TextField {
        placeholderText: parent.placeholderText
        placeholderTextColor: Theme.fg3
        color: Theme.fg1

        width: parent.fieldWidth

        background: Rectangle {
            color: Theme.bg3
            radius: 5
            border.color: Theme.fg3
        }
    }
}
