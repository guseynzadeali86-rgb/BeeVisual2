"""BeeVisual launcher - GUI (PySide6).  Run:  python main.py"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QThread, QTimer, QUrl, QVariantAnimation, Signal
from PySide6.QtGui import (QBrush, QColor, QDesktopServices, QFont, QFontDatabase, QFontMetrics, QIcon,
                           QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox, QFrame, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPushButton, QStackedWidget, QWidget)

import core

ASSETS = core.bundle_dir() / "assets"
A1, A2 = QColor(255, 200, 30), QColor(255, 138, 0)
CREAM, INK, GRAY = QColor(255, 244, 214), QColor(25, 16, 6), QColor(170, 160, 140)
W, H, SIDE = 1280, 720, 260
RAM_OPTIONS = [2, 3, 4, 6, 8, 12, 16]
FONT_FAMILY = "Inter"


# ------------------------------------------------------------------ helpers
def font(px: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    f = QFont(FONT_FAMILY)
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


def tinted(name: str, color: QColor, size: int) -> QPixmap:
    src = QPixmap(str(ASSETS / "icons" / f"{name}.png")).scaled(
        size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    out = QPixmap(src.size())
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.drawPixmap(0, 0, src)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(out.rect(), color)
    p.end()
    return out


def cover(pix: QPixmap, w: int, h: int) -> QPixmap:
    s = pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    return s.copy((s.width() - w) // 2, (s.height() - h) // 2, w, h)


def amber_gradient(x0: float, x1: float, a: int = 255) -> QLinearGradient:
    g = QLinearGradient(x0, 0, x1, 0)
    c1, c2 = QColor(A1), QColor(A2)
    c1.setAlpha(a)
    c2.setAlpha(a)
    g.setColorAt(0, c1)
    g.setColorAt(1, c2)
    return g


def load_quotes() -> list[str]:
    try:
        q = json.loads((ASSETS / "quotes" / "quotes.json").read_text(encoding="utf-8"))
        return [str(x) for x in q] or ["Победи весь мир с BeeVisual"]
    except (OSError, ValueError):
        return ["Победи весь мир с BeeVisual"]


def split_lines(words: list[str], fm: QFontMetrics, max_w: int) -> list[list[str]]:
    """One line if it fits, otherwise the most balanced 2-line split."""
    space = fm.horizontalAdvance(" ")
    width = lambda ws: sum(fm.horizontalAdvance(w) for w in ws) + space * max(0, len(ws) - 1)
    if width(words) <= max_w or len(words) < 2:
        return [words]
    best = min(range(1, len(words)), key=lambda i: max(width(words[:i]), width(words[i:])))
    return [words[:best], words[best:]]


# ------------------------------------------------------------------ worker
class LaunchWorker(QThread):
    status = Signal(str)
    progress = Signal(int, int)
    started_game = Signal(object, str)
    failed = Signal(str)

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = dict(cfg)
        self._value, self._max = 0, 0

    def _set_progress(self, v):
        self._value = int(v)
        self.progress.emit(self._value, self._max)

    def _set_max(self, m):
        self._max = int(m)
        self.progress.emit(self._value, self._max)

    def run(self):
        try:
            cb = {"setStatus": lambda t: self.status.emit(str(t)),
                  "setProgress": self._set_progress,
                  "setMax": self._set_max}
            self.status.emit("Подготовка…")
            command, cwd = core.prepare_launch(self.cfg, cb, lambda m: self.status.emit(m))
            self.status.emit("Запускаю Minecraft…")
            proc, log_path = core.start_game(command, cwd)
            self.started_game.emit(proc, log_path)
        except Exception as e:  # shown to the user
            self.failed.emit(f"{type(e).__name__}: {e}")


# ------------------------------------------------------------------ widgets
class NavButton(QPushButton):
    def __init__(self, parent, icon_name: str, text: str):
        super().__init__(parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFixedSize(228, 46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label = text
        self.icon_on = tinted(icon_name, INK, 22)
        c = QColor(CREAM)
        c.setAlpha(160)
        self.icon_off = tinted(icon_name, c, 22)
        self._hover = False

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.width(), self.height())
        if self.isChecked():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(amber_gradient(0, self.width())))
            p.drawRoundedRect(r, 12, 12)
            p.drawPixmap(18, 12, self.icon_on)
            p.setPen(INK)
            p.setFont(font(15, QFont.Weight.Bold))
        else:
            if self._hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 255, 255, 14))
                p.drawRoundedRect(r, 12, 12)
            p.drawPixmap(18, 12, self.icon_off)
            c = QColor(CREAM)
            c.setAlpha(190 if self._hover else 165)
            p.setPen(c)
            p.setFont(font(15, QFont.Weight.DemiBold))
        p.drawText(QRectF(52, 0, 170, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.label)


class RoundButton(QAbstractButton):
    def __init__(self, parent, color: QColor):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self.color)
        c.setAlpha(255 if self._hover else 215)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawEllipse(QRectF(0, 0, 14, 14))


class LaunchButton(QAbstractButton):
    PAD, BW, BH = 40, 380, 84

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(self.BW + 2 * self.PAD, self.BH + 2 * self.PAD)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.pix = {k: QPixmap(str(ASSETS / "launcher" / f"button_launch_{k}.png")) for k in ("normal", "hover", "pressed")}
        self.icon_pm = tinted("play", INK, 24)
        self.label = "ЗАПУСТИТЬ"
        self._hover = False

    def hitButton(self, pos):
        return QRectF(self.PAD, self.PAD, self.BW, self.BH).contains(QPointF(pos))

    def mouseMoveEvent(self, e):
        h = self.hitButton(e.position().toPoint())
        if h != self._hover:
            self._hover = h
            self.update()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        enabled = self.isEnabled()
        key = "pressed" if (self.isDown() and enabled) else "hover" if (self._hover and enabled) else "normal"
        p.setOpacity(1.0 if enabled else 0.55)
        p.drawPixmap(0, 0, self.pix[key])
        dy = 3 if key == "pressed" else 0
        f = font(28, QFont.Weight.ExtraBold)
        fm = QFontMetrics(f)
        tw = fm.horizontalAdvance(self.label)
        gx = self.PAD + self.BW / 2 - (tw + 38) / 2
        cy = self.PAD + self.BH / 2 + dy
        p.drawPixmap(int(gx), int(cy - 12), self.icon_pm)
        p.setFont(f)
        p.setPen(INK)
        p.drawText(QPointF(gx + 38, cy + (fm.ascent() - fm.descent()) / 2), self.label)


class Chip(QFrame):
    def __init__(self, parent, caption: str, w: int, caret: bool = False):
        super().__init__(parent)
        self.setFixedSize(w, 52)
        self.caption, self.caret = caption, caret

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(255, 255, 255, 24), 1))
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawRoundedRect(r, 12, 12)
        p.setPen(GRAY)
        f = font(10, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
        p.setFont(f)
        p.drawText(QPointF(16, 20), self.caption)
        if self.caret:
            x, y = self.width() - 26, 24
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(A1)
            p.drawPolygon(QPolygonF([QPointF(x, y), QPointF(x + 9, y), QPointF(x + 4.5, y + 5)]))


CHIP_EDIT_QSS = f"""
QLineEdit, QComboBox {{ background: transparent; border: none; color: rgb(255,244,214);
    font-family: '{FONT_FAMILY}'; font-size: 15px; font-weight: 600; padding: 0 0 0 0; selection-background-color: rgb(255,170,20); selection-color: black; }}
