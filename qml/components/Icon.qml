import QtQuick

import "../styles"


Text {
    property string icon: "?"
    property int size: 20

    text: icon

    font.family: Theme.materialSymbols
    font.pixelSize: size
    font.kerning: true
    font.features: { "rlig": 1 }

    color: Theme.fg1
}
