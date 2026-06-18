from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops

def generate_glossy_icon():
    size = 512
    # Create base image with transparency
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # 1. Soft Drop Shadow under the entire icon
    shadow_mask = Image.new("L", (size, size), 0)
    shadow_draw = ImageDraw.Draw(shadow_mask)
    shadow_draw.rounded_rectangle([36, 44, 476, 484], radius=110, fill=255)
    shadow = Image.new("RGBA", (size, size), (15, 23, 42, 120))
    shadow_layer = Image.composite(shadow, Image.new("RGBA", (size, size), (0, 0, 0, 0)), shadow_mask)
    shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(16))
    base.alpha_composite(shadow_blurred)
    
    # 2. Main Icon Body Mask
    body_mask = Image.new("L", (size, size), 0)
    body_mask_draw = ImageDraw.Draw(body_mask)
    body_mask_draw.rounded_rectangle([32, 32, 480, 480], radius=110, fill=255)
    
    # Background Gradient: Dark Steel Blue to Obsidian (Classic early-2010s depth)
    bg = Image.new("RGBA", (size, size))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        ratio = y / size
        # Smooth interpolation
        r = int(24 + (15 - 24) * ratio)
        g = int(34 + (23 - 34) * ratio)
        b = int(54 + (42 - 54) * ratio)
        bg_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        
    icon_body = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    icon_body = Image.composite(bg, icon_body, body_mask)
    
    # 3. 3D Metallic Silver Bevel & Border
    border_draw = ImageDraw.Draw(icon_body)
    # Outer silver/steel rim
    border_draw.rounded_rectangle([32, 32, 480, 480], radius=110, outline=(170, 180, 195, 255), width=7)
    # Inner light reflection bevel
    border_draw.rounded_rectangle([38, 38, 474, 474], radius=104, outline=(241, 245, 249, 120), width=2)
    # Dark outline shadow
    border_draw.rounded_rectangle([31, 31, 481, 481], radius=111, outline=(15, 23, 42, 160), width=2)
    
    # 4. Sleek Silver Serif Monogram 'I' in the Center (Skeuomorphic & Dimensional)
    logo_mask = Image.new("L", (size, size), 0)
    logo_draw = ImageDraw.Draw(logo_mask)
    
    # Draw vertical stem of 'I'
    logo_draw.rounded_rectangle([238, 195, 274, 395], radius=18, fill=255)
    # Draw circular dot
    logo_draw.ellipse([238, 115, 274, 151], fill=255)
    # Classy serif wing (Top)
    logo_draw.rounded_rectangle([206, 195, 306, 220], radius=6, fill=255)
    # Classy serif wing (Bottom)
    logo_draw.rounded_rectangle([196, 370, 316, 395], radius=6, fill=255)
    
    # Draw logo drop shadow inside the body
    logo_shadow = Image.new("RGBA", (size, size), (15, 23, 42, 180))
    logo_shadow_layer = Image.composite(logo_shadow, Image.new("RGBA", (size, size), (0, 0, 0, 0)), logo_mask)
    logo_shadow_blurred = logo_shadow_layer.filter(ImageFilter.GaussianBlur(8))
    # Shift shadow down slightly
    shadow_shifted = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_shifted.paste(logo_shadow_blurred, (0, 5))
    icon_body.alpha_composite(shadow_shifted)
    
    # Fill logo with chrome metallic gradient (Silver to White highlight)
    logo_fill = Image.new("RGBA", (size, size))
    lf_draw = ImageDraw.Draw(logo_fill)
    for y in range(size):
        ratio = y / size
        val = int(210 + (255 - 210) * (1.0 - ratio))
        lf_draw.line([(0, y), (size, y)], fill=(val, val, val + 8, 255))
        
    logo_body = Image.composite(logo_fill, Image.new("RGBA", (size, size), (0, 0, 0, 0)), logo_mask)
    
    # Subtle inner highlights on the logo shape
    logo_border = ImageDraw.Draw(logo_body)
    logo_border.rounded_rectangle([238, 195, 274, 395], radius=18, outline=(255, 255, 255, 120), width=2)
    logo_border.ellipse([238, 115, 274, 151], outline=(255, 255, 255, 120), width=2)
    logo_border.rounded_rectangle([206, 195, 306, 220], radius=6, outline=(255, 255, 255, 120), width=2)
    logo_border.rounded_rectangle([196, 370, 316, 395], radius=6, outline=(255, 255, 255, 120), width=2)
    
    icon_body.alpha_composite(logo_body)
    
    # 5. Glossy Glass Overlay Reflection (iOS 4/6 signature style)
    gloss_mask = Image.new("L", (size, size), 0)
    gloss_draw = ImageDraw.Draw(gloss_mask)
    # Ellipse shape cutting across top-half
    gloss_draw.ellipse([-120, -240, 632, 250], fill=255)
    
    # Intersect with the main squircle body mask
    intersect_mask = ImageChops.multiply(body_mask, gloss_mask)
    
    # Generate white glossy gradient fade
    gloss_grad = Image.new("RGBA", (size, size))
    gg_draw = ImageDraw.Draw(gloss_grad)
    for y in range(size):
        ratio = y / 250
        if ratio > 1.0:
            ratio = 1.0
        alpha = int(85 * (1.0 - ratio * 0.85))  # High sheen fading downwards
        gg_draw.line([(0, y), (size, y)], fill=(255, 255, 255, alpha))
        
    gloss_final = Image.composite(gloss_grad, Image.new("RGBA", (size, size), (0, 0, 0, 0)), intersect_mask)
    icon_body.alpha_composite(gloss_final)
    
    # Merge onto base
    base.alpha_composite(icon_body)
    return base

def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "frontend" / "src" / "assets" / "hero.png"
    output = root / "packaging" / "iconique.ico"

    # Generate the beautiful icon image
    icon_image = generate_glossy_icon()
    
    # Ensure folders exist
    source.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Save PNG version for Web UI / Hero image
    icon_image.save(source, format="PNG")
    
    # Save standard Windows multi-resolution ICO file
    icon_image.save(
        output,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("Successfully generated classic glossy icon formats.")

if __name__ == "__main__":
    main()