QComboBox::drop-down {{ border: none; width: 0px; }}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{ background: rgb(22,20,15); color: rgb(255,244,214); border: 1px solid rgba(255,190,40,60);
    selection-background-color: rgb(255,170,20); selection-color: black; outline: 0; }}
"""


class HeroPage(QWidget):
    """Big quote, subtitle, launch button, status and the version / nick / RAM chips."""

    def __init__(self, parent, cfg: dict):
        super().__init__(parent)
        self.quotes = load_quotes()
        random.shuffle(self.quotes)
        self.qi = 0
        self.q_opacity = 1.0
        self.status_text, self.running = "", False
        self.prog = (0, 0)
        self.error = False
        self.lines: list[list[str]] = []
        self._layout_quote()

        self.btn = LaunchButton(self)
        self.btn.move(59 - LaunchButton.PAD, 480 - LaunchButton.PAD)

        Chip(self, "ВЕРСИЯ", 232).move(59, 612)
        ver = QLabel(f"Minecraft {core.MC_VERSION}  •  Fabric", self)
        ver.setStyleSheet(f"color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:15px; font-weight:600; background:transparent;")
        ver.setGeometry(75, 630, 210, 24)

        nick_chip = Chip(self, "НИКНЕЙМ", 188)
        nick_chip.move(305, 612)
        self.nick = QLineEdit(cfg["nickname"], nick_chip)
        self.nick.setMaxLength(16)
        self.nick.setStyleSheet(CHIP_EDIT_QSS)
        self.nick.setGeometry(16, 24, 160, 24)

        ram_chip = Chip(self, "ОЗУ", 120, caret=True)
        ram_chip.move(507, 612)
        self.ram = QComboBox(ram_chip)
        for g in RAM_OPTIONS:
            self.ram.addItem(f"{g} ГБ", g)
        idx = self.ram.findData(int(cfg["ram_gb"]))
        self.ram.setCurrentIndex(idx if idx >= 0 else RAM_OPTIONS.index(4))
        self.ram.setStyleSheet(CHIP_EDIT_QSS)
        self.ram.setGeometry(16, 24, 90, 24)

        self.fade = QVariantAnimation(self)
        self.fade.setDuration(260)
        self.fade.valueChanged.connect(self._on_fade)
        self.fade.finished.connect(self._fade_done)
        self._fading_out = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_quote)
        self.timer.start(7000)

    # --- quotes
    def _layout_quote(self):
        self.qfont = font(66, QFont.Weight.Black)
        fm = QFontMetrics(self.qfont)
        self.lines = split_lines(self.quotes[self.qi].split(), fm, 900)

    def next_quote(self):
        if self.fade.state() == QVariantAnimation.State.Running:
            return
        self._fading_out = True
        self.fade.setStartValue(1.0)
        self.fade.setEndValue(0.0)
        self.fade.start()

    def _on_fade(self, v):
        self.q_opacity = float(v)
        self.update()

    def _fade_done(self):
        if self._fading_out:
            self._fading_out = False
            self.qi = (self.qi + 1) % len(self.quotes)
            self._layout_quote()
            self.fade.setStartValue(0.0)
            self.fade.setEndValue(1.0)
            self.fade.start()

    # --- state
    def set_running(self, running: bool):
        self.running = running
        self.btn.label = "ЗАПУСК…" if running else "ЗАПУСТИТЬ"
        self.btn.setEnabled(not running)
        self.nick.setEnabled(not running)
        self.ram.setEnabled(not running)
        self.update()

    def set_status(self, text: str, error: bool = False):
        self.status_text, self.error = text, error
        self.update()

    def set_progress(self, v: int, m: int):
        self.prog = (v, m)
        self.update()

    # --- painting
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        fm = QFontMetrics(self.qfont)
        space = fm.horizontalAdvance(" ")
        p.setOpacity(self.q_opacity)
        n = len(self.lines)
        for i, words in enumerate(self.lines):
            cy = 378 - 80 * (n - 1 - i)
            base = cy + (fm.ascent() - fm.descent()) / 2
            x = 59.0
            for w in words:
                if w == "BeeVisual":
                    path = QPainterPath()
                    path.addText(x, base, self.qfont, w)
                    br = path.boundingRect()
                    g = QLinearGradient(br.left(), 0, br.right(), 0)
                    g.setColorAt(0, A1)
                    g.setColorAt(1, A2)
                    p.fillPath(path, QBrush(g))
                else:
                    p.setFont(self.qfont)
                    p.setPen(CREAM)
                    p.drawText(QPointF(x, base), w)
                x += fm.horizontalAdvance(w) + space
        p.setOpacity(1.0)
        p.setFont(font(20, QFont.Weight.Medium))
        sub = QColor(CREAM)
        sub.setAlpha(190)
        p.setPen(sub)
        p.drawText(QPointF(61, 447), "Чистая картинка. Лучший визуал. Сладкая победа.")
        # status + progress to the right of the button
        if self.status_text:
            c = QColor(255, 120, 100) if self.error else QColor(CREAM)
            p.setPen(c)
            p.setFont(font(15, QFont.Weight.DemiBold))
            text = QFontMetrics(p.font()).elidedText(self.status_text, Qt.TextElideMode.ElideRight, 500)
            p.drawText(QPointF(470, 518), text)
        if self.running:
            v, m = self.prog
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 30))
            p.drawRoundedRect(QRectF(470, 532, 420, 8), 4, 4)
            if m > 0:
                w = max(8.0, 420 * min(1.0, v / m))
                p.setBrush(QBrush(amber_gradient(470, 890)))
                p.drawRoundedRect(QRectF(470, 532, w, 8), 4, 4)
        # quote dots
        total = len(self.quotes)
        x = 1019 - 40 - 22 * total
        for i in range(total):
            active = i == self.qi
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(A1 if active else QColor(255, 255, 255, 70))
            wdt = 28 if active else 8
            p.drawRoundedRect(QRectF(x, 686, wdt, 8), 4, 4)
            x += wdt + 10


CARD_QSS = ("background: rgba(255,255,255,16); border: 1px solid rgba(255,190,40,40); border-radius: 14px;")


def make_text_card(parent, y: int, title: str, body: str, icon: str | None = None) -> QFrame:
    card = QFrame(parent)
    card.setGeometry(59, y, 860, 96)
    card.setStyleSheet(f"QFrame {{ {CARD_QSS} }}")
    x = 24
    if icon:
        ic = QLabel(card)
        ic.setPixmap(tinted(icon, A1, 34))
        ic.setGeometry(24, 30, 34, 34)
        ic.setStyleSheet("background: transparent; border: none;")
        x = 76
    t = QLabel(title, card)
    t.setGeometry(x, 16, 760, 28)
    t.setStyleSheet(f"color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:18px; font-weight:800; background:transparent; border:none;")
    b = QLabel(body, card)
    b.setGeometry(x, 46, 780, 40)
    b.setWordWrap(True)
    b.setStyleSheet(f"color: rgba(255,244,214,170); font-family:'{FONT_FAMILY}'; font-size:14px; background:transparent; border:none;")
    return card


def page_title(parent, text: str):
    t = QLabel(text, parent)
    t.setGeometry(59, 60, 700, 50)
    t.setStyleSheet(f"color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:40px; font-weight:900; background:transparent;")


class NewsPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        page_title(self, "Новости")
        make_text_card(self, 140, "Добро пожаловать в BeeVisual", "Нажми «Играть» → «Запустить»: лаунчер сам скачает Minecraft 1.21.4, Fabric и запустит игру с клиентом.", "news")
        make_text_card(self, 256, "Меню модулей — Right Shift", "В игре нажми правый Shift, чтобы открыть ClickGUI: NoRender, FullBright, ViewModel, Swing Animation и другие.", "cat_render")
        make_text_card(self, 372, "Жужжим дальше", "Новые модули и анимации будут появляться с обновлениями. Следи за новостями здесь.", "particles")


MODULES = [
    ("norender", "NoRender", "Убирает огонь на экране, тряску камеры и лишние эффекты."),
    ("fullbright", "FullBright", "Яркая картинка даже в темноте."),
    ("viewmodel", "ViewModel", "Положение и размер предмета в руке."),
    ("swinganimation", "Swing Animation", "Свои анимации взмаха и скорость."),
    ("ambience", "Ambience", "Время суток и погода только у тебя на экране."),
    ("zoom", "Zoom", "Приближение по клавише."),
]


class VisualsPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        page_title(self, "Визуалы")
        for i, (ic, name, desc) in enumerate(MODULES):
            make_text_card(self, 130 + i * 86, name, desc, ic).setFixedHeight(78)


class TaskWorker(QThread):
    """Runs any function in the background; reports result or error."""
    done = Signal(object)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.done.emit(self.fn(lambda m: self.log.emit(m)))
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


LIST_QSS = f"""
QListWidget {{ background: rgba(255,255,255,14); border: 1px solid rgba(255,190,40,40); border-radius: 12px;
    color: rgb(255,244,214); font-family: '{FONT_FAMILY}'; font-size: 13px; outline: 0; padding: 4px; }}
