"""
Maze Visualization Widget for Pathfinder GUI.
Displays visual representation of pool, platform, and analysis zones.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSlot
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
import math


class MazeVisualizationWidget(QWidget):
    """
    Widget that draws a visual representation of the Morris Water Maze setup.
    Shows pool, platform, and analysis zones (thigmotaxis, chaining, corridor).
    """

    def __init__(self, parent=None, parameters=None):
        super().__init__(parent)

        # Store parameters object
        self.parameters = parameters

        # Default spatial parameters
        self.pool_center_x = 250.0
        self.pool_center_y = 250.0
        self.pool_diameter = 500.0
        self.platform_x = 350.0
        self.platform_y = 150.0
        self.platform_diameter = 50.0

        self.setMinimumSize(600, 600)
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Maze Geometry Visualization")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Legend
        legend = QLabel(
            "🔵 Pool  |  🔴 Platform  |  "
            "⚫ Thigmotaxis  |  🟡 Chaining  |  "
            "🟣 Focal Search  |  🟢 Search Corridor"
        )
        legend.setAlignment(Qt.AlignCenter)
        legend.setStyleSheet("font-size: 10pt; padding: 5px;")
        layout.addWidget(legend)

        layout.addStretch()

    @pyqtSlot(dict)
    def update_parameters(self, params):
        """Update spatial parameters and redraw"""
        self.pool_center_x = params.get('pool_center_x', self.pool_center_x)
        self.pool_center_y = params.get('pool_center_y', self.pool_center_y)
        self.pool_diameter = params.get('pool_diameter', self.pool_diameter)
        self.platform_x = params.get('platform_x', self.platform_x)
        self.platform_y = params.get('platform_y', self.platform_y)
        self.platform_diameter = params.get('platform_diameter', self.platform_diameter)
        self.update()  # Trigger repaint

    def set_parameters(self, parameters):
        """Set the Parameters object and redraw"""
        self.parameters = parameters
        self.update()  # Trigger repaint

    def _get_zone_parameters(self):
        """Get zone parameters from Parameters object or use defaults"""
        if self.parameters is None:
            # Defaults when no parameters object
            return {
                'thigmotaxis_percent': 20.0,
                'chaining_width_percent': 6.0,
                'focal_multiplier': 1.5,
                'directed_multiplier': 3.5,
                'corridor_degrees': 15.0,
                'pixels_per_cm': 1.0
            }
        else:
            return {
                'thigmotaxis_percent': self.parameters.thigmotaxis_zone_percent,
                'chaining_width_percent': self.parameters.chaining_radius_percent,
                'focal_multiplier': self.parameters.focal_search_radius_multiplier,
                'directed_multiplier': self.parameters.directed_search_radius_multiplier,
                'corridor_degrees': self.parameters.corridor_width_degrees,
                'pixels_per_cm': self.parameters.pixels_per_cm
            }

    def paintEvent(self, event):
        """Draw the maze visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get widget dimensions
        width = self.width()
        height = self.height()

        # Calculate scaling to fit pool in widget with margins
        margin = 50
        available_width = width - 2 * margin
        available_height = height - 2 * margin
        scale = min(available_width, available_height) / self.pool_diameter

        # Transform coordinates: origin at top-left, y increases downward
        # We need to map pool coordinates to widget coordinates
        def to_widget_x(x):
            return margin + (x - self.pool_center_x + self.pool_diameter / 2) * scale

        def to_widget_y(y):
            return margin + (y - self.pool_center_y + self.pool_diameter / 2) * scale

        # Pool center in widget coordinates
        pool_center_widget_x = to_widget_x(self.pool_center_x)
        pool_center_widget_y = to_widget_y(self.pool_center_y)
        pool_radius_widget = (self.pool_diameter / 2) * scale

        # Platform center in widget coordinates
        platform_center_widget_x = to_widget_x(self.platform_x)
        platform_center_widget_y = to_widget_y(self.platform_y)
        platform_radius_widget = (self.platform_diameter / 2) * scale

        # Get zone parameters from settings
        zone_params = self._get_zone_parameters()

        # Calculate pool radius
        pool_radius = self.pool_diameter / 2

        # 1. Draw thigmotaxis zone (annulus near wall)
        thigmo_thickness = pool_radius * (zone_params['thigmotaxis_percent'] / 100.0)
        thigmo_inner_radius = (pool_radius - thigmo_thickness) * scale
        thigmo_outer_radius = pool_radius_widget

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(200, 200, 200, 100)))  # Light gray, semi-transparent

        # Draw outer circle
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            thigmo_outer_radius,
            thigmo_outer_radius
        )

        # Draw inner circle (to create annulus) in background color
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            thigmo_inner_radius,
            thigmo_inner_radius
        )

        # 2. Draw chaining zone (annulus centered on pool center, midpoint at platform distance)
        # Calculate distance from pool center to platform
        dx_plat = self.platform_x - self.pool_center_x
        dy_plat = self.platform_y - self.pool_center_y
        dist_to_platform = math.sqrt(dx_plat**2 + dy_plat**2)

        # Annulus width (convert from % of diameter to absolute units)
        annulus_width = (self.pool_diameter * zone_params['chaining_width_percent'] / 100)

        # Inner and outer radii: midpoint of annulus is at platform distance
        chaining_inner_radius = dist_to_platform - (annulus_width / 2)
        chaining_outer_radius = dist_to_platform + (annulus_width / 2)

        # Ensure radii stay within pool bounds
        chaining_inner_radius = max(self.platform_diameter, chaining_inner_radius)  # At least as big as platform
        chaining_outer_radius = min(pool_radius, chaining_outer_radius)  # At most pool radius

        chaining_inner_radius_widget = chaining_inner_radius * scale
        chaining_outer_radius_widget = chaining_outer_radius * scale

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 0, 80)))  # Yellow, semi-transparent

        # Draw outer circle
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            chaining_outer_radius_widget,
            chaining_outer_radius_widget
        )

        # Draw inner circle (to create annulus) in background color
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            chaining_inner_radius_widget,
            chaining_inner_radius_widget
        )

        # Draw chaining zone boundary lines for clarity
        painter.setPen(QPen(QColor(255, 200, 0), 2, Qt.DashLine))  # Yellow dashed
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            chaining_inner_radius_widget,
            chaining_inner_radius_widget
        )
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            chaining_outer_radius_widget,
            chaining_outer_radius_widget
        )

        # 3. Draw directed search corridor (triangular from opposite wall toward platform)
        # Drawn AFTER annulus zones so it's not obscured by white inner circles
        corridor_width_degrees = zone_params['corridor_degrees']  # degrees on each side

        # Calculate angle from pool center to platform
        dx = self.platform_x - self.pool_center_x
        dy = self.platform_y - self.pool_center_y
        angle_to_platform_rad = math.atan2(dy, dx)

        # Draw corridor as a triangular polygon from opposite wall to platform
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(100, 255, 100, 80)))  # Light green, transparent

        # Starting point: opposite wall (single point - narrow end of corridor)
        opposite_angle_rad = angle_to_platform_rad + math.pi
        start_x = self.pool_center_x + pool_radius * math.cos(opposite_angle_rad)
        start_y = self.pool_center_y + pool_radius * math.sin(opposite_angle_rad)
        start_x_widget = pool_center_widget_x + (start_x - self.pool_center_x) * scale
        start_y_widget = pool_center_widget_y + (start_y - self.pool_center_y) * scale

        # Two edge points at platform side (wide end of corridor)
        # These define the angular width of the corridor
        left_plat_angle_rad = angle_to_platform_rad - math.radians(corridor_width_degrees)
        right_plat_angle_rad = angle_to_platform_rad + math.radians(corridor_width_degrees)

        # Extend to pool edge on platform side
        left_end_x = self.pool_center_x + pool_radius * math.cos(left_plat_angle_rad)
        left_end_y = self.pool_center_y + pool_radius * math.sin(left_plat_angle_rad)
        right_end_x = self.pool_center_x + pool_radius * math.cos(right_plat_angle_rad)
        right_end_y = self.pool_center_y + pool_radius * math.sin(right_plat_angle_rad)

        left_end_x_widget = pool_center_widget_x + (left_end_x - self.pool_center_x) * scale
        left_end_y_widget = pool_center_widget_y + (left_end_y - self.pool_center_y) * scale
        right_end_x_widget = pool_center_widget_x + (right_end_x - self.pool_center_x) * scale
        right_end_y_widget = pool_center_widget_y + (right_end_y - self.pool_center_y) * scale

        # Draw triangular corridor: single point at far wall, two points at platform side
        from PyQt5.QtGui import QPolygonF
        corridor_polygon = QPolygonF([
            QPointF(start_x_widget, start_y_widget),         # Narrow end at far wall
            QPointF(left_end_x_widget, left_end_y_widget),   # Left edge at platform side
            QPointF(right_end_x_widget, right_end_y_widget), # Right edge at platform side
        ])
        painter.drawPolygon(corridor_polygon)

        # 4. Draw focal search zone (small, tight search around platform)
        focal_search_radius = self.platform_diameter * zone_params['focal_multiplier']
        focal_search_radius_widget = focal_search_radius * scale

        painter.setPen(QPen(QColor(255, 100, 200), 2, Qt.DashLine))  # Pink/magenta dashed
        painter.setBrush(Qt.NoBrush)  # No fill, just outline
        painter.drawEllipse(
            QPointF(platform_center_widget_x, platform_center_widget_y),
            focal_search_radius_widget,
            focal_search_radius_widget
        )

        # 4. Draw pool boundary
        painter.setPen(QPen(QColor(0, 100, 200), 3))  # Blue
        painter.setBrush(QBrush(QColor(200, 230, 255, 50)))  # Light blue, transparent
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            pool_radius_widget,
            pool_radius_widget
        )

        # 5. Draw platform
        painter.setPen(QPen(QColor(200, 0, 0), 2))  # Red
        painter.setBrush(QBrush(QColor(255, 100, 100)))  # Light red
        painter.drawEllipse(
            QPointF(platform_center_widget_x, platform_center_widget_y),
            platform_radius_widget,
            platform_radius_widget
        )

        # 6. Draw pool center marker
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.black))
        painter.drawEllipse(
            QPointF(pool_center_widget_x, pool_center_widget_y),
            3, 3
        )

        # 7. Draw coordinate info at bottom
        painter.setPen(QPen(Qt.black))
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(
            margin,
            height - margin + 30,
            f"Pool Center: ({self.pool_center_x:.1f}, {self.pool_center_y:.1f}) | "
            f"Platform: ({self.platform_x:.1f}, {self.platform_y:.1f})"
        )
