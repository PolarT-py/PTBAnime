import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../styles"


Pane {
    height: parent.height
    spacing: 0

    background: Rectangle { color: Theme.bg1; border.color: Theme.bg3; border.width: 1 }

    ColumnLayout {
        anchors.fill: parent
        spacing: 6

        // Home Button at the top
        Button {
            text: "🏠"
            font.pixelSize: 30

            Layout.alignment: Qt.AlignTop

            Layout.preferredWidth: 40
            Layout.preferredHeight: 40

            onClicked: {
                pageStack.navigate("pages/Home.qml", 1)
            }
        }

        // Fill in the middle space
        Item { Layout.fillHeight: true }

        // Buttons on the bottom
        ColumnLayout {
            spacing: 6

            // Credits Button
            Button {
                text: "🎬"
                font.pixelSize: 30

                Layout.preferredWidth: 40
                Layout.preferredHeight: 40

                onClicked: {
                    pageStack.navigate("pages/Credits.qml", 3)
                }
            }

            // Settings Button
            Button {
                text: "⚙️"
                font.pixelSize: 30

                Layout.preferredWidth: 40
                Layout.preferredHeight: 40

                onClicked: {
                    pageStack.navigate("pages/Settings.qml", 0)
                }
            }
        }
    }
}