QListWidget::item {{ padding: 8px; border-radius: 8px; }}
QListWidget::item:selected {{ background: rgba(255,190,30,70); color: rgb(255,244,214); }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: rgba(255,190,40,90); border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
BTN_QSS = (f"QPushButton {{ color: rgb(25,16,6); font-family:'{FONT_FAMILY}'; font-size:13px; font-weight:800; "
           "background: rgb(255,190,30); border:none; border-radius:10px; } "
           "QPushButton:hover { background: rgb(255,210,70); } QPushButton:disabled { background: rgba(255,190,30,90); }")
BTN2_QSS = (f"QPushButton {{ color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:13px; font-weight:700; "
            "background: rgba(255,255,255,20); border:1px solid rgba(255,190,40,70); border-radius:10px; } "
            "QPushButton:hover { background: rgba(255,200,30,40); } QPushButton:disabled { color: rgba(255,244,214,90); }")
EDIT_QSS = (f"QLineEdit, QComboBox {{ color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:14px; "
            "background: rgba(255,255,255,16); border:1px solid rgba(255,255,255,24); border-radius:10px; padding-left:12px; } "
            "QLineEdit:focus { border-color: rgba(255,200,30,150); } "
            "QComboBox QAbstractItemView { background: rgb(22,20,15); color: rgb(255,244,214); selection-background-color: rgb(255,170,20); selection-color: black; }")
KIND_NAMES = [("Моды", "mod"), ("Ресурспаки", "resourcepack"), ("Шейдеры", "shader")]


class DownloadsPage(QWidget):
    """Search Modrinth and install mods / resource packs / shaders straight into the game."""

    def __init__(self, parent):
        super().__init__(parent)
        page_title(self, "Загрузки")
        self.hits: list[dict] = []
        self.worker: TaskWorker | None = None

        self.query = QLineEdit(self)
        self.query.setPlaceholderText("Поиск на Modrinth (пусто = самое популярное)")
        self.query.setGeometry(59, 124, 400, 34)
        self.query.setStyleSheet(EDIT_QSS)
        self.query.returnPressed.connect(self.search)
        self.kind = QComboBox(self)
        for name, key in KIND_NAMES:
            self.kind.addItem(name, key)
        self.kind.setGeometry(470, 124, 140, 34)
        self.kind.setStyleSheet(EDIT_QSS)
        self.kind.currentIndexChanged.connect(lambda _i: (self.search(), self.refresh_installed()))
        self.go = QPushButton("Найти", self)
        self.go.setGeometry(620, 124, 100, 34)
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.setStyleSheet(BTN_QSS)
        self.go.clicked.connect(self.search)

        cap = lambda t, x, y: self._cap(t, x, y)
        cap("НАЙДЕНО (для Minecraft 1.21.4)", 59, 170)
        self.results = QListWidget(self)
        self.results.setGeometry(59, 192, 520, 380)
        self.results.setStyleSheet(LIST_QSS)
        self.results.itemDoubleClicked.connect(lambda _i: self.install())
        cap("УСТАНОВЛЕНО", 600, 170)
        self.installed = QListWidget(self)
        self.installed.setGeometry(600, 192, 320, 380)
        self.installed.setStyleSheet(LIST_QSS)

        self.install_btn = QPushButton("Установить выбранное", self)
        self.install_btn.setGeometry(59, 586, 240, 38)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setStyleSheet(BTN_QSS)
        self.install_btn.clicked.connect(self.install)
        self.remove_btn = QPushButton("Удалить выбранное", self)
        self.remove_btn.setGeometry(600, 586, 190, 38)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setStyleSheet(BTN2_QSS)
        self.remove_btn.clicked.connect(self.remove)
        self.folder_btn = QPushButton("Папка", self)
        self.folder_btn.setGeometry(800, 586, 120, 38)
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.setStyleSheet(BTN2_QSS)
        self.folder_btn.clicked.connect(self.open_folder)

        self.status = QLabel("Двойной клик по строке - установить. Зависимости (Fabric API и др.) ставятся сами.", self)
        self.status.setGeometry(59, 636, 860, 40)
        self.status.setWordWrap(True)
        self.status.setStyleSheet(f"color: rgba(255,244,214,170); font-family:'{FONT_FAMILY}'; font-size:13px; background:transparent;")
        self._loaded = False
        self.refresh_installed()

    def _cap(self, text, x, y):
        l = QLabel(text, self)
        l.setGeometry(x, y, 420, 18)
        l.setStyleSheet(f"color: rgb(170,160,140); font-family:'{FONT_FAMILY}'; font-size:11px; font-weight:800; letter-spacing:1px; background:transparent;")

    def showEvent(self, e):
        if not self._loaded:
            self._loaded = True
            self.search()
        super().showEvent(e)

    def _busy(self, busy: bool):
        for w in (self.go, self.install_btn, self.remove_btn, self.kind):
            w.setEnabled(not busy)

    def _run(self, fn, on_done):
        if self.worker is not None and self.worker.isRunning():
            return
        self._busy(True)
        w = TaskWorker(fn)
        w.log.connect(self.status.setText)
        w.done.connect(on_done)
        w.failed.connect(self._fail)
        w.finished.connect(lambda: self._busy(False))
        self.worker = w
        w.start()

    def _fail(self, msg: str):
        self.status.setText(f"Ошибка: {msg}")

    def search(self):
        kind, q = self.kind.currentData(), self.query.text().strip()
        self.status.setText("Ищу…")
        self._run(lambda log: core.modrinth_search(q, kind), self._show_hits)

    def _show_hits(self, hits):
        self.hits = hits
        self.results.clear()
        for h in hits:
            it = QListWidgetItem(f"{h['title']}  -  {h['author']}\n{h['desc'][:90]}")
            self.results.addItem(it)
        self.status.setText(f"Найдено: {len(hits)}" if hits else "Ничего не найдено для 1.21.4")

    def install(self):
        row = self.results.currentRow()
        if row < 0 or row >= len(self.hits):
            self.status.setText("Сначала выбери строку в списке слева")
            return
        h, kind = self.hits[row], self.kind.currentData()
        self._run(lambda log: core.install_project(h["id"], kind, log) or h["title"],
                  lambda title: (self.status.setText(f"Установлено: {title}"), self.refresh_installed()))

    def refresh_installed(self):
        self.installed.clear()
        self.files = core.list_installed(self.kind.currentData())
        for f in self.files:
            self.installed.addItem(QListWidgetItem(f.name))

    def remove(self):
        row = self.installed.currentRow()
        if row < 0 or row >= len(self.files):
            return
        f = self.files[row]
        if QMessageBox.question(self, "BeeVisual", f"Удалить {f.name}?") == QMessageBox.StandardButton.Yes:
            core.remove_installed(f)
            self.refresh_installed()
            self.status.setText(f"Удалено: {f.name}")

    def open_folder(self):
        d = core.MC_DIR / core.KINDS[self.kind.currentData()][1]
        d.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))


