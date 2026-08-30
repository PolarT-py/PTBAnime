pragma Singleton

import QtQuick


QtObject {
    property bool dark: true

    readonly property color bg1: dark ? "#121212" : "#ffffff"
    readonly property color bg2: dark ? "#1c1c1c" : "#f2f2f2"
    readonly property color bg3: dark ? "#282828" : "#e5e5e5"

    readonly property color fg1: dark ? "#ffffff" : "#111111"
    readonly property color fg2: dark ? "#cccccc" : "#444444"
    readonly property color fg3: dark ? "#888888" : "#777777"

    // Add Accent Colors
}
