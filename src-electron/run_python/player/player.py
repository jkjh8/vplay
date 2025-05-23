import os
import sys
import socket
import threading
import win32process, win32con
import json
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget

import vlc

player_data = {
    "event": "",
    "buffering": 0,
    "media_path": "",
    "filename": "",
    "volume": 100,
    "speed": 1.0,
    "duration": 0,
    "time": 0,
    "position": 0.0,
    "fullscreen": False,
    "playing": False,
}
default = {
    "background_color": "white",
    "fullscreen": False,
    "logo": {
        "path": "",
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0,
        "show": False,
    }
}

MULTICAST_GROUP = "239.255.255.250"
MULTICAST_PORT = 1234

class stdinReaderr(QThread):
    message_received = Signal(str)
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                if self.running == False:
                    break
                data = sys.stdin.readline()
                if data:
                    self.message_received.emit(data.strip())
            except Exception as e:
                self.print_json("error", {"message": f"Error reading stdin: {e}"})
                break

    def stop(self):
        self.running = False

class Player(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player_data = player_data
        self._default = default
        self.setWindowTitle("VP")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))
        # logo_label과 svg_widget 초기화
        self.logo_label = QLabel(self)
        self.logo_label.setVisible(False)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.svg_widget = QSvgWidget(self)
        self.svg_widget.setVisible(False)
        # 레이아웃 설정
        layout = QVBoxLayout()
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        # 설정 로드 및 초기화
        self._default = self.load_default()
        self.initPlayer()
        # 입출력 스레드 초기화
        self.initStdinThread()

        self.set_background_color(self._default["background_color"])
        self.set_fullscreen(self._default["fullscreen"])
        self.set_logo(self._default["logo"]["path"])
        self.show_logo(self._default["logo"]["show"])
        # 우선순위 설정
        try:
            handle = win32process.GetCurrentProcess()
            win32process.SetPriorityClass(handle, win32con.REALTIME_PRIORITY_CLASS)
        except Exception as e:
            self.print_json("error", {"message": f"우선순위 설정 실패: {e}"})

    def save_default(self, data=None):
        # Save default settings to a file
        if not data:
            return
        try:
            with open("default.json", "w") as f:
                json.dump(self._default, f)
            self.print_json("info", {"message": "Default settings saved."})
        except Exception as e:
            self.print_json("error", {"message": f"Error saving default settings: {e}"})

    def load_default(self):
        # Load default settings from a file
        try:
            with open("default.json", "r") as f:
                data = json.load(f)
            self.print_json("info", {"message": "Default settings loaded."})
            return data
        except FileNotFoundError:
            self.print_json("error", {"message": "Default settings file not found."})
            return self._default
        except json.JSONDecodeError:
            self.print_json("error", {"message": "Error decoding JSON from default settings file."})
            return self._default
        except Exception as e:
            self.print_json("error", {"message": f"Error loading default settings: {e}"})
            return self._default

    def initStdinThread(self):
        # Initialize stdin thread
        self.stdin_thread = stdinReaderr()
        self.stdin_thread.message_received.connect(self.handle_message)
        self.stdin_thread.start()

    def initPlayer(self):
        # Initialize VLC player with hardware decoding options
        self.instance = vlc.Instance(
            "--no-video-title-show",
            "--avcodec-hw=any",
            "--no-drop-late-frames",
            "--no-skip-frames"
        )
        self.player = self.instance.media_player_new()
        
        # 플레이어 캔버스 지정하기
        self.player.set_hwnd(int(self.winId()))
        # 이벤트 핸들러 등록하기
        self.init_events()
        
    def init_events(self):
        # 이벤트 등록하기
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerBuffering, self.on_buffering)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerTimeChanged, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerPlaying, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerPaused, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerStopped, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEncounteredError, self.on_error)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerMediaChanged, self.update_player_data)
        
    def on_buffering(self, event):
        buffering = getattr(event.u, "buffering", None)
        if buffering is not None:
            self.player_data["buffering"] = buffering
        else:
            self.print_json("error", {"message": "Buffering event received, but no buffering info found."})

    def on_end_reached(self, event):
        self.update_player_data(event)
        # self.player.stop()

    def on_error(self, event):
        self.print_json("error", {"message": "Error occurred"})

    def update_player_data(self, event=None):
        event_type = getattr(event, "type", "manual")
        self.player_data["event"] = str(event_type)
        media = self.player.get_media()
        if media is not None:
            self.player_data["filename"] = media.get_mrl()
        else:
            self.player_data["filename"] = ""
        self.player_data["duration"] = self.player.get_length()
        self.player_data["time"] = self.player.get_time()
        self.player_data["position"] = self.player.get_position()
        self.player_data["playing"] = self.player.is_playing()
        self.player_data["volume"] = self.player.audio_get_volume()
        self.player_data["speed"] = self.player.get_rate()
        self.player_data["fullscreen"] = self.player.get_fullscreen()
        self.print_json("info", self.player_data)

    @Slot(str)
    def handle_message(self, data):
        # stdin에서 읽은 데이터는 이미 str이므로 decode 필요 없음
        self.receive_udp_data = data.strip()
        # play:media_path
        if self.receive_udp_data.startswith("play:"):
            media_path = self.receive_udp_data[5:]  # "play:" 다음부터 끝까지
            self.set_media(media_path.strip())
            self.player.play()
        # set:media_path
        elif self.receive_udp_data.startswith("set:"):
            media_path = self.receive_udp_data[4:]
            self.set_media(media_path.strip())
        # stop
        elif self.receive_udp_data.startswith("stop"):
            self.player.stop()
        # pause
        elif self.receive_udp_data.startswith("pause"):
            self.player.pause()
        # resume
        elif self.receive_udp_data.startswith("resume"):
            self.player.play()
        # play
        elif self.receive_udp_data.startswith("play"):
            self.player.play()
        # set:volume
        elif self.receive_udp_data.startswith("volume:"):
            volume = int(self.receive_udp_data[7:])
            if 0 <= volume <= 100:
                self.player.audio_set_volume(volume)
            else:
                self.print_json("error", {"message": "Invalid volume value. Must be between 0 and 100."})
        # set:position
        elif self.receive_udp_data.startswith("position:"):
            position = float(self.receive_udp_data[9:])
            if 0.0 <= position <= 1.0:
                self.player.set_position(position)
            else:
                self.print_json("error", {"message": "Invalid position value. Must be between 0.0 and 1.0."})
        # set:speed
        elif self.receive_udp_data.startswith("speed:"):
            speed = float(self.receive_udp_data[6:])
            if speed > 0:
                self.player.set_rate(speed)
            else:
                self.print_json("error", {"message": "Invalid speed value. Must be greater than 0."})
        # set:fullscreen
        elif self.receive_udp_data.startswith("fullscreen:"):
            fullscreen = self.receive_udp_data[11:].lower() == "true"
            self.set_fullscreen(fullscreen)
            self._default["fullscreen"] = fullscreen
            self.save_default(self._default)
        # set: background_color
        elif self.receive_udp_data.startswith("background_color:"):
            color = self.receive_udp_data[17:]
            self.set_background_color(color)
            self._default["background_color"] = color
            self.save_default(self._default)
        # set:logo
        elif self.receive_udp_data.startswith("set_logo:"):
            logo_path = self.receive_udp_data[9:]
            self.set_logo(logo_path.strip())
            self._default["logo"]["path"] = logo_path.strip()
            self.save_default(self._default)
            
        # show:logo
        elif self.receive_udp_data.startswith("show_logo:"):
            value = self.receive_udp_data[10:].lower() == "true"
            self.show_logo(value)
            self._default["logo"]["show"] = value
            self.save_default(self._default)
        
        elif self.receive_udp_data.startswith("logo_size:"):
            try:
                size = self.receive_udp_data[10:].split(",")
                if len(size) == 2:
                    width = int(size[0])
                    height = int(size[1])
                    self._default["logo"]["width"] = width
                    self._default["logo"]["height"] = height
                    self.save_default(self._default)
                    self.show_logo(self._default["logo"]["show"])
                else:
                    self.print_json("error", {"message": "Invalid logo size format. Use 'width,height'."})
            except ValueError:
                self.print_json("error", {"message":"Invalid logo size values. Must be integers."})

    def set_fullscreen(self, fullscreen):
        try:
            if fullscreen:
                self.showFullScreen()
            else:
                self.showNormal()
            self.player.set_fullscreen(fullscreen)
            self.player_data["fullscreen"] = fullscreen
            self.player.set_hwnd(int(self.winId()))
            self.update_player_data(None)  # 또는 그냥 self.update_player_data()
        except Exception as e:
            self.print_json("error", {"message": f"Error setting fullscreen: {e}"})

    def set_background_color(self, color):
        try:
            # Set background color
            self.setStyleSheet(f"background-color: {color};")
            self.print_json("default", self._default)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting background color: {e}"})

    def set_logo(self, logo_path):
        try:
            # Set logo path
            if not logo_path or logo_path == "":
                self.print_json("error", {"message": "No logo path provided."})
                return
            self._default["logo"]["path"] = os.path.normpath(logo_path.strip())
            self.print_json("default", self._default)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting logo: {e}"})
            
    def show_logo(self, value):
        try:
            logo_path = self._default["logo"]["path"]
            if not logo_path or not os.path.isfile(logo_path):
                self.logo_label.setVisible(False)
                self.svg_widget.setVisible(False)
                return
            ext = os.path.splitext(logo_path)[1].lower()
            width = self._default["logo"].get("width", 0)
            height = self._default["logo"].get("height", 0)
            if ext == ".svg":
                self.logo_label.setVisible(False)
                self.svg_widget.load(logo_path)
                self.svg_widget.setVisible(value)
                self.svg_widget.raise_()
                if width == 0 or height == 0:
                    self.svg_widget.adjustSize()
                    self.svg_widget.move(
                        (self.width() - self.svg_widget.width()) // 2,
                        (self.height() - self.svg_widget.height()) // 2
                    )
                else:
                    self.svg_widget.resize(width, height)
                    self.svg_widget.move(
                        (self.width() - width) // 2,
                        (self.height() - height) // 2
                    )
            else:
                pixmap = QPixmap(logo_path)
                if pixmap.isNull():
                    self.logo_label.setVisible(False)
                    self.svg_widget.setVisible(False)
                    return
                self.svg_widget.setVisible(False)
                self.logo_label.setPixmap(
                    pixmap if width == 0 or height == 0 else pixmap.scaled(
                        width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )
                if width == 0 or height == 0:
                    self.logo_label.resize(pixmap.width(), pixmap.height())
                    self.logo_label.move(
                        (self.width() - pixmap.width()) // 2,
                        (self.height() - pixmap.height()) // 2
                    )
                else:
                    self.logo_label.resize(width, height)
                    self.logo_label.move(
                        (self.width() - width) // 2,
                        (self.height() - height) // 2
                    )
                self.logo_label.setVisible(value)
                self.logo_label.raise_()
                self.print_json("default", self._default)
        except Exception as e:
            self.print_json("error", {"message": f"Error showing logo: {e}"})

    def set_media(self, media_path):
        try:
            # Set the media file
            if not media_path or media_path == "":
                self.print_json("error", {"message": "No media path provided."})
                return
            self.player_data["media_path"] = os.path.normpath(media_path.strip())
            self.player.set_media(self.instance.media_new(self.player_data["media_path"]))
            self.print_json("info", self.player_data)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting media: {e}"})

    def resizeEvent(self, event):
        width = self._default["logo"].get("width", 0)
        height = self._default["logo"].get("height", 0)
        logo_path = self._default["logo"]["path"]
        ext = os.path.splitext(logo_path)[1].lower() if logo_path else ""
        if not logo_path or not os.path.isfile(logo_path):
            self.logo_label.setVisible(False)
            self.svg_widget.setVisible(False)
        else:
            if ext == ".svg":
                if self.svg_widget.isVisible():
                    if width == 0 or height == 0:
                        self.svg_widget.adjustSize()
                        self.svg_widget.move(
                            (self.width() - self.svg_widget.width()) // 2,
                            (self.height() - self.svg_widget.height()) // 2
                        )
                    else:
                        self.svg_widget.resize(width, height)
                        self.svg_widget.move(
                            (self.width() - width) // 2,
                            (self.height() - height) // 2
                        )
            else:
                if self.logo_label.isVisible() and self.logo_label.pixmap():
                    pixmap = self.logo_label.pixmap()
                    if width == 0 or height == 0:
                        self.logo_label.setPixmap(pixmap)
                        self.logo_label.resize(pixmap.width(), pixmap.height())
                        self.logo_label.move(
                            (self.width() - pixmap.width()) // 2,
                            (self.height() - pixmap.height()) // 2
                        )
                    else:
                        self.logo_label.setPixmap(pixmap.scaled(
                            width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        self.logo_label.resize(width, height)
                        self.logo_label.move(
                            (self.width() - width) // 2,
                            (self.height() - height) // 2
                        )
        super().resizeEvent(event)
    
    def closeEvent(self, event):
        self.player.stop()
        if hasattr(self, 'stdin_thread'):
            self.stdin_thread.running = False
        event.accept()
        
    def print_json(self, type, data):
        # Print player data as JSON with type included in the output
        try:
            output = {
                "type": type,
                "data": data
            }
            json_data = json.dumps(output, indent=4)
            print(json_data, flush=True)
        except Exception as e:
            self.print_json("error", {"message": f"Error printing JSON: {e}"})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player()
    player.show()
    sys.exit(app.exec())

