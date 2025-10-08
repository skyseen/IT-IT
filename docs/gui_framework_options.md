# GUI Framework Options Beyond Tkinter

The existing IT-IT desktop experience is implemented with Tkinter because it ships with CPython and keeps packaging light. While the current light beauty-tech polish helps, Tkinter still limits the amount of visual refinement and interaction fidelity we can achieve. This note captures alternative Python-friendly GUI stacks that can deliver a richer, more modern experience while preserving the tool's backend workflows.

## Evaluation Criteria

To stay aligned with the automation team's needs, each option was reviewed against the following:

- **Aesthetic flexibility** – depth of styling, animation support, responsive layouts.
- **Productivity** – quality of tooling, learning curve for engineers/designers, community resources.
- **Compatibility** – how easily the current workflow logic (email triggers, SAP utilities, telco parsers) can be reused.
- **Distribution** – packaging implications for Windows-first deployment.

## Recommended Path: PySide6 (Qt for Python)

Qt remains the most mature cross-platform GUI stack for desktop applications. PySide6 (the officially supported Qt for Python bindings) combines a rich component set, hardware-accelerated rendering, and powerful styling hooks.

### Why PySide6 Works Well

- **Advanced styling** – Qt's `QtQuick`/`QSS` styling supports glassmorphism, translucency, and depth cues that match the beauty-tech prompt. Components can be themed globally or per-widget.
- **Layout fidelity** – flexible layouts, dockable panels, stacked widgets, and high-DPI scaling make complex admin dashboards easier to model than in Tkinter.
- **Reuse of backend code** – the business logic that lives in modules such as `config_manager`, `activity_log`, `sap_workflows`, and `telco_workflows` can be imported directly. Only the view/controller glue needs to be rewritten.
- **Design tooling** – designers can deliver Qt Design Studio files or Figma exports that map neatly to QML, easing collaboration.
- **Deployment** – PyInstaller and Briefcase both support bundling PySide6 applications for Windows/macOS. File size grows (~80–100 MB), but remains manageable for the ops team.

### Migration Outline

1. **Abstract workflow services** – extract Tkinter-specific dialogs from `ui.py`/`sap_workflows.py` into backend helpers that accept primitive values. This keeps PySide6 controllers thin.
2. **Implement a Qt main window** – create a `MainWindow` with:
   - A hero header for environment & status badges.
   - A `QTabWidget` hosting "User Ops", "SAP", "Agile", "Telecom", and "Operations Center" pages.
   - Shared `CommandCard` components (icon, title, description, CTA) styled with gradients/glass.
3. **Port interactive flows** – rebuild multi-user forms and SAP dialogs as `QDialog` instances. Use `QFileDialog` and `QMessageBox` for file selection and confirmations.
4. **Introduce a design system** – consolidate typography, color tokens, and spacing in a `Palette` module so themes can be swapped quickly.
5. **Iterate with designers** – wire high-fidelity prototypes (Figma → Qt) to ensure each microinteraction (hover glow, loading shimmer) matches the prompt.

### Prototype Skeleton

The following PySide6 prototype demonstrates the layout strategy. It reuses the backend logging/profile services and shows how multi-user dialogs can feed existing workflows without Tkinter:

