import QtQuick
import QtQuick.Controls

import "../styles"


Column {
    // The Cover for the Anime
    Image {
        source: "../../assets/images/anime_card_thumbnail.png"
        fillMode: Image.PreserveAspectCrop
        clip: true

        width: 200
        height: 300
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
