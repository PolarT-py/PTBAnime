import QtQuick

import "../styles"


Flickable {
    anchors.fill: parent
    clip: true
    
    interactive: true
    acceptedButtons: Qt.LeftButton

    // Set the Background
    Rectangle {
        color: Theme.bg2
        
        width: parent.width
        height: parent.height
    }
}
