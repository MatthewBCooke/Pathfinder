"""
Maze geometry utilities for Pathfinder analysis.
"""

from pydantic import BaseModel, Field
from typing import Tuple
import math


class MazeGeometry(BaseModel):
    """
    Morris Water Maze geometry configuration.
    All measurements in same units as tracking data (pixels or cm).
    """
    
    # Pool parameters
    center_x: float = Field(..., description="Pool center X coordinate")
    center_y: float = Field(..., description="Pool center Y coordinate")
    pool_diameter: float = Field(..., description="Pool diameter")
    
    # Platform parameters
    platform_x: float = Field(..., description="Platform center X coordinate")
    platform_y: float = Field(..., description="Platform center Y coordinate")
    platform_diameter: float = Field(..., description="Platform diameter")
    
    @property
    def pool_radius(self) -> float:
        """Get pool radius"""
        return self.pool_diameter / 2
    
    @property
    def platform_radius(self) -> float:
        """Get platform radius"""
        return self.platform_diameter / 2
    
    @property
    def pool_center(self) -> Tuple[float, float]:
        """Get pool center as tuple"""
        return (self.center_x, self.center_y)
    
    @property
    def platform_center(self) -> Tuple[float, float]:
        """Get platform center as tuple"""
        return (self.platform_x, self.platform_y)
    
    def distance_to_pool_center(self, x: float, y: float) -> float:
        """Calculate distance from point to pool center"""
        dx = x - self.center_x
        dy = y - self.center_y
        return math.sqrt(dx**2 + dy**2)
    
    def distance_to_platform(self, x: float, y: float) -> float:
        """Calculate distance from point to platform center"""
        dx = x - self.platform_x
        dy = y - self.platform_y
        return math.sqrt(dx**2 + dy**2)
    
    def distance_to_wall(self, x: float, y: float) -> float:
        """Calculate distance from point to pool wall"""
        dist_to_center = self.distance_to_pool_center(x, y)
        return self.pool_radius - dist_to_center
    
    def is_in_pool(self, x: float, y: float) -> bool:
        """Check if point is inside the pool"""
        return self.distance_to_pool_center(x, y) <= self.pool_radius
    
    def is_on_platform(self, x: float, y: float) -> bool:
        """Check if point is on the platform"""
        return self.distance_to_platform(x, y) <= self.platform_radius
    
    def angle_from_center(self, x: float, y: float) -> float:
        """Calculate angle from pool center to point (radians)"""
        dx = x - self.center_x
        dy = y - self.center_y
        return math.atan2(dy, dx)
    
    def get_quadrant(self, x: float, y: float) -> int:
        """
        Get quadrant number (1-4) based on platform location.
        Quadrant 1 contains the platform.
        """
        # Calculate angle relative to platform
        platform_angle = self.angle_from_center(self.platform_x, self.platform_y)
        point_angle = self.angle_from_center(x, y)
        
        # Normalize to 0-2π
        relative_angle = (point_angle - platform_angle) % (2 * math.pi)
        
        # Determine quadrant (0-90° = Q1, 90-180° = Q2, etc.)
        quadrant = int(relative_angle / (math.pi / 2)) + 1
        
        return min(quadrant, 4)  # Ensure 1-4 range
    
    def calculate_annulus_40(self, x: float, y: float) -> int:
        """
        Calculate annulus-40 value (corridor around platform).
        Returns counter value based on proximity to platform corridor.
        """
        # This is a simplified version - full implementation would be more complex
        dist_to_platform = self.distance_to_platform(x, y)
        
        # Define corridor width (typically platform radius + buffer)
        corridor_width = self.platform_radius * 3
        
        if dist_to_platform <= corridor_width:
            return 1
        else:
            return 0
