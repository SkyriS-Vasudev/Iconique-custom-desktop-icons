import os
from PIL import Image
from backend.logging_config import logger

def _workspace_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_assets_dir():
    appdata = os.getenv('APPDATA')
    if appdata:
        assets_dir = os.path.join(appdata, 'Iconique', 'assets')
        try:
            os.makedirs(assets_dir, exist_ok=True)
            return assets_dir
        except OSError:
            logger.warning("AppData assets directory is not writable; falling back to workspace assets.")

    assets_dir = os.path.join(_workspace_root(), 'backend', 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    return assets_dir

def validate_image(file_path):
    """
    Validates if the file is a valid image and is a supported format.
    Supported formats: PNG, JPG, JPEG, WEBP.
    """
    if not os.path.exists(file_path):
        logger.error(f"Image validation failed: file does not exist at {file_path}")
        return False, "File does not exist."
        
    # Check extension
    _, ext = os.path.splitext(file_path.lower())
    if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
        logger.error(f"Image validation failed: unsupported extension {ext}")
        return False, f"Unsupported image format '{ext}'. Only PNG, JPG, JPEG, and WEBP are supported."
        
    try:
        with Image.open(file_path) as img:
            img.verify()  # verify integrity without loading full pixel data
        logger.debug(f"Image at {file_path} is valid.")
        return True, "Valid image."
    except Exception as e:
        logger.error(f"Image validation failed: invalid image format for {file_path}. Error: {e}")
        return False, "Invalid image file or file is corrupted."

def convert_to_ico(image_path, output_name=None):
    """
    Converts a PNG, JPG, or WEBP image into a standard multi-resolution Windows ICO file.
    Saves in the Iconique APPDATA assets folder.
    """
    is_valid, msg = validate_image(image_path)
    if not is_valid:
        raise ValueError(msg)
        
    assets_dir = get_assets_dir()
    if not output_name:
        base_name = os.path.basename(image_path)
        name_part, _ = os.path.splitext(base_name)
        output_name = f"{name_part}.ico"
    elif not output_name.lower().endswith('.ico'):
        output_name = f"{output_name}.ico"
        
    output_path = os.path.join(assets_dir, output_name)
    
    try:
        with Image.open(image_path) as img:
            # Ensure it is in RGBA mode to preserve transparency (especially for WEBP/PNG)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            # Standard ICO resolutions
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            
            # Save as multi-size ICO
            img.save(output_path, format="ICO", sizes=sizes)
            logger.info(f"Successfully converted {image_path} to ICO at {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to convert image to ICO: {e}")
        raise RuntimeError(f"Error during ICO generation: {str(e)}")

def generate_preview(image_path, output_name=None, size=(256, 256)):
    """
    Generates a resized PNG preview from any supported input image.
    Used for showing previews before applying a theme or custom upload.
    """
    is_valid, msg = validate_image(image_path)
    if not is_valid:
        raise ValueError(msg)
        
    assets_dir = get_assets_dir()
    if not output_name:
        base_name = os.path.basename(image_path)
        name_part, _ = os.path.splitext(base_name)
        output_name = f"{name_part}_preview.png"
    elif not output_name.lower().endswith('.png'):
        output_name = f"{output_name}_preview.png"
        
    output_path = os.path.join(assets_dir, output_name)
    
    try:
        with Image.open(image_path) as img:
            # Resize keeping aspect ratio or just pad it to a square
            img_ratio = img.width / img.height
            
            if img_ratio > 1:
                # Wide image
                new_width = size[0]
                new_height = int(size[0] / img_ratio)
            else:
                # Tall image
                new_height = size[1]
                new_width = int(size[1] * img_ratio)
                
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create transparent canvas and paste the resized image in center
            canvas = Image.new("RGBA", size, (0, 0, 0, 0))
            offset_x = (size[0] - new_width) // 2
            offset_y = (size[1] - new_height) // 2
            canvas.paste(resized, (offset_x, offset_y))
            
            canvas.save(output_path, format="PNG")
            logger.debug(f"Preview PNG generated for {image_path} at {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to generate preview PNG: {e}")
        raise RuntimeError(f"Error generating preview: {str(e)}")
