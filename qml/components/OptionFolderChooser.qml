import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import "../styles"


Row {
    spacing: 10

    property string optionText: "Option Text Field"
    property string placeholderText: "Placeholder Text"
    property int fieldWidth: 400
    property string dialogTitle: "Select Folder"

    property alias value: textFieldValue.text

    Text {
        text: parent.optionText
        font.pixelSize: 16
        color: Theme.fg1

        anchors.verticalCenter: parent.verticalCenter
    }

    TextField {
        id: textFieldValue

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

    NormalButton {
        text: "Browse Folder"
        onClicked: folderDialog.open()
    }

    FolderDialog {
        id: folderDialog

        title: parent.dialogTitle

        onAccepted: { textFieldValue.text = selectedFolder }
    }
}
