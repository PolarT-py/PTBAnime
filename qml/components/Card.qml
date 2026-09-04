import QtQuick
import QtQuick.Controls
import QtQuick.Effects

import "../styles"


Column {
    // The Button and Cover for the Anime
    Button {
        width: 200
        height: 300
        
        background: Rectangle { color: "Transparent" }

        // When pressed, go to overview and update with fetched Anime information
        onClicked: {
            pageStack.navigate("pages/Overview.qml", 2)
        }

        RectangularShadow {
            anchors.fill: coverIMG
            anchors.centerIn: coverIMG

            offset.x: -2
            offset.y: 2
            blur: 10
            spread: 0.1
        }

        Image {
            id: coverIMG

            source: "../../assets/images/anime_card_thumbnail.png"
            fillMode: Image.PreserveAspectCrop
            clip: true

            width: parent.width
            height: parent.height
        }
    }

    // The Title of the Anime
    Label {
        text: "Insert Anime Name But it's long"
        font.pixelSize: 18

        width: parent.width
        wrapMode: Text.WordWrap

        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter

        color: Theme.fg1
    }
}
