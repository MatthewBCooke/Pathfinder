#!/usr/bin/env python3
"""
Example usage of extracted heatmap and auto-parameter functions.

These functions are now pure analysis - no GUI dependencies!
"""

from pathfinder.analysis import aggregate_heatmap_data, calculate_auto_parameters
from pathfinder.types import HeatmapData, AutoParameters


def example_heatmap_analysis(experiment):
    """
    Example: Generate heatmap data without GUI.
    
    The visualization layer (matplotlib) would consume this HeatmapData.
    """
    # Define filters (same as GUI inputs, but as dict)
    filters = {
        'day_filter': 'All',      # Options: 'All', '1', '1-3' (range)
        'trial_filter': '1-5'     # Options: 'All', '3', '1-10' (range)
    }
    
    # Call pure analysis function
    heatmap_data = aggregate_heatmap_data(
        experiment=experiment,
        filters=filters,
        gridsize=50,           # Grid size for hexbin
        gaussian_sigma=2.0     # Smoothing parameter
    )
    
    # Result is pure data - no plotting done yet!
    print(f"Collected {len(heatmap_data.x_raw)} data points")
    print(f"Spatial extent: {heatmap_data.extent}")
    print(f"Smoothed data shape: {heatmap_data.x_smoothed.shape}")
    
    # Now you could pass this to visualization layer
    # plot_heatmap_with_matplotlib(heatmap_data)  # GUI code stays separate
    
    return heatmap_data


def example_auto_parameters(experiment):
    """
    Example: Automatically calculate experimental parameters.
    
    No messagebox dialogs - warnings returned in result object.
    """
    # Fully automatic calculation
    params = calculate_auto_parameters(experiment)
    
    print(f"✅ Analyzed {params.trial_count} trials")
    print(f"Goal position: ({params.goal_x:.2f}, {params.goal_y:.2f})")
    print(f"Maze centre: ({params.maze_centre_x:.2f}, {params.maze_centre_y:.2f})")
    print(f"Maze diameter: {params.maze_diameter:.2f} (radius: {params.maze_radius:.2f})")
    print(f"Goal diameter: {params.goal_diameter:.2f}")
    
    # Check warnings (replaces GUI messageboxes)
    if params.warnings:
        print("\n⚠️  Warnings:")
        for warning in params.warnings:
            print(f"  - {warning}")
    
    return params


def example_partial_manual_override(experiment):
    """
    Example: Mix manual and automatic parameters.
    """
    # Manual goal, auto-calculate everything else
    params = calculate_auto_parameters(
        experiment,
        manual_goal=(100.0, 150.0),     # Manual goal position
        max_trial_length=60.0            # Custom time limit
    )
    
    print(f"Goal (manual): ({params.goal_x}, {params.goal_y})")
    print(f"Maze centre (auto): ({params.maze_centre_x:.2f}, {params.maze_centre_y:.2f})")
    
    return params


def example_heatmap_with_custom_filters(experiment):
    """
    Example: Various filter configurations.
    """
    # All days, all trials
    data_all = aggregate_heatmap_data(
        experiment,
        filters={'day_filter': 'All', 'trial_filter': 'All'}
    )
    
    # Single day, trial range
    data_day1 = aggregate_heatmap_data(
        experiment,
        filters={'day_filter': '1', 'trial_filter': '1-3'}
    )
    
    # Day range, all trials
    data_days_1_to_5 = aggregate_heatmap_data(
        experiment,
        filters={'day_filter': '1-5', 'trial_filter': 'All'}
    )
    
    # Single day, single trial
    data_specific = aggregate_heatmap_data(
        experiment,
        filters={'day_filter': '3', 'trial_filter': '2'}
    )
    
    return data_all, data_day1, data_days_1_to_5, data_specific


# ============================================================================
# How the GUI layer would use these functions
# ============================================================================

def gui_heatmap_button_callback(experiment, day_input, trial_input, gridsize_input):
    """
    Example: How the GUI heatmap() method should be refactored.
    
    BEFORE: heatmap() did analysis + plotting in one big method
    AFTER:  Split into analysis (pure) + visualization (GUI)
    """
    try:
        # 1. Call pure analysis function
        filters = {
            'day_filter': day_input,
            'trial_filter': trial_input
        }
        heatmap_data = aggregate_heatmap_data(
            experiment,
            filters,
            gridsize=int(gridsize_input)
        )
        
        # 2. Now do GUI visualization (stays in Pathfinder.py)
        visualize_heatmap_with_matplotlib(heatmap_data)
        
    except ValueError as e:
        # GUI error handling
        show_error_messagebox(f"Heatmap error: {e}")


def gui_auto_params_callback(experiment, goal_var, centre_var, diam_var):
    """
    Example: How getAutoLocations() should be refactored.
    
    BEFORE: getAutoLocations() mixed analysis with messagebox dialogs
    AFTER:  Analysis function returns warnings, GUI displays them
    """
    try:
        # Parse manual inputs (or None for auto)
        manual_goal = parse_manual_input(goal_var)  # None if "Auto"
        manual_centre = parse_manual_input(centre_var)
        manual_diameter = parse_manual_input(diam_var)
        
        # 1. Call pure analysis function
        params = calculate_auto_parameters(
            experiment,
            manual_goal=manual_goal,
            manual_maze_centre=manual_centre,
            manual_maze_diameter=manual_diameter
        )
        
        # 2. Update GUI fields with results
        update_gui_fields(params)
        
        # 3. Show warnings in GUI (if any)
        if params.warnings:
            show_warning_messagebox('\n'.join(params.warnings))
        
        return params
        
    except ValueError as e:
        # GUI error handling
        show_error_messagebox(f"Auto-calculation error: {e}")
        return None


# ============================================================================
# Placeholder functions (would be actual GUI code in Pathfinder.py)
# ============================================================================

def visualize_heatmap_with_matplotlib(heatmap_data: HeatmapData):
    """Placeholder for GUI visualization code."""
    import matplotlib.pyplot as plt
    import matplotlib.cm as CM
    
    plt.figure(figsize=(4, 4))
    plt.hexbin(
        heatmap_data.x_smoothed,
        heatmap_data.y_smoothed,
        gridsize=heatmap_data.gridsize,
        cmap=CM.jet,
        vmin=0
    )
    plt.colorbar()
    plt.gca().set_aspect('equal')
    plt.title("Heatmap")
    plt.show()


def show_error_messagebox(message):
    """Placeholder for GUI error dialog."""
    print(f"ERROR: {message}")


def show_warning_messagebox(message):
    """Placeholder for GUI warning dialog."""
    print(f"WARNING: {message}")


def update_gui_fields(params: AutoParameters):
    """Placeholder for updating GUI input fields."""
    print(f"Updating GUI with: goal=({params.goal_x}, {params.goal_y}), ...")


def parse_manual_input(var_value):
    """Placeholder for parsing GUI input."""
    if var_value in ["Auto", "auto", "automatic", "Automatic", ""]:
        return None
    return var_value


if __name__ == '__main__':
    print(__doc__)
    print("\nThese functions are now available for:")
    print("  - GUI layer (Pathfinder.py)")
    print("  - CLI tools")
    print("  - Jupyter notebooks")
    print("  - Batch processing scripts")
    print("\nNo tkinter or matplotlib required for analysis! 🎉")
