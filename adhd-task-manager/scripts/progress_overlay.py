#!/usr/bin/env python3
"""OpenClaw task progress desktop overlay (MVP).

Features:
- Borderless, always-on-top floating desktop window
- Modern minimal card UI with progress bar
- Fox placeholder (emoji or local image)
- Accepts task updates from repeated CLI calls
- Fireworks animation + praise text on completion (10 seconds)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork

SERVER_NAME_BASE = "openclaw_task_progress_overlay_v1"
DEFAULT_WIDTH = 460
DEFAULT_HEIGHT = 190
STATE_DIR = Path(os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw"))) / "runtime" / "progress-overlay"
STATE_FILE = STATE_DIR / "window-state.json"
SERVER_NAME_FILE = STATE_DIR / "active-server-name.txt"
SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets" / "fox"
DEFAULT_RUN_IMAGE = ASSETS_DIR / "running.png"
DEFAULT_CELEBRATE_IMAGE = ASSETS_DIR / "celebrate.png"


@dataclass
class ProgressState:
    goal: str
    total_steps: int
    current_step: int
    step_text: str = ""
    completed: bool = False
    force_celebrate: bool = False
    praise: str = "太棒了，你把这件事做完了！"
    fox_run_image: str = ""
    fox_celebrate_image: str = ""

    @property
    def clamped_total(self) -> int:
        # Clamp display total to 1..8 for the bar/UI. Never inflate below the declared
        # step count (old min=4 caused e.g. 3-step tasks to show 3/4 forever with no completion).
        t = int(self.total_steps)
        if t < 1:
            t = 1
        return min(8, t)

    @property
    def clamped_current(self) -> int:
        return max(0, min(self.current_step, self.clamped_total))

    @property
    def percent(self) -> int:
        total = self.clamped_total
        if total <= 0:
            return 0
        return int((self.clamped_current / total) * 100)

    @property
    def done(self) -> bool:
        return self.completed or self.clamped_current >= self.clamped_total


class FireworkParticle:
    def __init__(
        self,
        x: float,
        y: float,
        color: QtGui.QColor,
        speed_range: tuple[float, float] = (1.5, 5.5),
        life_range: tuple[int, int] = (36, 62),
        radius_range: tuple[float, float] = (1.5, 3.8),
        gravity: float = 0.06,
    ) -> None:
        angle = random.uniform(0, math.tau)
        speed = random.uniform(speed_range[0], speed_range[1])
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(life_range[0], life_range[1])
        self.max_life = self.life
        self.radius = random.uniform(radius_range[0], radius_range[1])
        self.color = color
        self.gravity = gravity

    def step(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.99
        self.life -= 1
        return self.life > 0


class ScreenFireworksOverlay(QtWidgets.QWidget):
    def __init__(self, screen: QtGui.QScreen, duration_sec: float = 10.0) -> None:
        super().__init__(None)
        self._screen = screen
        self._end_ts = time.time() + duration_sec
        self._particles: list[FireworkParticle] = []

        flags = (
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setGeometry(self._screen.geometry())

        for _ in range(7):
            self._spawn_burst()

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self.raise_()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)

        for p in self._particles:
            alpha = max(20, int(255 * (p.life / p.max_life)))
            color = QtGui.QColor(p.color)
            color.setAlpha(alpha)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QtCore.QPointF(p.x, p.y), p.radius, p.radius)

    def _tick(self) -> None:
        alive: list[FireworkParticle] = []
        for p in self._particles:
            if p.step():
                alive.append(p)
        self._particles = alive

        if time.time() < self._end_ts:
            if random.random() < 0.42:
                self._spawn_burst()
        else:
            self._timer.stop()
            self.close()
            return

        self.update()

    def _spawn_burst(self) -> None:
        x = random.uniform(60, max(61, self.width() - 60))
        y = random.uniform(40, max(41, int(self.height() * 0.72)))
        palette = [
            QtGui.QColor("#ff1744"),
            QtGui.QColor("#ff3d00"),
            QtGui.QColor("#ff9100"),
            QtGui.QColor("#ffea00"),
            QtGui.QColor("#76ff03"),
            QtGui.QColor("#00e676"),
            QtGui.QColor("#00e5ff"),
            QtGui.QColor("#00b0ff"),
            QtGui.QColor("#3d5afe"),
            QtGui.QColor("#651fff"),
            QtGui.QColor("#d500f9"),
            QtGui.QColor("#f50057"),
        ]

        for _ in range(random.randint(75, 120)):
            self._particles.append(
                FireworkParticle(
                    x,
                    y,
                    random.choice(palette),
                    speed_range=(2.5, 9.5),
                    life_range=(44, 88),
                    radius_range=(2.0, 5.6),
                    gravity=0.075,
                )
            )


class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, state: ProgressState, initial_geometry: QtCore.QRect | None = None) -> None:
        super().__init__()
        self.state = state
        self.always_on_top = True
        self.drag_position = QtCore.QPoint()
        self._active_celebrations: list[ScreenFireworksOverlay] = []
        self._last_celebrate_ts = 0.0

        self._build_window()
        self._build_ui()
        if initial_geometry:
            self.setGeometry(initial_geometry)
        self.apply_state(self.state)

    def _build_window(self) -> None:
        self._apply_window_flags()
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        screen = QtGui.QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def _apply_window_flags(self) -> None:
        flags = QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool
        if self.always_on_top:
            flags |= QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _build_ui(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QtWidgets.QFrame()
        self.card.setObjectName("card")
        outer.addWidget(self.card)

        layout = QtWidgets.QVBoxLayout(self.card)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(10)

        self.fox_holder = QtWidgets.QLabel("🦊")
        self.fox_holder.setAlignment(QtCore.Qt.AlignCenter)
        self.fox_holder.setFixedSize(92, 92)
        self.fox_holder.setObjectName("fox")
        top.addWidget(self.fox_holder)

        right = QtWidgets.QVBoxLayout()
        right.setSpacing(4)

        self.goal_label = QtWidgets.QLabel("目标")
        self.goal_label.setObjectName("goal")
        self.goal_label.setWordWrap(True)
        right.addWidget(self.goal_label)

        self.step_label = QtWidgets.QLabel("第 0/4 步")
        self.step_label.setObjectName("step")
        right.addWidget(self.step_label)

        top.addLayout(right, 1)
        layout.addLayout(top)

        self.progress_bg = QtWidgets.QFrame()
        self.progress_bg.setObjectName("progressBg")
        self.progress_bg.setFixedHeight(10)
        pb_layout = QtWidgets.QHBoxLayout(self.progress_bg)
        pb_layout.setContentsMargins(1, 1, 1, 1)

        self.progress_fill = QtWidgets.QFrame()
        self.progress_fill.setObjectName("progressFill")
        self.progress_fill.setFixedWidth(0)
        pb_layout.addWidget(self.progress_fill)
        pb_layout.addStretch(1)
        layout.addWidget(self.progress_bg)

        self.status_label = QtWidgets.QLabel("正在推进中")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        self.setStyleSheet(
            """
            QWidget { font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; color: #1f2937; }
            #card {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                            stop:0 rgba(255,255,255,245),
                            stop:1 rgba(246,248,252,240));
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,210);
            }
            #fox {
                background: transparent;
                border: none;
                font-size: 52px;
            }
            #goal { font-size: 14px; font-weight: 600; }
            #step { font-size: 12px; color: #4b5563; }
            #status { font-size: 12px; color: #9a3412; }
            #progressBg {
                background: rgba(229,231,235,190);
                border: 1px solid rgba(209,213,219,180);
                border-radius: 6px;
            }
            #progressFill {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #fb923c,
                            stop:1 #f97316);
                border-radius: 5px;
            }
            """
        )

    def _toggle_topmost(self) -> None:
        self.always_on_top = not self.always_on_top
        geo = self.geometry()
        self._apply_window_flags()
        self.show()
        self.setGeometry(geo)
        self.raise_()
        self.activateWindow()
        persist_geometry(self.geometry())

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu(self)
        top_label = "取消置顶" if self.always_on_top else "置顶"
        top_action = menu.addAction(top_label)
        min_action = menu.addAction("最小化")
        close_action = menu.addAction("关闭")

        picked = menu.exec(event.globalPos())
        if picked == top_action:
            self._toggle_topmost()
        elif picked == min_action:
            self.showMinimized()
        elif picked == close_action:
            self.close()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            persist_geometry(self.geometry())
        super().mouseReleaseEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        persist_geometry(self.geometry())
        super().closeEvent(event)

    def _set_fox(self, fox_image: str) -> None:
        path = Path(fox_image).expanduser() if fox_image else None
        if path and path.exists() and path.is_file():
            pixmap = QtGui.QPixmap(str(path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.fox_holder.size(),
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
                self.fox_holder.setPixmap(scaled)
                self.fox_holder.setText("")
                return
        self.fox_holder.setPixmap(QtGui.QPixmap())
        self.fox_holder.setText("🦊")

    def _animate_progress(self, percent: int) -> None:
        width = max(0, int((self.progress_bg.width() - 2) * (percent / 100.0)))
        self.progress_fill.setMaximumWidth(self.progress_bg.width() - 2)

        anim = QtCore.QPropertyAnimation(self.progress_fill, b"minimumWidth", self)
        anim.setDuration(420)
        anim.setStartValue(self.progress_fill.width())
        anim.setEndValue(width)
        anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def apply_state(self, state: ProgressState) -> None:
        self.state = state

        total = state.clamped_total
        current = state.clamped_current
        percent = state.percent
        done_or_force = state.done or state.force_celebrate

        self.goal_label.setText(state.goal.strip() or "未设置目标")
        self.step_label.setText(f"第 {current}/{total} 步")
        self._animate_progress(percent)
        fox_image = state.fox_celebrate_image if done_or_force else state.fox_run_image
        self._set_fox(fox_image)

        if done_or_force:
            self.status_label.setText(state.praise.strip() or "完成了，真的很棒。")
            # Ensure celebration is visible even if window was minimized.
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self._start_fireworks_for_10s()
        elif current <= 0:
            if state.step_text:
                self.status_label.setText(f"准备开始：{state.step_text}")
            else:
                self.status_label.setText("准备开始，先做第一步")
        else:
            if state.step_text:
                self.status_label.setText(f"正在推进第 {current} 步：{state.step_text}")
            else:
                self.status_label.setText(f"正在推进第 {current} 步")

    def _start_fireworks_for_10s(self) -> None:
        now = time.time()
        if now - self._last_celebrate_ts < 1.2:
            return
        self._last_celebrate_ts = now

        screen = self.screen() or QtGui.QGuiApplication.primaryScreen()
        if not screen:
            return
        overlay = ScreenFireworksOverlay(screen, duration_sec=10.0)
        overlay.destroyed.connect(lambda *_: self._remove_celebration_overlay(overlay))
        self._active_celebrations.append(overlay)
        overlay.show()

    def _remove_celebration_overlay(self, overlay: ScreenFireworksOverlay) -> None:
        try:
            self._active_celebrations.remove(overlay)
        except ValueError:
            pass


class OverlayServer(QtCore.QObject):
    def __init__(self, window: OverlayWindow, server_name: str) -> None:
        super().__init__()
        self.window = window
        self.server = QtNetwork.QLocalServer(self)
        self._socket_buffers: dict[int, bytearray] = {}

        QtNetwork.QLocalServer.removeServer(server_name)
        if not self.server.listen(server_name):
            raise RuntimeError(f"Could not listen on local server: {server_name}")

        self.server.newConnection.connect(self._on_new_connection)

    def _on_new_connection(self) -> None:
        sock = self.server.nextPendingConnection()
        if sock is None:
            return
        self._socket_buffers[id(sock)] = bytearray()
        sock.readyRead.connect(lambda s=sock: self._read_socket(s))
        sock.disconnected.connect(lambda s=sock: self._on_disconnected(s))
        sock.disconnected.connect(sock.deleteLater)

    def _on_disconnected(self, sock: QtNetwork.QLocalSocket) -> None:
        self._socket_buffers.pop(id(sock), None)

    def _read_socket(self, sock: QtNetwork.QLocalSocket) -> None:
        sid = id(sock)
        self._socket_buffers.setdefault(sid, bytearray()).extend(bytes(sock.readAll()))
        raw = self._socket_buffers[sid].decode("utf-8", errors="replace").strip()
        if not raw:
            return
        try:
            payload = json.loads(raw)
            self._socket_buffers[sid].clear()
            if payload.get("action") == "close":
                QtWidgets.QApplication.quit()
                return
            if payload.get("action") == "replace":
                geo = self.window.geometry()
                persist_geometry(geo)
                response = {
                    "x": int(geo.x()),
                    "y": int(geo.y()),
                    "w": int(geo.width()),
                    "h": int(geo.height()),
                }
                sock.write(json.dumps(response).encode("utf-8"))
                sock.flush()
                sock.waitForBytesWritten(120)
                QtCore.QTimer.singleShot(40, QtWidgets.QApplication.quit)
                return
            state = parse_state_from_payload(payload)
            self.window.apply_state(state)
            # Ack so caller knows a real visible server accepted the update.
            sock.write(json.dumps({"ok": True}).encode("utf-8"))
            sock.flush()
            sock.waitForBytesWritten(120)
        except json.JSONDecodeError:
            return
        except Exception:
            pass


def parse_state_from_payload(payload: dict) -> ProgressState:
    run_img = str(payload.get("fox_run_image", "")).strip()
    celebrate_img = str(payload.get("fox_celebrate_image", "")).strip()
    legacy_img = str(payload.get("fox_image", "")).strip()
    if legacy_img and not run_img:
        run_img = legacy_img
    if not run_img:
        run_img = str(DEFAULT_RUN_IMAGE)
    if not celebrate_img:
        celebrate_img = str(DEFAULT_CELEBRATE_IMAGE)

    status = str(payload.get("status", "")).strip().lower()
    completed_by_status = status in {"done", "completed", "complete", "finished", "success"}

    return ProgressState(
        goal=str(payload.get("goal", "")).strip(),
        total_steps=int(payload.get("total_steps", 4)),
        current_step=int(payload.get("current_step", 0)),
        step_text=str(payload.get("step_text", "")).strip(),
        completed=bool(payload.get("completed", False)) or completed_by_status,
        force_celebrate=bool(payload.get("force_celebrate", False)),
        praise=str(payload.get("praise", "太棒了，你把这件事做完了！")),
        fox_run_image=run_img,
        fox_celebrate_image=celebrate_img,
    )


def send_update_to_running_instance(server_name: str, payload: dict, require_ack: bool = False) -> bool:
    socket = QtNetwork.QLocalSocket()
    socket.connectToServer(server_name)
    if not socket.waitForConnected(250):
        return False

    socket.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    socket.flush()
    if not socket.waitForBytesWritten(250):
        socket.disconnectFromServer()
        return False
    # Prefer ack from server; for normal progress updates, no-ack can be treated as
    # legacy-server success. For celebration-critical updates, caller can require ack.
    if not socket.waitForReadyRead(260):
        socket.disconnectFromServer()
        return not require_ack
    raw = bytes(socket.readAll()).decode("utf-8", errors="replace").strip()
    if not raw:
        socket.disconnectFromServer()
        return not require_ack
    try:
        ack = json.loads(raw)
        ok = bool(ack.get("ok", False))
    except Exception:
        ok = not require_ack
    socket.disconnectFromServer()
    return ok


def request_replace_from_running_instance(server_name: str) -> QtCore.QRect | None:
    socket = QtNetwork.QLocalSocket()
    socket.connectToServer(server_name)
    if not socket.waitForConnected(200):
        return None

    socket.write(json.dumps({"action": "replace"}).encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(120)

    if not socket.waitForReadyRead(240):
        socket.disconnectFromServer()
        return None

    raw = bytes(socket.readAll()).decode("utf-8", errors="replace").strip()
    socket.disconnectFromServer()
    if not raw:
        return None
    try:
        data = json.loads(raw)
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        w = int(data.get("w", DEFAULT_WIDTH))
        h = int(data.get("h", DEFAULT_HEIGHT))
        return QtCore.QRect(x, y, max(240, w), max(120, h))
    except Exception:
        return None


def load_persisted_geometry() -> QtCore.QRect | None:
    try:
        if not STATE_FILE.exists():
            return None
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        w = int(data.get("w", DEFAULT_WIDTH))
        h = int(data.get("h", DEFAULT_HEIGHT))
        return QtCore.QRect(x, y, max(240, w), max(120, h))
    except Exception:
        return None


def persist_geometry(geo: QtCore.QRect) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "x": int(geo.x()),
            "y": int(geo.y()),
            "w": int(geo.width()),
            "h": int(geo.height()),
            "ts": time.time(),
        }
        STATE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def read_active_server_name() -> str:
    try:
        if SERVER_NAME_FILE.exists():
            name = SERVER_NAME_FILE.read_text(encoding="utf-8").strip()
            if name:
                return name
    except Exception:
        pass
    return SERVER_NAME_BASE


def write_active_server_name(name: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        SERVER_NAME_FILE.write_text(name, encoding="utf-8")
    except Exception:
        pass


def server_name_candidates() -> list[str]:
    active = read_active_server_name()
    out: list[str] = []
    for n in (active, SERVER_NAME_BASE):
        if n and n not in out:
            out.append(n)
    return out


def create_overlay_server_with_fallback(window: OverlayWindow, preferred_name: str) -> tuple[OverlayServer, str]:
    # 1) try preferred name first
    try:
        srv = OverlayServer(window, preferred_name)
        write_active_server_name(preferred_name)
        return srv, preferred_name
    except RuntimeError:
        pass

    # 2) try base name
    if preferred_name != SERVER_NAME_BASE:
        try:
            srv = OverlayServer(window, SERVER_NAME_BASE)
            write_active_server_name(SERVER_NAME_BASE)
            return srv, SERVER_NAME_BASE
        except RuntimeError:
            pass

    # 3) dynamic fallback to avoid hard failure when stale named pipe/socket blocks
    dynamic_name = f"{SERVER_NAME_BASE}_{os.getpid()}_{int(time.time() * 1000)}"
    srv = OverlayServer(window, dynamic_name)
    write_active_server_name(dynamic_name)
    return srv, dynamic_name


def build_payload(args: argparse.Namespace) -> dict:
    return {
        "goal": args.goal,
        "total_steps": args.total_steps,
        "current_step": args.current_step,
        "step_text": args.step_text,
        "completed": args.completed,
        "force_celebrate": args.force_celebrate,
        "status": args.status,
        "praise": args.praise,
        "fox_image": args.fox_image,
        "fox_run_image": args.fox_run_image,
        "fox_celebrate_image": args.fox_celebrate_image,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw desktop progress overlay")
    parser.add_argument("--goal", default="", help="整个任务目标")
    parser.add_argument("--total-steps", type=int, default=4, help="总步数(建议 4-8)")
    parser.add_argument("--current-step", type=int, default=0, help="当前进行到第几步")
    parser.add_argument("--step-text", default="", help="当前这一步正在做什么")
    parser.add_argument("--completed", action="store_true", help="标记任务已完成，触发烟花")
    parser.add_argument("--force-celebrate", action="store_true", help="强制触发烟花庆祝（兜底）")
    parser.add_argument("--status", default="", help="可选状态：running/completed/done")
    parser.add_argument("--praise", default="完成啦！你真的很厉害。", help="完成后的夸夸文案")
    parser.add_argument("--fox-image", default="", help="兼容参数：进行中小狐狸图片路径(可选)")
    parser.add_argument(
        "--fox-run-image",
        default=str(DEFAULT_RUN_IMAGE),
        help="进行中小狐狸图片路径(默认使用 skill 内置 running.png)",
    )
    parser.add_argument(
        "--fox-celebrate-image",
        default=str(DEFAULT_CELEBRATE_IMAGE),
        help="完成小狐狸图片路径(默认使用 skill 内置 celebrate.png)",
    )
    parser.add_argument(
        "--close",
        action="store_true",
        help="关闭已运行的悬浮窗实例",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    payload = build_payload(args)

    if args.close:
        payload = {"action": "close"}
    elif not args.goal.strip():
        parser.error("--goal is required unless --close is used")

    if args.close:
        for name in server_name_candidates():
            send_update_to_running_instance(name, payload, require_ack=False)
        return 0

    # Unified strategy for every update:
    # 1) hand off geometry from old instance if possible
    # 2) proactively close/cleanup old instances
    # 3) start a fresh instance for this step/state
    handoff_geometry = None
    chosen_name = server_name_candidates()[0]
    for name in server_name_candidates():
        handoff_geometry = request_replace_from_running_instance(name)
        if handoff_geometry is not None:
            chosen_name = name
            time.sleep(0.08)
            break

    close_payload = {"action": "close"}
    for name in server_name_candidates():
        send_update_to_running_instance(name, close_payload, require_ack=False)
        QtNetwork.QLocalServer.removeServer(name)
    QtNetwork.QLocalServer.removeServer(SERVER_NAME_BASE)
    time.sleep(0.12)

    state = parse_state_from_payload(payload)
    win = OverlayWindow(state, initial_geometry=handoff_geometry or load_persisted_geometry())

    server, active_name = create_overlay_server_with_fallback(win, chosen_name)
    _ = active_name

    win.show()
    win.raise_()
    win.activateWindow()

    # Keep reference alive
    _ = server
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
