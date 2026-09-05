import QtQuick
import QtQuick.Controls

import "../styles"


// ToDo
// 
// Anime Path Text Field / Folder chooser
// Dark mode toggle
// Glowing Cards toggle
// Title Mode english/romaji/native
// AniList OAuth option to link/unlink
// AniList option to toggle autosync
// Button to clear all Cache


Page {
    id: settingsPage

    Rectangle {
        anchors.fill: parent
        color: Theme.bg2

        Text {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            
            text: "Settings Page"
            font.pixelSize: 24
            color: Theme.fg1
        }
    }
}
