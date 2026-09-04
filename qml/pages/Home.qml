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
                        model: 13
                        // model: 0
                        delegate: Card {}
                    }
                }
            }

            // Display message when there are no cards
            Column {
                id: noCardsMessage

                anchors.horizontalCenter: parent.horizontalCenter
                visible: homePageGrid.children.length <= 1  // The Repeater counts as a child so need to account for it

                H2 {
                    text: "No Anime Available :("

                    anchors.horizontalCenter: parent.horizontalCenter
                }

                H3 {
                    text: "Make sure to Check your Paths and Folder to make sure it's formatted properly!"

                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Spacer { spacing: 50 }

                Image {
                    source: "../../assets/images/anime_card_thumbnail.png"
                    anchors.horizontalCenter: parent.horizontalCenter

                    width: 100
                    height: 100
                }
            }
        }
    }
}
