"""
Pure Python implementation of entropy calculation from MATLAB Entropy.m
Designed for pathfinder search strategy analysis.
"""

import numpy as np
from typing import Union


def entropy(
    x: Union[list, np.ndarray],
    y: Union[list, np.ndarray],
    Xp: float,
    Yp: float
) -> float:
    """
    Calculate entropy of a distribution of points relative to a platform goal position.
    
    This function computes the Shannon entropy based on the spatial distribution of
    coordinate points relative to a target platform position. The entropy metric
    combines:
    1. Average distance from all points to the platform goal
    2. The covariance structure (eigenvalue product) of the point distribution
    
    Algorithm:
    - Compute distances from each point (x[i], y[i]) to platform (Xp, Yp)
    - Calculate weighted mean and covariance of relative coordinates
    - Compute eigenvalues of the 2D covariance matrix
    - Calculate entropy as: 0.5 * log(mean_distance) + 0.25 * log(det(covariance))
    - Return mean entropy across all samples
    
    Args:
        x: Array-like of x-coordinates (can be list or numpy array)
        y: Array-like of y-coordinates (can be list or numpy array)
        Xp: X-coordinate of the platform goal position (float)
        Yp: Y-coordinate of the platform goal position (float)
    
    Returns:
        float: The computed entropy value. Returns NaN if inputs are empty or
               computation fails due to singular matrices.
    
    Raises:
        ValueError: If x and y arrays have different lengths
    
    Edge Cases:
        - Empty arrays: Returns NaN
        - Single point: Returns valid entropy based on that point
        - Divide by zero: Uses epsilon (1e-10) to prevent numerical issues
        - Singular covariance matrix: Uses epsilon to regularize eigenvalue product
    """
    
    # Handle input types and convert to numpy arrays
    x_arr = np.asarray(x, dtype=float).flatten()
    y_arr = np.asarray(y, dtype=float).flatten()
    
    # Edge case: empty arrays
    if len(x_arr) == 0 or len(y_arr) == 0:
        return np.nan
    
    # Validate matching dimensions
    if len(x_arr) != len(y_arr):
        raise ValueError(
            f"x and y arrays must have the same length. "
            f"Got x: {len(x_arr)}, y: {len(y_arr)}"
        )
    
    # Compute relative displacements from platform goal
    dx = x_arr - Xp  # Shape: (N,)
    dy = y_arr - Yp  # Shape: (N,)
    
    # Compute Euclidean distances from platform goal
    dist_squared = dx**2 + dy**2  # Shape: (N,)
    dist = np.sqrt(dist_squared)   # Shape: (N,)
    
    # Compute mean distance (scalar)
    mean_distance = np.mean(dist)  # Scalar
    
    # Initialize weighting (uniform weights in original implementation)
    # w is effectively a vector of ones
    weights = np.ones(len(x_arr))  # Shape: (N,)
    sum_weights = np.sum(weights)  # Scalar
    
    # Compute weighted means of relative coordinates
    weighted_dx = weights * dx
    weighted_dy = weights * dy
    
    mean_dx = np.sum(weighted_dx) / sum_weights  # Scalar
    mean_dy = np.sum(weighted_dy) / sum_weights  # Scalar
    
    # Compute weighted second moments
    # These are used to construct the covariance matrix
    weighted_dx_sq = weights * dx * dx
    weighted_dy_sq = weights * dy * dy
    weighted_dx_dy = weights * dx * dy
    
    mean_dx_sq = np.sum(weighted_dx_sq) / sum_weights  # Scalar
    mean_dy_sq = np.sum(weighted_dy_sq) / sum_weights  # Scalar
    mean_dx_dy = np.sum(weighted_dx_dy) / sum_weights  # Scalar
    
    # Construct the 2x2 covariance matrix
    # Cov(X,X) = E[X²] - E[X]²
    # Cov(X,Y) = E[XY] - E[X]E[Y]
    cov_matrix = np.array([
        [mean_dx_sq - mean_dx**2, mean_dx_dy - mean_dx * mean_dy],
        [mean_dx_dy - mean_dx * mean_dy, mean_dy_sq - mean_dy**2]
    ])
    
    # Compute eigenvalues of the covariance matrix
    try:
        eigenvalues = np.linalg.eigvals(cov_matrix)  # Shape: (2,)
    except np.linalg.LinAlgError:
        # Fallback if eigval computation fails
        return np.nan
    
    # Compute determinant as product of eigenvalues
    # det(Cov) = λ₁ * λ₂
    var_xy2 = eigenvalues[0] * eigenvalues[1]  # Scalar
    
    # Compute weighted mean squared distance
    weighted_dist_sq = weights * dist_squared
    mean_dist_sq = np.sum(weighted_dist_sq) / sum_weights  # Scalar
    
    # Numerical stability: use epsilon to prevent log(0)
    epsilon = 1e-10
    safe_mean_distance = np.maximum(mean_distance, epsilon)
    safe_var_xy2 = np.maximum(var_xy2, epsilon)
    
    # Compute entropy components:
    # LogE = 2 * 0.5 * log(mean_distance) + 2 * 0.5 * 0.5 * log(determinant)
    #      = log(mean_distance) + 0.5 * log(determinant)
    LogE = 2 * 0.5 * np.log(safe_mean_distance) + 2 * 0.5 * 0.5 * np.log(safe_var_xy2)
    
    # Return the entropy value
    # In the original MATLAB code, output = mean(LogE) where LogE is scalar
    output = LogE
    
    return float(output)


if __name__ == "__main__":
    """
    Simple test cases to verify the entropy function works correctly.
    """
    
    # Test 1: Single point at origin, platform at origin
    # Expected: Very small entropy (point coincides with goal)
    result1 = entropy([0], [0], 0, 0)
    print(f"Test 1 (point at platform): {result1}")
    
    # Test 2: Points distributed around platform
    x_test = [0, 1, -1, 0.5, -0.5]
    y_test = [0, 1, -1, 0.5, -0.5]
    result2 = entropy(x_test, y_test, 0, 0)
    print(f"Test 2 (distributed points): {result2}")
    
    # Test 3: Platform offset from points
    x_test = [1, 2, 3, 4, 5]
    y_test = [1, 2, 3, 4, 5]
    result3 = entropy(x_test, y_test, 10, 10)
    print(f"Test 3 (offset platform): {result3}")
    
    # Test 4: Empty array (should return NaN)
    result4 = entropy([], [], 0, 0)
    print(f"Test 4 (empty arrays): {result4}")
    
    # Test 5: Array-like inputs (lists converted to numpy)
    result5 = entropy([0, 1, 2], [0, 1, 2], 0, 0)
    print(f"Test 5 (list inputs): {result5}")