class SettingsPage(QWidget):
    changed = Signal()

    def __init__(self, parent, cfg: dict):
        super().__init__(parent)
        page_title(self, "Настройки")
        lab = lambda text, y: self._label(text, y)
        lab("ПАПКА ИГРЫ", 140)
        self.path = QLabel(str(core.MC_DIR), self)
        self.path.setGeometry(59, 164, 640, 30)
        self.path.setStyleSheet(f"color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:14px; background: rgba(255,255,255,16); border:1px solid rgba(255,255,255,24); border-radius:10px; padding-left:12px;")
        self.open_btn = self._button("Открыть папку", 715, 164, 160)
        self.open_btn.clicked.connect(lambda: self._open(core.MC_DIR))
        self.logs_btn = self._button("Открыть логи", 890, 164, 160)
        self.logs_btn.clicked.connect(lambda: self._open(core.LOG_DIR))
        lab("ДОПОЛНИТЕЛЬНЫЕ JVM-АРГУМЕНТЫ", 230)
        self.jvm = QLineEdit(cfg["jvm_extra"], self)
        self.jvm.setPlaceholderText("например: -XX:+UseG1GC")
        self.jvm.setGeometry(59, 254, 816, 34)
        self.jvm.setStyleSheet(f"QLineEdit {{ color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:14px; background: rgba(255,255,255,16); border:1px solid rgba(255,255,255,24); border-radius:10px; padding-left:12px; }} QLineEdit:focus {{ border-color: rgba(255,200,30,150); }}")
        self.jvm.editingFinished.connect(self.changed)
        self.hide_cb = QCheckBox("Скрывать лаунчер, пока идёт игра", self)
        self.hide_cb.setChecked(bool(cfg["hide_while_playing"]))
        self.hide_cb.setGeometry(59, 320, 500, 28)
        self.hide_cb.setStyleSheet(f"QCheckBox {{ color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:15px; font-weight:600; spacing:10px; }} QCheckBox::indicator {{ width:18px; height:18px; border-radius:5px; background: rgb(58,52,40); }} QCheckBox::indicator:checked {{ background: rgb(255,190,30); }}")
        self.hide_cb.toggled.connect(self.changed)
        info = QLabel("Java скачивается автоматически вместе с игрой. Настройки модулей — в игре на Right Shift.", self)
        info.setGeometry(59, 372, 816, 40)
        info.setWordWrap(True)
        info.setStyleSheet(f"color: rgba(255,244,214,150); font-family:'{FONT_FAMILY}'; font-size:13px; background:transparent;")

    def _label(self, text: str, y: int):
        l = QLabel(text, self)
        l.setGeometry(59, y, 600, 20)
        l.setStyleSheet(f"color: rgb(170,160,140); font-family:'{FONT_FAMILY}'; font-size:11px; font-weight:800; letter-spacing:1px; background:transparent;")

    def _button(self, text: str, x: int, y: int, w: int) -> QPushButton:
        b = QPushButton(text, self)
        b.setGeometry(x, y, w, 30)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"QPushButton {{ color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:13px; font-weight:700; background: rgba(255,255,255,20); border:1px solid rgba(255,190,40,70); border-radius:10px; }} QPushButton:hover {{ background: rgba(255,200,30,40); }}")
        return b

    @staticmethod
    def _open(path: Path):
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


