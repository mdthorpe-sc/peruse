#!/usr/bin/env python3
"""
Image tiling functionality for handling large screenshots.

This module provides functions to:
1. Detect oversized images that exceed Bedrock's dimension limits
2. Split large images into manageable tiles with overlap
3. Analyze tiles separately using Claude models
4. Combine results from multiple tiles intelligently  
5. Clean up temporary tile files

Addresses the ValidationException issue when screenshots exceed Bedrock's
maximum image dimensions (e.g., shortcut.com at 1920x9168 pixels).
"""

import os
import tempfile
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image
import uuid

# Import logging framework
from logging_config import get_logger


class ImageTilingError(Exception):
    """Custom exception for image tiling operations"""
    pass


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """
    Get the dimensions of an image file.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Tuple of (width, height) in pixels
        
    Raises:
        ImageTilingError: If image cannot be opened or read
    """
    logger = get_logger("image_tiling")
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            logger.debug(f"Image dimensions: {width}x{height} - {image_path}")
            return width, height
    except Exception as e:
        raise ImageTilingError(f"Could not read image dimensions from {image_path}: {e}")


def needs_tiling(image_path: str, max_height: int = 4000, max_width: int = 4096) -> bool:
    """
    Check if an image needs to be tiled due to size constraints.
    
    Args:
        image_path: Path to the image file
        max_height: Maximum allowed height in pixels (default: 4000)
        max_width: Maximum allowed width in pixels (default: 4096)
    
    Returns:
        True if image needs tiling, False otherwise
    """
    logger = get_logger("image_tiling")
    
    try:
        width, height = get_image_dimensions(image_path)
        needs_tiling_result = height > max_height or width > max_width
        
        if needs_tiling_result:
            logger.user_info(f"Image requires tiling: {width}x{height} exceeds {max_width}x{max_height}")
        
        return needs_tiling_result
    except ImageTilingError:
        # If we can't read the image, assume it doesn't need tiling
        logger.user_warning(f"Could not check image dimensions for {image_path}, assuming no tiling needed")
        return False


def tile_image(
    image_path: str, 
    tile_height: int = 3000, 
    overlap: int = 200,
    temp_dir: Optional[str] = None
) -> List[str]:
    """
    Split a large image into overlapping tiles.
    
    Args:
        image_path: Path to the image to tile
        tile_height: Maximum height of each tile in pixels (default: 3000)
        overlap: Overlap between tiles in pixels (default: 200)
        temp_dir: Directory for temporary files (default: system temp)
    
    Returns:
        List of paths to tile image files
        
    Raises:
        ImageTilingError: If tiling operation fails
    """
    logger = get_logger("image_tiling")
    
    try:
        width, height = get_image_dimensions(image_path)
        
        if height <= tile_height:
            # Image doesn't need tiling, return original
            logger.debug(f"Image {height}px tall, no tiling needed (max: {tile_height}px)")
            return [image_path]
        
        if temp_dir is None:
            temp_dir = tempfile.gettempdir()
        
        temp_dir_path = Path(temp_dir)
        temp_dir_path.mkdir(exist_ok=True)
        
        tiles = []
        image_id = str(uuid.uuid4())[:8]
        
        logger.operation_start(f"Tiling image {width}x{height} into {tile_height}px tiles with {overlap}px overlap")
        
        with Image.open(image_path) as img:
            y_offset = 0
            tile_index = 0
            
            while y_offset < height:
                # Calculate tile boundaries
                tile_start_y = y_offset
                tile_end_y = min(y_offset + tile_height, height)
                
                # Add overlap for non-final tiles
                if tile_end_y < height:
                    tile_end_y = min(tile_end_y + overlap, height)
                
                # Extract tile
                tile_img = img.crop((0, tile_start_y, width, tile_end_y))
                
                # Save tile
                tile_filename = f"tile_{image_id}_{tile_index:03d}_{tile_start_y}_{tile_end_y}.png"
                tile_path = temp_dir_path / tile_filename
                tile_img.save(tile_path)
                
                tiles.append(str(tile_path))
                
                logger.debug(f"Created tile {tile_index}: {tile_start_y}-{tile_end_y} ({tile_img.size[1]}px high)")
                
                # Move to next tile position (subtract overlap to avoid double-counting)
                y_offset += tile_height
                tile_index += 1
        
        logger.user_success(f"Created {len(tiles)} tiles from {width}x{height} image")
        return tiles
        
    except Exception as e:
        raise ImageTilingError(f"Failed to tile image {image_path}: {e}")


