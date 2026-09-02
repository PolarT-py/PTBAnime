import QtQuick
import QtQuick.Controls

import "../components"
import "../styles"


Page {
    id: homePage

    background: Rectangle { color: Theme.bg2 }
    padding: 2

    // Flickable that wraps everything so it's scrollable
    PageScroll {
        id: homePageScroll

        contentWidth: pageColumn.width
        contentHeight: pageColumn.height

        // Content Lives here
        Column {
            id: pageColumn

            width: homePageScroll.width
            spacing: 10

            Button {
                text: "To Overview"
                onClicked: {
                    pageStack.navigate("pages/Overview.qml", 2)
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter

                text: "Welcome to PTBAnime!"
                font.pixelSize: 24
                color: Theme.fg1
            }

            // Wrapper for the Grid
            Item {
                id: gridContainer

                width: Math.max(homePageScroll.width, homePageGrid.width)
                height: homePageGrid.height

                implicitWidth: width
                implicitHeight: height

                // Grid for the Cards
                Grid {
                    id: homePageGrid

                    property int minimumSpacing: 20 // The minimum column spacing inbetween the Cards
                    property int cardWidth: 200  // This is hard coded for Card's width

                    anchors.horizontalCenter: parent.horizontalCenter

                    columns: Math.max(1, Math.floor((homePageScroll.width - padding * 2 + columnSpacing) / (cardWidth + columnSpacing)))

                    columnSpacing: minimumSpacing
                    rowSpacing: 40

                    padding: 10

                    // Placeholder cards
                    Repeater {
                        model: 20
                        delegate: Card {}
                    }
                }
            }
        }
    }
}
