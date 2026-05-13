#!/usr/bin/env python3
"""Create a professional PassPort icon"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=256):
    """Create a professional password manager icon"""
    
    # Create base image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factor
    s = size / 256
    
    # Background - dark rounded square
    margin = 10
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(30 * s),
        fill=(30, 30, 50)  # Dark navy
    )
    
    # Inner gradient effect - lighter center
    inner_margin = 25
    draw.rounded_rectangle(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        radius=int(25 * s),
        fill=(52, 73, 94)  # Steel blue
    )
    
    # Shield outline
    shield_top = int(size * 0.25)
    shield_bottom = int(size * 0.75)
    shield_left = int(size * 0.25)
    shield_right = int(size * 0.75)
    
    # Shield shape (simplified)
    shield_points = [
        (shield_left, shield_top + int(size * 0.15)),      # Left top
        (size // 2, shield_top),                             # Top center
        (shield_right, shield_top + int(size * 0.15)),      # Right top
        (shield_right, shield_top + int(size * 0.35)),      # Right middle
        (size // 2, shield_bottom),                          # Bottom point
        (shield_left, shield_top + int(size * 0.35)),       # Left middle
    ]
    
    # Draw white shield
    draw.polygon(shield_points, fill=(255, 255, 255, 230))
    
    # Keyhole circle
    key_cx = size // 2
    key_cy = size // 2 - int(15 * s)
    key_radius = int(20 * s)
    
    # Keyhole (simplified as circle + rectangle)
    draw.ellipse(
        [key_cx - key_radius, key_cy - key_radius,
         key_cx + key_radius, key_cy + key_radius],
        fill=(52, 73, 94)
    )
    
    # Keyhole stem
    stem_width = int(12 * s)
    draw.rectangle(
        [key_cx - stem_width // 2, key_cy,
         key_cx + stem_width // 2, key_cy + int(35 * s)],
        fill=(52, 73, 94)
    )
    
    # Add subtle border
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(30 * s),
        outline=(255, 255, 255, 50),
        width=int(2 * s)
    )
    
    # Save icons in multiple sizes
    icon_dir = 'icons'
    os.makedirs(icon_dir, exist_ok=True)
    
    # Save main icon
    icon_path = f'{icon_dir}/passport.png'
    img.save(icon_path, 'PNG')
    print(f"✅ Created {icon_path} ({size}x{size})")
    
    # Create smaller sizes
    sizes = [16, 22, 24, 32, 48, 64, 96, 128]
    for icon_size in sizes:
        resized = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        size_path = f'{icon_dir}/passport-{icon_size}.png'
        resized.save(size_path, 'PNG')
    
    # Also save as SVG-like PNG for system tray
    tray_icon = img.resize((24, 24), Image.Resampling.LANCZOS)
    tray_icon.save(f'{icon_dir}/passport-tray.png', 'PNG')
    
    print(f"✅ Created icons in {icon_dir}/ directory")
    print(f"   Main icon: {icon_path}")
    print(f"   Sizes: {', '.join(str(s) for s in sizes)}")

if __name__ == "__main__":
    create_icon()
