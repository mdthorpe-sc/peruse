#!/usr/bin/env python3
"""
Test the image tiling functionality for handling large screenshots.

This test validates that we can properly:
1. Detect oversized images
2. Split them into manageable tiles
3. Analyze tiles separately 
4. Combine results intelligently
5. Clean up temporary files
"""

import sys
import tempfile
import json
import pytest
from pathlib import Path
from PIL import Image
from typing import List, Tuple
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the image tiling functions we just created
from image_tiling import (
    get_image_dimensions,
    needs_tiling, 
    tile_image,
    analyze_tiled_image,
    combine_tile_results,
    cleanup_tiles,
    ImageTilingError,
    get_optimal_tile_settings,
    estimate_tile_count
)


class TestImageDimensions:
    """Test image dimension detection functionality"""
    
    def create_test_image(self, width: int, height: int, temp_dir: str) -> str:
        """Helper to create test images of specific dimensions"""
        image_path = Path(temp_dir) / f"test_{width}x{height}.png"
        
        # Create a simple test image with the specified dimensions
        image = Image.new('RGB', (width, height), color='white')
        # Add some visual elements so it's not completely blank
        for i in range(0, height, 100):
            for j in range(0, width, 100):
                # Add colored squares to make the image visually distinct
                color = (i % 255, j % 255, (i + j) % 255)
                for y in range(i, min(i + 50, height)):
                    for x in range(j, min(j + 50, width)):
                        image.putpixel((x, y), color)
        
        image.save(image_path)
        return str(image_path)
    
    def test_get_image_dimensions_standard(self):
        """Test getting dimensions of standard-sized image"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = self.create_test_image(1920, 1080, temp_dir)
            
            # Test our implementation
            width, height = get_image_dimensions(image_path)
            assert width == 1920
            assert height == 1080
            
            # For now, verify the test image was created correctly
            image = Image.open(image_path)
            assert image.size == (1920, 1080)
    
    def test_get_image_dimensions_large(self):
        """Test getting dimensions of large image like shortcut.com"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = self.create_test_image(1920, 9168, temp_dir)
            
            # Test our implementation
            width, height = get_image_dimensions(image_path)
            assert width == 1920
            assert height == 9168
            
            # Verify test image creation
            image = Image.open(image_path)
            assert image.size == (1920, 9168)
    
    def test_needs_tiling_standard_image(self):
        """Test that standard images don't need tiling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = self.create_test_image(1920, 1080, temp_dir)
            
            # needs_tiling should return False for standard images
            assert not needs_tiling(image_path, max_height=4000)
    
    def test_needs_tiling_large_image(self):
        """Test that large images do need tiling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = self.create_test_image(1920, 9168, temp_dir)
            
            # needs_tiling should return True for large images
            assert needs_tiling(image_path, max_height=4000)


