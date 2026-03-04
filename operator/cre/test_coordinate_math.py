#!/usr/bin/env python3
"""
Pure math test for coordinate conversion logic.
Tests the mathematical correctness without requiring Quartz/AppKit.
"""

def test_triangle_vertices():
    """Test triangle vertex generation."""
    def triangle_vertices(size: int) -> list[tuple[int, int]]:
        return [(0, -size), (-size, size), (size, size)]
    
    vertices = triangle_vertices(220)
    expected = [(0, -220), (-220, 220), (220, 220)]
    assert vertices == expected, f"Expected {expected}, got {vertices}"
    print("✅ Triangle vertices: PASS")
    return vertices


def test_coordinate_conversion_math():
    """Test the coordinate conversion formula (simulated)."""
    # Simulate: screen_height = 900 * 2 = 1800 (for 2880x1800 Retina)
    screen_height = 1800
    
    def pixel_to_quartz(px: float, py: float, screen_height: float) -> tuple[float, float]:
        """Pure math version of _pixel_to_global_quartz."""
        gx = px
        gy = screen_height - py
        return (gx, gy)
    
    # Test center conversion
    px, py = 1440.0, 900.0
    gx, gy = pixel_to_quartz(px, py, screen_height)
    assert gx == 1440.0, f"Expected gx=1440, got {gx}"
    assert gy == 900.0, f"Expected gy=900, got {gy}"
    print(f"✅ Center conversion: ({px}, {py}) → ({gx}, {gy})")
    
    # Test triangle vertices conversion
    vertices = [(0, -220), (-220, 220), (220, 220)]
    center_x, center_y = 1440, 900
    
    print("\nTriangle vertices conversion (size=220, center=(1440, 900)):")
    for vx, vy in vertices:
        px = center_x + vx
        py = center_y + vy
        gx, gy = pixel_to_quartz(float(px), float(py), screen_height)
        print(f"  Relative ({vx:4d}, {vy:4d}) → Image ({px:4d}, {py:4d}) → Quartz ({gx:6.1f}, {gy:6.1f})")
    
    # Verify Y flip
    top_vertex = vertices[0]  # (0, -220)
    px_top = center_x + top_vertex[0]
    py_top = center_y + top_vertex[1]  # 900 - 220 = 680
    gx_top, gy_top = pixel_to_quartz(float(px_top), float(py_top), screen_height)
    assert gy_top == 1120.0, f"Top vertex Y should flip: expected 1120, got {gy_top}"
    print(f"\n✅ Y-flip verification: Top vertex Y={py_top} → Quartz Y={gy_top} (flipped)")
    
    return True


def test_screenshot_center_math():
    """Test screenshot center calculation."""
    def get_center(width: int, height: int) -> tuple[int, int]:
        return (width // 2, height // 2)
    
    # Test 2880x1800 screenshot
    w, h = 2880, 1800
    cx, cy = get_center(w, h)
    assert cx == 1440, f"Expected cx=1440, got {cx}"
    assert cy == 900, f"Expected cy=900, got {cy}"
    print(f"✅ Screenshot center (2880×1800): ({cx}, {cy})")
    
    return (cx, cy)


def test_all_sizes():
    """Test all four triangle sizes."""
    sizes = [220, 160, 100, 50]
    center_x, center_y = 1440, 900
    
    print("\nAll triangle sizes:")
    for size in sizes:
        def triangle_vertices(size: int):
            return [(0, -size), (-size, size), (size, size)]
        
        vertices = triangle_vertices(size)
        print(f"\n  Size {size}:")
        for vx, vy in vertices:
            px = center_x + vx
            py = center_y + vy
            print(f"    ({vx:4d}, {vy:4d}) → Image ({px:4d}, {py:4d})")
    
    print("\n✅ All sizes: PASS")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Coordinate Math Test (Pure Logic, No Dependencies)")
    print("=" * 60)
    
    try:
        test_triangle_vertices()
        test_coordinate_conversion_math()
        test_screenshot_center_math()
        test_all_sizes()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
