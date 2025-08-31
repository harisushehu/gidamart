"""
Image Processing Utilities
Handles image uploads, conversion, and optimization
"""

import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename

try:
    from pillow_heif import register_heif_opener
    # Register HEIF opener with Pillow
    register_heif_opener()
    HEIC_SUPPORT = True
    print("✅ HEIC support enabled - iPhone photos will be converted to JPEG")
except ImportError:
    HEIC_SUPPORT = False
    print("⚠️ HEIC support not available - iPhone photos will be rejected")

def is_allowed_image_file(filename):
    """
    Check if the uploaded file is an allowed image type
    """
    if not filename:
        return False
    
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    if HEIC_SUPPORT:
        allowed_extensions.update({'heic', 'heif'})
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def convert_heic_to_jpeg(input_path, output_path=None, quality=85):
    """
    Convert HEIC/HEIF image to JPEG format
    
    Args:
        input_path (str): Path to the HEIC file
        output_path (str): Path for the output JPEG file (optional)
        quality (int): JPEG quality (1-100)
    
    Returns:
        str: Path to the converted JPEG file
    """
    if not HEIC_SUPPORT:
        raise Exception("HEIC support not available. Install pillow-heif package.")
    
    try:
        # Open HEIC image
        with Image.open(input_path) as img:
            # Convert to RGB (JPEG doesn't support transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.jpg"
            
            # Save as JPEG
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
        return output_path
        
    except Exception as e:
        raise Exception(f"Failed to convert HEIC to JPEG: {str(e)}")

def process_uploaded_image(file, upload_folder, max_size=(1920, 1080), quality=85):
    """
    Process uploaded image file, converting HEIC if necessary
    
    Args:
        file: Flask uploaded file object
        upload_folder (str): Directory to save the processed image
        max_size (tuple): Maximum dimensions (width, height)
        quality (int): JPEG quality for compressed images
    
    Returns:
        dict: {
            'success': bool,
            'filename': str,
            'original_format': str,
            'converted': bool,
            'error': str (if success=False)
        }
    """
    try:
        if not file or not file.filename:
            return {'success': False, 'error': 'No file provided'}
        
        if not is_allowed_image_file(file.filename):
            supported_formats = "JPG, JPEG, PNG, GIF, WebP"
            if HEIC_SUPPORT:
                supported_formats += ", HEIC, HEIF"
            return {
                'success': False, 
                'error': f'Unsupported file format. Supported formats: {supported_formats}'
            }
        
        # Secure the filename
        original_filename = secure_filename(file.filename)
        original_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # Generate unique filename
        unique_id = uuid.uuid4().hex
        
        # Check if it's a HEIC file that needs conversion
        is_heic = original_extension in ['heic', 'heif']
        converted = False
        
        if is_heic and HEIC_SUPPORT:
            # Save original HEIC file temporarily
            temp_path = os.path.join(upload_folder, f"temp_{unique_id}.{original_extension}")
            file.save(temp_path)
            
            # Convert to JPEG
            final_filename = f"{unique_id}.jpg"
            final_path = os.path.join(upload_folder, final_filename)
            
            try:
                convert_heic_to_jpeg(temp_path, final_path, quality)
                converted = True
                
                # Remove temporary HEIC file
                os.remove(temp_path)
                
            except Exception as e:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return {'success': False, 'error': f'HEIC conversion failed: {str(e)}'}
                
        else:
            # Handle regular image formats
            final_filename = f"{unique_id}.{original_extension}"
            final_path = os.path.join(upload_folder, final_filename)
            file.save(final_path)
        
        # Optimize/resize image if needed
        try:
            with Image.open(final_path) as img:
                # Check if image needs resizing
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Save optimized version
                    if img.mode in ('RGBA', 'LA', 'P') and final_filename.lower().endswith('.jpg'):
                        # Convert to RGB for JPEG
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    img.save(final_path, quality=quality, optimize=True)
                    
        except Exception as e:
            print(f"Warning: Image optimization failed: {str(e)}")
            # Continue anyway - the original file is still saved
        
        return {
            'success': True,
            'filename': final_filename,
            'original_format': original_extension.upper(),
            'converted': converted,
            'error': None
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_image_info(file_path):
    """
    Get information about an image file
    
    Args:
        file_path (str): Path to the image file
    
    Returns:
        dict: Image information
    """
    try:
        with Image.open(file_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1]
            }
    except Exception as e:
        return {'error': str(e)}
