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

    color: Theme.bg2
    visible: true

    // The beginning
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // The Sidebar
        Sidebar {
            id: sidebar

            Layout.fillHeight: true
            Layout.preferredWidth: 58
        }

        // Main Content Area
        ColumnLayout {
            spacing: 0

            // Top Bar (Disable for now since it's literally useless)
            // Topbar {
            //     Layout.fillWidth: true
            //     Layout.preferredHeight: 50
            // }

            // Page stack for storing our pages
            StackView {
                id: pageStack

                property int currentPage: 1
                property bool goingForward: true

                // Function for controlling swipe direction and page navigation
                // -1: Setup, 0: Settings, 1: Home, 2: Overview, 3: Credits
                function navigate(page, pageIndex) {
                    // Make sure it's on a different page
                    if (pageIndex != currentPage) {
                        // Set new direction and go to the new page
                        goingForward = pageIndex > currentPage
                        currentPage = pageIndex
                        replace(page)

                        // If it's going to home, then execute cache manager
                        if (pageIndex == 1) {
                            backend.update_cache()
                        }
                    }
                }

                // Make Page take up the as much space as it can
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true  // Don't overlap the sidebar during animations

                // Cool Animation Enter Animation
                replaceEnter: Transition {
                    NumberAnimation {
                        property: "x"
                        from: pageStack.goingForward ? pageStack.width : -pageStack.width
                        to: 0
                        duration: 500
                        easing.type: Easing.OutExpo
                    }
                }

                // Cool Animation Exit Animation
                replaceExit: Transition {
                    NumberAnimation {
                        property: "x"
                        from: 0
                        to: pageStack.goingForward ? -pageStack.width : pageStack.width
                        duration: 500
                        easing.type: Easing.OutExpo
                    }
                }

                // Cool Animation Enter Animation (Push)
                pushEnter: Transition {
                    NumberAnimation {
                        property: "x"
                        from: pageStack.goingForward ? pageStack.width : -pageStack.width
                        to: 0
                        duration: 500
                        easing.type: Easing.OutExpo
                    }
                }

                // Cool Animation Exit Animation (Push)
                pushExit: Transition {
                    NumberAnimation {
                        property: "x"
                        from: 0
                        to: pageStack.goingForward ? -pageStack.width : pageStack.width
                        duration: 500
                        easing.type: Easing.OutExpo
                    }
                }

                // Set the Home Page when you load in
                Component.onCompleted: {
                    if (backend.is_first_time) {
                        pageStack.currentPage = -1
                        pageStack.push("pages/Setup.qml", -1)
                    } else {
                        pageStack.currentPage = 1
                        pageStack.push("pages/Home.qml", 1)
                        backend.update_cache()
                    }
                }
            }
        }
    }
}
