import QtQuick
import QtQuick.Controls

import "../components"
import "../styles"


Page {
    id: overviewPage

    background: Rectangle { color: Theme.bg2 }
    padding: 2

    // Flickable that wraps everything so it's scrollable
    PageScroll {
        id: overviewPageScroll

        contentWidth: pageColumn.width
        contentHeight: pageColumn.height

        // Content Lives here
        Column {
            id: pageColumn

            width: overviewPageScroll.width
            spacing: 10
            padding: 10

            // Back button to bring you back to your Home Page Library
            NormalButton {
                text: "Back"
                fontSize: 18
                paddingAmount: 20

                onClicked: {
                    pageStack.navigate("pages/Home.qml", 1)
                }
            }

            // Anime Details
            Column {
                width: overviewPageScroll.width

                Rectangle {
                    width: parent.width
                    height: 300

                    color: "red"
                }
            }
        }
    }
}
