import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Rectangle {
    id: root
    width: 800
    height: 500
    color: "#f5f5f5"

    // Định nghĩa tín hiệu - nối với callback Python
    signal manualButtonPressed()
    signal manualButtonReleased()
    signal autoButtonClicked()
    signal abortButtonClicked()
    signal modeButtonClicked()
    signal sendButtonClicked(string text)
    signal settingsButtonClicked()
    // Tín hiệu liên quan tới thanh tiêu đề
    signal titleMinimize()
    signal titleClose()
    signal titleDragStart(real mouseX, real mouseY)
    signal titleDragMoveTo(real mouseX, real mouseY)
    signal titleDragEnd()

    // Bố cục chính
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // Thanh tiêu đề tùy chỉnh: thu nhỏ, đóng và kéo được
        Rectangle {
            id: titleBar
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: "#f7f8fa"
            border.width: 0

            // Kéo toàn bộ thanh tiêu đề (dùng tọa độ màn hình để tránh sai lệch tích lũy)
            // Đặt ở lớp thấp nhất để MouseArea của nút phản hồi trước
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onPressed: {
                    root.titleDragStart(mouse.x, mouse.y)
                }
                onPositionChanged: {
                    if (pressed) {
                        root.titleDragMoveTo(mouse.x, mouse.y)
                    }
                }
                onReleased: {
                    root.titleDragEnd()
                }
                z: 0  // Lớp thấp nhất
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                spacing: 8
                z: 1  // Lớp nút nằm trên lớp kéo

                // Khu vực kéo ở bên trái
                Item { id: dragArea; Layout.fillWidth: true; Layout.fillHeight: true }

                // Thu nhỏ
                Rectangle {
                    id: btnMin
                    width: 24; height: 24; radius: 6
                    color: btnMinMouse.pressed ? "#e5e6eb" : (btnMinMouse.containsMouse ? "#f2f3f5" : "transparent")
                    z: 2  // Đảm bảo nút ở lớp trên cùng
                    Text { anchors.centerIn: parent; text: "–"; font.pixelSize: 14; color: "#4e5969" }
                    MouseArea {
                        id: btnMinMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.titleMinimize()
                    }
                }

                // Đóng
                Rectangle {
                    id: btnClose
                    width: 24; height: 24; radius: 6
                    color: btnCloseMouse.pressed ? "#f53f3f" : (btnCloseMouse.containsMouse ? "#ff7875" : "transparent")
                    z: 2  // Đảm bảo nút ở lớp trên cùng
                    Text { anchors.centerIn: parent; text: "×"; font.pixelSize: 14; color: btnCloseMouse.containsMouse ? "white" : "#86909c" }
                    MouseArea {
                        id: btnCloseMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.titleClose()
                    }
                }
            }
        }

        // Khu vực thẻ trạng thái
        Rectangle {
            id: statusCard
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                // Nhãn trạng thái
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    color: "#E3F2FD"
                    radius: 12

                    Text {
                        anchors.centerIn: parent
                        text: displayModel ? displayModel.statusText : "Trạng thái: Chưa kết nối"
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: 14
                        font.weight: Font.Bold
                        color: "#2196F3"
                    }
                }

                // Khu vực hiển thị biểu cảm
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 120

                    // Nạp biểu cảm động: AnimatedImage cho GIF, Image cho ảnh tĩnh, Text cho emoji
                    Loader {
                        id: emotionLoader
                        anchors.centerIn: parent
                        width: Math.min(parent.width * 0.8, 200)
                        height: Math.min(parent.height * 0.8, 200)

                        sourceComponent: {
                            var path = displayModel ? displayModel.emotionPath : ""
                            if (!path || path.length === 0) {
                                return emojiComponent
                            }
                            if (path.indexOf(".gif") !== -1) {
                                return gifComponent
                            }
                            if (path.indexOf(".") !== -1) {
                                return imageComponent
                            }
                            return emojiComponent
                        }

                        // Thành phần ảnh động GIF
                        Component {
                            id: gifComponent
                            AnimatedImage {
                                fillMode: Image.PreserveAspectFit
                                source: displayModel ? ("file://" + displayModel.emotionPath) : ""
                                playing: true
                                speed: 1.05
                                cache: true
                            }
                        }

                        // Thành phần ảnh tĩnh
                        Component {
                            id: imageComponent
                            Image {
                                fillMode: Image.PreserveAspectFit
                                source: displayModel ? ("file://" + displayModel.emotionPath) : ""
                                cache: true
                            }
                        }

                        // Thành phần emoji dạng văn bản
                        Component {
                            id: emojiComponent
                            Text {
                                text: displayModel ? displayModel.emotionPath : "😊"
                                font.pixelSize: 80
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }

                // Khu vực hiển thị văn bản TTS
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    color: "transparent"

                    Text {
                        anchors.fill: parent
                        anchors.margins: 15
                        text: displayModel ? displayModel.ttsText : "Sẵn sàng"
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: 14
                        color: "#555555"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }

        // Khu vực nút (màu sắc và kích thước đồng bộ)
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: "#f7f8fa"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                anchors.bottomMargin: 12
                spacing: 10

                // Nút chế độ thủ công (nhấn giữ để nói) - màu chính
                Button {
                    id: manualBtn
                    Layout.preferredWidth: 140
                    Layout.preferredHeight: 40
                    text: "Nhấn giữ để nói"
                    visible: displayModel ? !displayModel.autoMode : true

                    background: Rectangle {
                        color: manualBtn.pressed ? "#0e42d2" : (manualBtn.hovered ? "#4080ff" : "#165dff")
                        radius: 8

                        Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
                    }

                    contentItem: Text {
                        text: manualBtn.text
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: 13
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onPressed: { manualBtn.text = "Thả để dừng"; root.manualButtonPressed() }
                    onReleased: { manualBtn.text = "Nhấn giữ để nói"; root.manualButtonReleased() }
                }

                // Nút chế độ tự động - màu chính
                Button {
                    id: autoBtn
                    Layout.preferredWidth: 140
                    Layout.preferredHeight: 40
                    text: displayModel ? displayModel.buttonText : "Bắt đầu hội thoại"
                    visible: displayModel ? displayModel.autoMode : false

                    background: Rectangle {
                        color: autoBtn.pressed ? "#0e42d2" : (autoBtn.hovered ? "#4080ff" : "#165dff")
                        radius: 8
                        Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
                    }

                    contentItem: Text { text: autoBtn.text; font.family: "PingFang SC, Microsoft YaHei UI"; font.pixelSize: 13; color: "white"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: root.autoButtonClicked()
                }

                // Ngắt hội thoại - màu phụ
                Button {
                    id: abortBtn
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    text: "Ngắt hội thoại"

                    background: Rectangle { color: abortBtn.pressed ? "#e5e6eb" : (abortBtn.hovered ? "#f2f3f5" : "#eceff3"); radius: 8 }
                    contentItem: Text { text: abortBtn.text; font.family: "PingFang SC, Microsoft YaHei UI"; font.pixelSize: 13; color: "#1d2129"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: root.abortButtonClicked()
                }

                // Nhập và gửi
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    spacing: 8

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        color: "white"
                        radius: 8
                        border.color: textInput.activeFocus ? "#165dff" : "#e5e6eb"
                        border.width: 1

                        TextInput {
                            id: textInput
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: "PingFang SC, Microsoft YaHei UI"
                            font.pixelSize: 13
                            color: "#333333"
                            selectByMouse: true
                            clip: true

                            // Văn bản gợi ý
                            Text { anchors.fill: parent; text: "Nhập nội dung..."; font: textInput.font; color: "#c9cdd4"; verticalAlignment: Text.AlignVCenter; visible: !textInput.text && !textInput.activeFocus }

                            Keys.onReturnPressed: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = "" } }
                        }
                    }

                    Button {
                        id: sendBtn
                        Layout.preferredWidth: 84
                        Layout.preferredHeight: 40
                        text: "Gửi"
                        background: Rectangle { color: sendBtn.pressed ? "#0e42d2" : (sendBtn.hovered ? "#4080ff" : "#165dff"); radius: 8 }
                        contentItem: Text { text: sendBtn.text; font.family: "PingFang SC, Microsoft YaHei UI"; font.pixelSize: 13; color: "white"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        onClicked: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = "" } }
                    }
                }

                // Chế độ (màu phụ)
                Button {
                    id: modeBtn
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    text: displayModel ? displayModel.modeText : "Hội thoại thủ công"
                    background: Rectangle { color: modeBtn.pressed ? "#e5e6eb" : (modeBtn.hovered ? "#f2f3f5" : "#eceff3"); radius: 8 }
                    contentItem: Text { text: modeBtn.text; font.family: "PingFang SC, Microsoft YaHei UI"; font.pixelSize: 13; color: "#1d2129"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: root.modeButtonClicked()
                }

                // Cài đặt (màu phụ)
                Button {
                    id: settingsBtn
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    text: "Cấu hình tham số"
                    background: Rectangle { color: settingsBtn.pressed ? "#e5e6eb" : (settingsBtn.hovered ? "#f2f3f5" : "#eceff3"); radius: 8 }
                    contentItem: Text { text: settingsBtn.text; font.family: "PingFang SC, Microsoft YaHei UI"; font.pixelSize: 13; color: "#1d2129"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: root.settingsButtonClicked()
                }
            }
        }
    }
}
