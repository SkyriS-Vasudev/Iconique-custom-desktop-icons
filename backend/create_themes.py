import os
import json
from PIL import Image, ImageDraw, ImageFont

def draw_icon(theme_name, app_name, bg_color, fg_color, shape_type):
    """
    Draws a beautiful high-resolution (256x256) icon using Pillow.
    """
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Background drawing
    if shape_type == "rounded_rect":
        draw.rounded_rectangle([16, 16, 240, 240], radius=48, fill=bg_color)
    elif shape_type == "circle":
        draw.ellipse([16, 16, 240, 240], fill=bg_color)
    elif shape_type == "cyber_shield":
        # Draw a futuristic polygon for cyberpunk
        draw.polygon([(128, 16), (240, 80), (240, 200), (128, 240), (16, 200), (16, 80)], fill=bg_color)
    elif shape_type == "pixel_box":
        # Draw pixelated box (retro style)
        draw.rectangle([16, 16, 240, 240], fill=bg_color, width=8, outline=fg_color)
    else:
        # Default rect
        draw.rectangle([16, 16, 240, 240], fill=bg_color)
        
    # 2. Draw application initials or symbolic shape in the center
    initials = "".join([w[0] for w in app_name.split() if w])[:2].upper()
    
    # Try to load a clean default font or fallback
    try:
        # On Windows, Arial is always available
        font = ImageFont.truetype("arial.ttf", 96)
    except IOError:
        font = ImageFont.load_default()
        
    # Calculate text position using textbbox (Pillow 10+)
    try:
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older Pillow
        text_w, text_h = draw.textsize(initials, font=font)
        
    text_x = (256 - text_w) // 2
    text_y = (256 - text_h) // 2 - 10  # adjust slightly upward for visual balance
    
    # Draw simple logo shapes for common apps to make them look custom
    if "Chrome" in app_name:
        # Draw concentric rings
        draw.ellipse([64, 64, 192, 192], outline=fg_color, width=12)
        draw.ellipse([96, 96, 160, 160], fill=fg_color)
    elif "Code" in app_name or "VS" in app_name:
        # Draw chevron-like shape < >
        draw.line([(80, 80), (40, 128), (80, 176)], fill=fg_color, width=16, joint="round")
        draw.line([(176, 80), (216, 128), (176, 176)], fill=fg_color, width=16, joint="round")
        draw.line([(140, 60), (116, 196)], fill=fg_color, width=12)
    elif "Edge" in app_name:
        # Draw wave/crest shape
        draw.arc([60, 60, 196, 196], 45, 315, fill=fg_color, width=16)
        draw.ellipse([110, 110, 146, 146], fill=fg_color)
    elif "Git" in app_name:
        # Draw Git branch diamond / nodes
        draw.line([(128, 60), (128, 196)], fill=fg_color, width=12)
        draw.ellipse([112, 60, 144, 92], fill=fg_color)
        draw.line([(128, 128), (180, 180)], fill=fg_color, width=12)
        draw.ellipse([164, 164, 196, 196], fill=fg_color)
        draw.ellipse([112, 164, 144, 196], fill=fg_color)
    else:
        # Draw text initials
        draw.text((text_x, text_y), initials, fill=fg_color, font=font)
        
    # 3. Add inner glowing border for premium feel
    if theme_name == "Cyberpunk":
        draw.rounded_rectangle([20, 20, 236, 236], radius=44, outline=(255, 0, 128, 255), width=4)
        
    return img

def create_themes():
    # Workspace themes folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    themes_root = os.path.join(base_dir, 'Theme Packs')
    os.makedirs(themes_root, exist_ok=True)
    
    # Theme configuration templates
    theme_templates = [
        {
            "name": "Cyberpunk",
            "author": "Iconique Team",
            "description": "Neon grids and glowing vectors from the future.",
            "category": "Sci-Fi",
            "bg_color": (15, 15, 25, 255),
            "fg_color": (0, 240, 255, 255),  # Neon Cyan
            "shape": "cyber_shield"
        },
        {
            "name": "Minimalist",
            "author": "SleekDesigns",
            "description": "Pure black and white flat icons for clean workspaces.",
            "category": "Minimalist",
            "bg_color": (245, 245, 247, 255),  # Off-white
            "fg_color": (20, 20, 20, 255),     # Dark gray
            "shape": "rounded_rect"
        },
        {
            "name": "Retro Gaming",
            "author": "ArcadeHero",
            "description": "8-bit inspired grid layouts and pixel styling.",
            "category": "Retro",
            "bg_color": (16, 0, 43, 255),      # Deep purple
            "fg_color": (255, 190, 11, 255),    # Golden yellow
            "shape": "pixel_box"
        },
        {
            "name": "Studio Ghibli",
            "author": "NatureChild",
            "description": "Soft pastel tones and organic rounded designs.",
            "category": "Pastel",
            "bg_color": (204, 227, 222, 255),   # Sage green
            "fg_color": (118, 146, 140, 255),   # Dark sage
            "shape": "circle"
        },
        {
            "name": "Pokemon",
            "author": "PalletTown",
            "description": "Gotta custom 'em all! Pokéball themed styling.",
            "category": "Gaming",
            "bg_color": (230, 57, 70, 255),     # Red
            "fg_color": (241, 250, 238, 255),    # White
            "shape": "circle"
        },
        {
            "name": "Dark Academia",
            "author": "OxfordScholar",
            "description": "Rich mahogany tones, leather textures, and brass trims.",
            "category": "Vintage",
            "bg_color": (44, 34, 30, 255),      # Dark brown
            "fg_color": (224, 169, 109, 255),   # Warm gold
            "shape": "rounded_rect"
        }
    ]
    
    apps = [
        "Google Chrome",
        "Visual Studio Code",
        "Microsoft Edge",
        "Git Bash",
        "AutoCAD 2021 - English",
        "Roblox Player"
    ]
    
    for t in theme_templates:
        theme_dir = os.path.join(themes_root, t["name"])
        os.makedirs(theme_dir, exist_ok=True)
        
        # Mapping
        icon_mapping = {}
        for app in apps:
            safe_app_name = "".join([c if c.isalnum() else '_' for c in app])
            filename = f"{safe_app_name.lower()}.ico"
            icon_mapping[app] = filename
            
            # Generate ICO file
            ico_path = os.path.join(theme_dir, filename)
            img = draw_icon(t["name"], app, t["bg_color"], t["fg_color"], t["shape"])
            
            # Save ICO with standard resolutions
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(ico_path, format="ICO", sizes=sizes)
            
        # Create theme.json
        theme_json = {
            "name": t["name"],
            "author": t["author"],
            "description": t["description"],
            "category": t["category"],
            "icons": icon_mapping
        }
        
        with open(os.path.join(theme_dir, "theme.json"), 'w', encoding='utf-8') as f:
            json.dump(theme_json, f, indent=2)
            
        print(f"Created theme pack: {t['name']}")

if __name__ == "__main__":
    create_themes()
