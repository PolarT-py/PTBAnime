import QtQuick
import QtQuick.Controls
import QtQuick.Effects

import "../styles"


Column {
    id: card_root

    // Properties
    property int anime_id: -1
    property string imageSource: "../../assets/images/anime_card_thumbnail.png"
    property string title: "Insert Anime Name But it's long"
    property string shadowColor: "black"

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
            color: shadowColor
        }

        Image {
            id: coverIMG

            source: card_root.imageSource
            fillMode: Image.PreserveAspectCrop
            clip: true

            width: parent.width
            height: parent.height
        }

        // MultiEffect {  // Test Blur for image
        //     anchors.fill: coverIMG
        //     source: coverIMG

        //     blurEnabled: true
        //     blur: 1.0
        //     blurMax: 42
        //     autoPaddingEnabled: false
        // }
    }

    Spacer {spacing: 10}

    // The Title of the Anime
    Label {
        text: card_root.title
        font.pixelSize: 18

        width: parent.width
        wrapMode: Text.WordWrap

        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter

        color: Theme.fg1
    }
}