def analyze_tiled_image(
    baseline_tiles: List[str], 
    current_tiles: List[str], 
    url: str,
    claude_analyzer  # ScreenshotMonitor instance for Claude analysis
) -> Dict[str, Any]:
    """
    Analyze tiled images by comparing corresponding tiles.
    
    Args:
        baseline_tiles: List of baseline tile image paths
        current_tiles: List of current tile image paths  
        url: URL being analyzed
        claude_analyzer: ScreenshotMonitor instance with compare_with_claude method
    
    Returns:
        Combined analysis results from all tiles
        
    Raises:
        ImageTilingError: If analysis fails
    """
    logger = get_logger("image_tiling")
    
    if len(baseline_tiles) != len(current_tiles):
        raise ImageTilingError(
            f"Tile count mismatch: {len(baseline_tiles)} baseline vs {len(current_tiles)} current"
        )
    
    logger.operation_start(f"Analyzing {len(baseline_tiles)} tile pairs for {url}")
    
    tile_results = []
    
    for i, (baseline_tile, current_tile) in enumerate(zip(baseline_tiles, current_tiles)):
        try:
            logger.debug(f"Analyzing tile {i+1}/{len(baseline_tiles)}")
            
            # Use the existing Claude analysis from ScreenshotMonitor
            result = claude_analyzer.compare_with_claude(baseline_tile, current_tile, url)
            
            # Add tile metadata to the result
            result["tile_info"] = {
                "tile_index": i,
                "baseline_path": baseline_tile,
                "current_path": current_tile
            }
            
            tile_results.append(result)
            
        except Exception as e:
            logger.user_error(f"Failed to analyze tile {i}: {e}")
            # Add error result so we don't lose track of the tile
            error_result = {
                "error": str(e),
                "has_changes": True,
                "severity": "unknown",
                "summary": f"Analysis failed for tile {i}",
                "tile_info": {
                    "tile_index": i,
                    "baseline_path": baseline_tile,
                    "current_path": current_tile
                }
            }
            tile_results.append(error_result)
    
    # Combine results from all tiles
    combined_result = combine_tile_results(tile_results)
    
    logger.operation_complete(f"Completed analysis of {len(baseline_tiles)} tiles")
    return combined_result


