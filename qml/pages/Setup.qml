import QtQuick
import QtQuick.Controls

import "../components"
import "../styles"


Page {
    id: setupPage

    background: Rectangle { color: Theme.bg2 }
    padding: 30

    // Flickable that wraps everything so it's scrollable
    PageScroll {
        id: setupPageScroll

        contentWidth: pageColumn.width
        contentHeight: pageColumn.height

        // Content Lives here
        Column {
            id: pageColumn

            width: setupPageScroll.width
            spacing: 10

            H2 {
                text: "Welcome to PTBAnime!"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            P { text: "This is the First Time Setup Page." }

            Spacer {}

            OptionTextField {
                optionText: "ASDASDA:"
                placeholderText: "Name I guess"
            }

            OptionFolderChooser {
                id: animeFolderChooser

                optionText: "Anime Folder:"
                placeholderText: "Path to your Anime Folder"
                dialogTitle: "Select Anime Folder"
            }
        }
    }

    // Finish Button to bring you to the Home Page
    NormalButton {
        id: finishSetupButton

        text: "Finish Setup"
        fontSize: 20
        borderWidth: 1
        borderColor: Theme.bg3
        backgroundColor: Theme.bg1

        width: parent.width * 0.8
        height: 50

        onClicked: {
            // Display message telling the user to wait while scanning is happening
            finishSetupButton.text = "Please wait while we scan through your Anime Folder"

            // Save the Settings
            backend.set_setting("app/anime_folder_path", animeFolderChooser.value)

            // Go to Home
            pageStack.navigate("pages/Home.qml", 1)
        }

        anchors.horizontalCenter: parent.horizontalCenter

        x: (setupPage.availableWidth - width) / 2
        y: setupPage.availableHeight - height - 20
    }
}