# ------------------------------------------------------------------ main window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = core.load_config()
        self.setWindowTitle("BeeVisual")
        self.setWindowIcon(QIcon(str(ASSETS / "logo" / "logo_128.png")))
        self.setFixedSize(W, H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.worker: LaunchWorker | None = None
        self.proc = None
        self.log_path = ""

        # backgrounds (cross-fade every 15 s)
        names = ["bg_sunset", "bg_night", "bg_cave"]
        self.bgs = [cover(QPixmap(str(ASSETS / "backgrounds" / f"{n}.png")), W, H) for n in names]
        self.bg_i, self.bg_next, self.bg_t = 0, 0, 1.0
        self.bg_anim = QVariantAnimation(self)
        self.bg_anim.setDuration(1200)
        self.bg_anim.setStartValue(0.0)
        self.bg_anim.setEndValue(1.0)
        self.bg_anim.valueChanged.connect(self._bg_step)
        self.bg_anim.finished.connect(self._bg_done)
        self.bg_timer = QTimer(self)
        self.bg_timer.timeout.connect(self._bg_advance)
        self.bg_timer.start(15000)

        # sidebar
        self.side = QWidget(self)
        self.side.setGeometry(0, 0, SIDE, H)
        logo = QLabel(self.side)
        logo.setPixmap(QPixmap(str(ASSETS / "logo" / "logo_128.png")).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setGeometry(22, 22, 56, 56)
        t1 = QLabel("BeeVisual", self.side)
        t1.setGeometry(92, 26, 160, 30)
        t1.setStyleSheet(f"color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:22px; font-weight:800; background:transparent;")
        t2 = QLabel("LAUNCHER", self.side)
        t2.setGeometry(93, 58, 140, 16)
        t2.setStyleSheet(f"color: rgb(255,200,30); font-family:'{FONT_FAMILY}'; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent;")
        self.nav = []
        for i, (ic, txt) in enumerate([("play", "Играть"), ("news", "Новости"), ("cat_render", "Визуалы"), ("cat_world", "Загрузки"), ("settings", "Настройки")]):
            b = NavButton(self.side, ic, txt)
            b.move(16, 138 + i * 56)
            b.clicked.connect(lambda _=False, idx=i: self.stack.setCurrentIndex(idx))
            self.nav.append(b)
        self.nav[0].setChecked(True)
        self.user = QLabel(self.side)
        self.user.setGeometry(76, 648, 160, 36)
        self.logo36 = QPixmap(str(ASSETS / "logo" / "logo_128.png")).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._refresh_user()
        ver = QLabel(f"v{core.LAUNCHER_VERSION}  •  MC {core.MC_VERSION}", self.side)
        ver.setGeometry(28, 700, 200, 16)
        ver.setStyleSheet(f"color: rgba(255,244,214,90); font-family:'{FONT_FAMILY}'; font-size:10px; background:transparent;")

        # pages
        self.stack = QStackedWidget(self)
        self.stack.setGeometry(SIDE + 1, 0, W - SIDE - 1, H)
        self.hero = HeroPage(self.stack, self.cfg)
        self.news = NewsPage(self.stack)
        self.visuals = VisualsPage(self.stack)
        self.downloads = DownloadsPage(self.stack)
        self.settings = SettingsPage(self.stack, self.cfg)
        for pg in (self.hero, self.news, self.visuals, self.downloads, self.settings):
            self.stack.addWidget(pg)
        self.hero.btn.clicked.connect(self.on_launch)
        self.hero.nick.editingFinished.connect(self._save)
        self.hero.nick.textChanged.connect(lambda _t: self._refresh_user())
        self.hero.ram.currentIndexChanged.connect(lambda _i: self._save())
        self.settings.changed.connect(self._save)

        # window buttons
        self.btn_min = RoundButton(self, QColor(255, 190, 40))
        self.btn_min.move(W - 58, 22)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_close = RoundButton(self, QColor(240, 90, 80))
        self.btn_close.move(W - 32, 22)
        self.btn_close.clicked.connect(self.close)

        self.poll = QTimer(self)
        self.poll.timeout.connect(self._poll_game)

    # --- backgrounds
    def _bg_advance(self):
        if self.bg_anim.state() == QVariantAnimation.State.Running:
            return
        self.bg_next = (self.bg_i + 1) % len(self.bgs)
        self.bg_anim.start()

    def _bg_step(self, v):
        self.bg_t = float(v)
        self.update()

    def _bg_done(self):
        self.bg_i, self.bg_t = self.bg_next, 1.0
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.bgs[self.bg_i])
        if self.bg_next != self.bg_i and self.bg_t < 1.0:
            p.setOpacity(self.bg_t)
            p.drawPixmap(0, 0, self.bgs[self.bg_next])
            p.setOpacity(1.0)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        p.fillRect(0, 0, SIDE, H, QColor(10, 9, 7, 235))
        p.fillRect(SIDE, 0, 1, H, QColor(255, 190, 40, 30))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        p.setBrush(QColor(255, 255, 255, 16))
        p.drawRoundedRect(QRectF(16.5, 636.5, 227, 52), 14, 14)
        p.drawPixmap(28, 644, self.logo36)
        p.setPen(QColor(255, 244, 214, 120))
        p.setFont(font(12, QFont.Weight.DemiBold))
        p.drawText(QRectF(W - 330, 14, 240, 30), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "BeeVisual 1.0")

    # --- dragging the frameless window
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.position().y() < 70 and self.windowHandle():
            self.windowHandle().startSystemMove()
        super().mousePressEvent(e)

    # --- config
    def _refresh_user(self):
        name = self.hero.nick.text() if hasattr(self, "hero") else self.cfg["nickname"]
        self.user.setText(f"{name or '—'}")
        self.user.setStyleSheet(f"color: rgb(255,244,214); font-family:'{FONT_FAMILY}'; font-size:14px; font-weight:700; background: transparent; padding-left: 0px;")

    def _save(self):
        nick = self.hero.nick.text().strip()
        if core.valid_nickname(nick):
            self.cfg["nickname"] = nick
        self.cfg["ram_gb"] = int(self.hero.ram.currentData() or 4)
        self.cfg["jvm_extra"] = self.settings.jvm.text().strip()
        self.cfg["hide_while_playing"] = self.settings.hide_cb.isChecked()
        core.save_config(self.cfg)

    # --- launching
    def on_launch(self):
        nick = self.hero.nick.text().strip()
        if not core.valid_nickname(nick):
            self.hero.set_status("Ник: 3–16 символов, только латиница, цифры и _", error=True)
            return
        self._save()
        self.hero.set_progress(0, 0)
        self.hero.set_status("Подготовка…")
        self.hero.set_running(True)
        self.worker = LaunchWorker(self.cfg)
        self.worker.status.connect(lambda t: self.hero.set_status(t))
        self.worker.progress.connect(self.hero.set_progress)
        self.worker.started_game.connect(self._on_started)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_started(self, proc, log_path):
        self.proc, self.log_path = proc, log_path
        self.hero.set_status("Игра запущена. Удачи!")
        self.hero.set_progress(1, 1)
        if self.cfg.get("hide_while_playing"):
            self.hide()
        self.poll.start(1000)

    def _on_failed(self, msg: str):
        self.hero.set_running(False)
        self.hero.set_status("Ошибка запуска (подробности в окне)", error=True)
        QMessageBox.critical(self, "BeeVisual", f"Не удалось подготовить запуск:\n\n{msg}")

    def _poll_game(self):
        if self.proc is None:
            self.poll.stop()
            return
        code = self.proc.poll()
        if code is None:
            return
        self.poll.stop()
        self.proc = None
        self.show()
        self.hero.set_running(False)
        if code == 0:
            self.hero.set_status("Игра закрыта")
        else:
            self.hero.set_status(f"Игра завершилась с ошибкой (код {code})", error=True)
            QMessageBox.warning(self, "BeeVisual", f"Minecraft завершился с кодом {code}.\nЛог: {self.log_path}\n\n{core.tail(self.log_path)}")

    def closeEvent(self, e):
        if self.worker is not None and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(2000)
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    global FONT_FAMILY
    loaded = False
    for f in sorted((ASSETS / "fonts").glob("*.otf")):
        loaded = QFontDatabase.addApplicationFont(str(f)) >= 0 or loaded
    if not loaded:
        FONT_FAMILY = "Segoe UI"
    app.setFont(font(13))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