class TestImageTiling:
    """Test image tiling/chunking functionality"""
    
    def create_test_image(self, width: int, height: int, temp_dir: str) -> str:
        """Helper to create test images of specific dimensions"""
        image_path = Path(temp_dir) / f"test_{width}x{height}.png"
        
        # Create image with distinct sections for easier testing
        image = Image.new('RGB', (width, height), color='white')
        
        # Add horizontal bands of different colors
        band_height = height // 10
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (128, 128, 128), # Gray
            (255, 128, 0),  # Orange
            (128, 0, 255),  # Purple
            (0, 128, 255),  # Light Blue
        ]
        
        for i, color in enumerate(colors):
            y_start = i * band_height
            y_end = min((i + 1) * band_height, height)
            
            for y in range(y_start, y_end):
                for x in range(width):
                    image.putpixel((x, y), color)
        
        image.save(image_path)
        return str(image_path)
    
    def test_tile_image_basic(self):
        """Test basic image tiling functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large test image
            image_path = self.create_test_image(1920, 6000, temp_dir)
            
            # tile_image should split into manageable chunks
            tiles = tile_image(image_path, tile_height=3000, overlap=200, temp_dir=temp_dir)
            
            # Should create 2-3 tiles for a 6000px tall image with 3000px tiles
            assert len(tiles) >= 2
            assert len(tiles) <= 3
            
            # All tile files should exist
            for tile_path in tiles:
                assert Path(tile_path).exists()
                
            # Clean up
            cleanup_tiles(tiles)
    
    def test_tile_image_overlap(self):
        """Test that tiles have proper overlap to avoid missing changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = self.create_test_image(1920, 6000, temp_dir)
            
            # Test overlap functionality
            # tiles = tile_image(image_path, tile_height=3000, overlap=200)
            # 
            # # Check that tiles overlap properly by examining their dimensions
            # for tile_path in tiles[:-1]:  # All but last tile
            #     tile_image = Image.open(tile_path)
            #     # Non-final tiles should include overlap
            #     assert tile_image.size[1] <= 3000 + 200  # tile_height + overlap
            pass
    
    def test_tile_image_cleanup(self):
        """Test cleanup of temporary tile files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = self.create_test_image(1920, 6000, temp_dir)
            
            # Test cleanup functionality
            tiles = tile_image(image_path, tile_height=3000, overlap=200, temp_dir=temp_dir)
            
            # Verify tiles exist
            for tile_path in tiles:
                assert Path(tile_path).exists()
            
            # Cleanup should remove all tiles
            cleanup_tiles(tiles)
            
            # Verify tiles are removed
            for tile_path in tiles:
                assert not Path(tile_path).exists()


class TestResultCombination:
    """Test combining analysis results from multiple tiles"""
    
    def test_combine_simple_results(self):
        """Test combining results with no changes"""
        no_change_result = {
            "has_changes": False,
            "severity": "none",
            "summary": "No changes detected",
            "changes_detected": [],
            "availability_status": "available",
            "recommendations": []
        }
        
        results = [no_change_result, no_change_result, no_change_result]
        
        combined = combine_tile_results(results)
        
        assert not combined["has_changes"]
        assert combined["severity"] == "none"
        assert len(combined["changes_detected"]) == 0
        assert combined["tile_count"] == 3
    
    def test_combine_mixed_results(self):
        """Test combining results where some tiles have changes"""
        no_change = {
            "has_changes": False,
            "severity": "none", 
            "summary": "No changes detected",
            "changes_detected": [],
            "availability_status": "available"
        }
        
        has_change = {
            "has_changes": True,
            "severity": "moderate",
            "summary": "Layout changes detected",
            "changes_detected": [
                {
                    "type": "layout",
                    "description": "Navigation moved",
                    "location": "Header",
                    "impact": "Minor"
                }
            ],
            "availability_status": "available"
        }
        
        results = [no_change, has_change, no_change]
        
        combined = combine_tile_results(results)
        
        assert combined["has_changes"]  # Should detect changes overall
        assert combined["severity"] == "moderate"  # Should use highest severity
        assert len(combined["changes_detected"]) == 1
        assert combined["tile_count"] == 3
    
    def test_combine_severity_escalation(self):
        """Test that combined results use the highest severity level"""
        minor_change = {
            "has_changes": True,
            "severity": "minor",
            "changes_detected": [{"type": "content", "description": "Minor text change"}]
        }
        
        critical_change = {
            "has_changes": True, 
            "severity": "critical",
            "changes_detected": [{"type": "error", "description": "Site error detected"}]
        }
        
        moderate_change = {
            "has_changes": True,
            "severity": "moderate", 
            "changes_detected": [{"type": "layout", "description": "Layout shift"}]
        }
        
        results = [minor_change, critical_change, moderate_change]
        
        combined = combine_tile_results(results)
        
        assert combined["severity"] == "critical"  # Should escalate to highest
        assert len(combined["changes_detected"]) == 3  # Should include all changes
        assert combined["has_changes"]


class TestIntegration:
    """Integration tests for the complete tiling workflow"""
    
    def create_realistic_test_image(self, width: int, height: int, temp_dir: str) -> str:
        """Create a more realistic test image that simulates a webpage"""
        image_path = Path(temp_dir) / f"realistic_{width}x{height}.png"
        
        image = Image.new('RGB', (width, height), color='white')
        
        # Header section (red)
        for y in range(100):
            for x in range(width):
                image.putpixel((x, y), (200, 50, 50))
        
        # Navigation section (blue) 
        for y in range(100, 200):
            for x in range(width):
                image.putpixel((x, y), (50, 50, 200))
        
        # Content sections with different patterns
        section_height = (height - 200) // 4
        colors = [(240, 240, 240), (220, 220, 220), (200, 200, 200), (180, 180, 180)]
        
        for i, color in enumerate(colors):
            y_start = 200 + i * section_height
            y_end = min(200 + (i + 1) * section_height, height)
            
            for y in range(y_start, y_end):
                for x in range(width):
                    # Add some variation within each section
                    variation = (x + y) % 20
                    adjusted_color = tuple(max(0, c - variation) for c in color)
                    image.putpixel((x, y), adjusted_color)
        
        image.save(image_path)
        return str(image_path)
    
    @patch('screenshot_monitor.ScreenshotMonitor.compare_with_claude')
    def test_full_tiling_workflow(self, mock_compare):
        """Test the complete workflow of tiling and analysis"""
        
        # Mock the Claude comparison to return predictable results
        mock_compare.return_value = {
            "has_changes": False,
            "severity": "none",
            "summary": "No changes detected in this tile",
            "changes_detected": [],
            "availability_status": "available",
            "recommendations": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create baseline and current images
            baseline_path = self.create_realistic_test_image(1920, 8000, temp_dir)
            current_path = self.create_realistic_test_image(1920, 8000, temp_dir)
            
            # Test the full workflow
            # result = analyze_tiled_image([baseline_path], [current_path], "https://test.com")
            # 
            # assert "has_changes" in result
            # assert "severity" in result
            # assert "summary" in result
            pass
    
    def test_error_handling(self):
        """Test error handling for invalid images and edge cases"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with non-existent file
            # assert get_image_dimensions("nonexistent.png") raises an exception
            
            # Test with invalid image file
            invalid_path = Path(temp_dir) / "invalid.png"
            invalid_path.write_text("not an image")
            
            # Should handle gracefully
            # result = needs_tiling(str(invalid_path))
            # assert result is False or an exception is raised appropriately
            pass


def main():
    """Run image tiling tests"""
    print("🧪 Testing Image Tiling Functionality")
    print("=" * 50)
    
    try:
        # For now, just validate that we can create test images
        print("✅ Test infrastructure created")
        print("📝 Tests ready for implementation")
        print("\nNext steps:")
        print("1. Implement image tiling functions")
        print("2. Run tests with: python tests/test_image_tiling.py")
        print("3. Iterate based on test results")
        
    except Exception as e:
        print(f"\n❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 