def combine_tile_results(tile_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine analysis results from multiple tiles into a single result.
    
    Args:
        tile_results: List of analysis results from individual tiles
    
    Returns:
        Combined analysis result
    """
    logger = get_logger("image_tiling")
    
    if not tile_results:
        return {
            "has_changes": False,
            "severity": "none",
            "summary": "No tiles to analyze",
            "changes_detected": [],
            "availability_status": "unknown",
            "recommendations": [],
            "tile_count": 0
        }
    
    # Severity hierarchy for escalation
    severity_levels = {
        "none": 0,
        "minor": 1, 
        "moderate": 2,
        "major": 3,
        "critical": 4,
        "unknown": 5  # Treat unknown as highest to be safe
    }
    
    # Collect data from all tiles
    has_any_changes = False
    max_severity = "none"
    all_changes = []
    all_recommendations = []
    error_count = 0
    availability_statuses = []
    
    for i, result in enumerate(tile_results):
        # Check for errors
        if "error" in result:
            error_count += 1
            logger.user_warning(f"Tile {i} had analysis error: {result['error']}")
        
        # Aggregate changes
        if result.get("has_changes", False):
            has_any_changes = True
        
        # Track highest severity
        tile_severity = result.get("severity", "unknown")
        if severity_levels.get(tile_severity, 0) > severity_levels.get(max_severity, 0):
            max_severity = tile_severity
        
        # Collect changes (add tile location info)
        tile_changes = result.get("changes_detected", [])
        for change in tile_changes:
            # Add tile information to location
            tile_info = result.get("tile_info", {})
            tile_index = tile_info.get("tile_index", i)
            
            change_copy = change.copy()
            original_location = change_copy.get("location", "")
            change_copy["location"] = f"Tile {tile_index + 1}: {original_location}"
            all_changes.append(change_copy)
        
        # Collect recommendations
        tile_recommendations = result.get("recommendations", [])
        all_recommendations.extend(tile_recommendations)
        
        # Track availability
        availability = result.get("availability_status")
        if availability:
            availability_statuses.append(availability)
    
    # Determine overall availability
    if not availability_statuses:
        overall_availability = "unknown"
    elif "unavailable" in availability_statuses:
        overall_availability = "unavailable"
    elif "partially_available" in availability_statuses:
        overall_availability = "partially_available"
    elif "error" in availability_statuses:
        overall_availability = "error"
    else:
        overall_availability = "available"
    
    # Generate summary
    tile_count = len(tile_results)
    if error_count > 0:
        error_summary = f" ({error_count} tiles had analysis errors)"
    else:
        error_summary = ""
    
    if has_any_changes:
        change_count = len(all_changes)
        summary = f"Analysis of {tile_count} tiles found {change_count} changes{error_summary}"
    else:
        summary = f"Analysis of {tile_count} tiles found no changes{error_summary}"
    
    # Remove duplicate recommendations
    unique_recommendations = list(set(all_recommendations))
    
    combined_result = {
        "has_changes": has_any_changes,
        "severity": max_severity,
        "summary": summary,
        "changes_detected": all_changes,
        "availability_status": overall_availability,
        "recommendations": unique_recommendations,
        "tile_count": tile_count,
        "tiles_with_errors": error_count
    }
    
    logger.debug(f"Combined {tile_count} tile results: {max_severity} severity, {len(all_changes)} changes")
    return combined_result


def cleanup_tiles(tile_paths: List[str]) -> None:
    """
    Clean up temporary tile files.
    
    Args:
        tile_paths: List of tile file paths to delete
    """
    logger = get_logger("image_tiling")
    
    cleaned_count = 0
    error_count = 0
    
    for tile_path in tile_paths:
        try:
            tile_file = Path(tile_path)
            if tile_file.exists():
                tile_file.unlink()
                cleaned_count += 1
                logger.debug(f"Cleaned up tile: {tile_path}")
        except Exception as e:
            error_count += 1
            logger.user_warning(f"Failed to clean up tile {tile_path}: {e}")
    
    if cleaned_count > 0:
        logger.debug(f"Cleaned up {cleaned_count} tile files")
    
    if error_count > 0:
        logger.user_warning(f"Failed to clean up {error_count} tile files")


def get_optimal_tile_settings(image_width: int, image_height: int) -> Dict[str, int]:
    """
    Calculate optimal tiling settings based on image dimensions.
    
    Args:
        image_width: Width of the image in pixels
        image_height: Height of the image in pixels
    
    Returns:
        Dictionary with recommended tile_height and overlap values
    """
    # Base settings
    base_tile_height = 3000
    base_overlap = 200
    
    # Adjust based on image characteristics
    if image_height <= 4000:
        # Small enough for single tile
        return {"tile_height": image_height, "overlap": 0}
    elif image_height <= 8000:
        # Medium image - use larger tiles
        return {"tile_height": 3500, "overlap": 250}
    else:
        # Very large image - use standard settings
        return {"tile_height": base_tile_height, "overlap": base_overlap}


def estimate_tile_count(image_path: str, tile_height: int = 3000) -> int:
    """
    Estimate how many tiles an image will produce.
    
    Args:
        image_path: Path to the image
        tile_height: Height of each tile
    
    Returns:
        Estimated number of tiles
    """
    try:
        _, height = get_image_dimensions(image_path)
        return max(1, (height + tile_height - 1) // tile_height)  # Ceiling division
    except ImageTilingError:
        return 1 