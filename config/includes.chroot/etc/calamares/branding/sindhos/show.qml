/* SindhOS installer slideshow (Calamares, slideshow API 2). */
import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    Timer {
        interval: 15000
        repeat: true
        running: presentation.activatedInCalamares
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Image {
            id: art1
            source: "slide1.png"
            width: 640; height: 360
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
        Text {
            anchors.horizontalCenter: art1.horizontalCenter
            anchors.top: art1.bottom
            anchors.topMargin: 12
            text: "سنڌ او ايس ۾ ڀلي ڪري آيا<br/>Welcome to SindhOS. The rest of the installation is automatic and takes a few minutes."
            wrapMode: Text.WordWrap
            width: 600
            horizontalAlignment: Text.AlignHCenter
        }
    }

    Slide {
        Text {
            anchors.centerIn: parent
            text: "Ctrl+Space: English / سنڌي<br/>Type Sindhi in Roman letters or with the Sindhi keyboard."
            wrapMode: Text.WordWrap
            width: 600
            horizontalAlignment: Text.AlignHCenter
        }
    }

    function onActivate() { }
    function onLeave() { }
}