```python
# prototypes/pyside6_app.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict

from PySide6 import QtCore, QtWidgets

from activity_log import get_recent_events, log_event
from config_manager import get_active_profile_name


@dataclass
class CommandAction:
    label: str
    description: str
    handler: Callable[[QtWidgets.QWidget], None]
    accent: str = "#8AA7FF"


class CommandCard(QtWidgets.QFrame):
    def __init__(self, action: CommandAction, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commandCard")
        self.setProperty("accent", action.accent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QtWidgets.QLabel(action.label)
        title.setObjectName("cardTitle")
        body = QtWidgets.QLabel(action.description)
        body.setObjectName("cardBody")
        body.setWordWrap(True)

        cta = QtWidgets.QPushButton("Launch")
        cta.setObjectName("cardCta")
        cta.clicked.connect(lambda: action.handler(self))

        layout.addWidget(title)
        layout.addWidget(body, 1)
        layout.addWidget(cta)


class ActivityFeed(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Operations Center", parent)
        self.setObjectName("activityFeed")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)
        refresh = QtWidgets.QPushButton("Refresh Feed")
        refresh.clicked.connect(self.populate)
        layout.addWidget(refresh)
        self.populate()

    def populate(self) -> None:
        self.list_widget.clear()
        for event in get_recent_events(limit=12):
            timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M")
            self.list_widget.addItem(f"[{timestamp}] {event.summary}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IT ! IT – Beauty Tech Edition")
        self.resize(1200, 780)

        container = QtWidgets.QWidget()
        container.setObjectName("appContainer")
        self.setCentralWidget(container)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        header = self._build_header(container)
        layout.addWidget(header)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._build_user_ops_tab(), "User Ops")
        tabs.addTab(self._build_placeholder_tab("SAP"), "SAP")
        tabs.addTab(self._build_placeholder_tab("Agile"), "Agile")
        tabs.addTab(self._build_placeholder_tab("Telecom"), "Telecom")
        tabs.addTab(ActivityFeed(), "Operations Center")
        layout.addWidget(tabs, 1)

    def _build_header(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        header = QtWidgets.QFrame(parent)
        header.setObjectName("heroHeader")
        grid = QtWidgets.QGridLayout(header)
        grid.setContentsMargins(24, 24, 24, 24)
        grid.setHorizontalSpacing(32)

        banner = QtWidgets.QLabel("IT ! IT Admin Toolkit")
        banner.setObjectName("heroTitle")
        sub = QtWidgets.QLabel("Collaborative automation cockpit with a luminous beauty-tech polish.")
        sub.setObjectName("heroSubtitle")

        badge = QtWidgets.QLabel()
        badge.setObjectName("statusBadge")
        badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        badge.setText(f"● {get_active_profile_name()} – Ready")

        grid.addWidget(banner, 0, 0, 1, 1)
        grid.addWidget(sub, 1, 0, 1, 1)
        grid.addWidget(badge, 0, 1, 2, 1)
        return header

    def _build_user_ops_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(tab)
        layout.setSpacing(18)
        layout.setContentsMargins(6, 6, 6, 6)

        actions: Dict[str, CommandAction] = {
            "new_user": CommandAction(
                label="Create New User Pack",
                description="Bundle welcome assets and trigger onboarding email sequences.",
                handler=lambda parent: log_event("prototype", "Trigger new user dialog"),
                accent="#7CC3A2",
            ),
            "disable_user": CommandAction(
                label="Disable User Access",
                description="Queue off-boarding notifications and archive instructions.",
                handler=lambda parent: log_event("prototype", "Trigger disable dialog"),
                accent="#E69896",
            ),
        }

        row = 0
        col = 0
        for action in actions.values():
            card = CommandCard(action)
            layout.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)
        return tab

    def _build_placeholder_tab(self, label: str) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        message = QtWidgets.QLabel(f"Qt prototype placeholder for {label} workflows.")
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message.setObjectName("placeholderText")
        layout.addWidget(message, 1)
        return tab


def launch() -> None:
    app = QtWidgets.QApplication([])
    theme_path = Path(__file__).with_name("pyside6_theme.qss")
    app.setStyleSheet(theme_path.read_text())
    window = MainWindow()
    window.show()
    app.exec()
```

The companion `pyside6_theme.qss` stylesheet (also in the `prototypes/` folder) applies glass panels, hover glows, and typographic rhythm inline with the beauty-tech prompt. Engineers can run the prototype with `python prototypes/pyside6_app.py` after installing PySide6 (`pip install PySide6`).

## Other Frameworks to Consider

| Framework | Strengths | Trade-offs |
|-----------|-----------|-----------|
| **Flet** | Flutter-inspired UI with web+desktop targets, reactive model, rich widget catalog. | Heavier runtime, limited offline packaging maturity for enterprise environments.
| **DearPyGui** | GPU-accelerated immediate mode UI, great for dense dashboards and real-time telemetry. | Requires rethinking layout paradigm; styling polished but less "beauty" oriented.
| **Kivy** | Touch-friendly, highly animated experiences. | Mobile-first metaphors feel less natural for mouse/keyboard admin workflows.

## Recommended Next Steps

1. Socialize the PySide6 prototype with stakeholders to confirm the visual direction resonates.
2. Incrementally port highest-value workflows (e.g., multi-user onboarding) into Qt dialogs while keeping Tkinter UI as a fallback during transition.
3. Align with packaging/IT to confirm PySide6 deploy plan and necessary runtimes for operators.

This approach gives the team a clear migration path away from Tkinter, unlocking the richer UI/UX the beauty-tech brief envisions without disrupting the underlying automation logic.
