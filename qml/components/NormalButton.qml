import QtQuick
import QtQuick.Controls

import "../styles"

Button {
    property int fontSize: 12
    property int paddingAmount: 10
    property int borderRadius: 5
    property int borderWidth: 1
    property string borderColor: Theme.fg3
    property string backgroundColor: Theme.bg3

    font.pixelSize: fontSize

    palette { buttonText: Theme.fg1 }
    background: Rectangle { color: parent.backgroundColor; radius: parent.borderRadius; border.width: parent.borderWidth; border.color: parent.borderColor }

    leftPadding: paddingAmount
    rightPadding: paddingAmount
}
