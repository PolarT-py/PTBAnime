import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

import "components"
import "pages"
import "styles"


Window {
    id: mainWindow
    title: "PTBAnime"

    width: 1000
    height: 700
    minimumWidth: 1000
    minimumHeight: 700

    visible: true

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // The Sidebar
        Sidebar {
            Layout.fillHeight: true
            Layout.preferredWidth: 58
        }

        // Main Content Area
        ColumnLayout {
            spacing: 0

            // Top Bar
            Topbar {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
            }

            // Page stack for storing our pages
            StackView {
                id: pageStack

                property int currentPage: 1
                property bool goingForward: true

                // Function for controlling swipe direction and page navigation
                // 0: Settings, 1: Home, 2: Overview, 3: Credits
                function navigate(page, pageIndex) {
                    // Make sure it's on a different page
                    if (pageIndex != currentPage) {
                        // Set new direction and go to the new page
                        goingForward = pageIndex > currentPage
                        currentPage = pageIndex
                        replace(page)
                    }
                }

                // Make Page take up the as much space as it can
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true  // Don't overlap the sidebar during animations

                replaceEnter: Transition {
                    NumberAnimation {
                        property: "x"
                        from: pageStack.goingForward ? pageStack.width : -pageStack.width
                        to: 0
                        duration: 500
                        easing.type: Easing.OutExpo
                    }
                }

                replaceExit: Transition {
                    NumberAnimation {
                        property: "x"
                        from: 0
                        to: pageStack.goingForward ? -pageStack.width : pageStack.width
                        duration: 500
                        easing.type: Easing.OutExpo
                    }
                }

                initialItem: Home { id: homePage }
            }
        }
    }
}
