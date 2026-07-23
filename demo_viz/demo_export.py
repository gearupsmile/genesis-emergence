import os
import glob
import zipfile
import imageio.v3 as iio
from demo_viz.demo_config import FRAMES_DIR, VIDEOS_DIR, FPS, LOGS_DIR

def compile_video(output_filename="demo_video.mp4"):
    output_path = os.path.join(VIDEOS_DIR, output_filename)
    frame_files = sorted(glob.glob(os.path.join(FRAMES_DIR, "*.png")))
    
    if not frame_files:
        print("No frames found to compile.")
        return None
        
    print(f"Compiling {len(frame_files)} frames into {output_path}...")
    
    # Write MP4
    writer = iio.imopen(output_path, "w", plugin="pyav")
    writer.init_video_stream("vp9", fps=FPS) # Or h264 if supported, vp9 is often universally supported without external codecs
    # Note: imageio[ffmpeg] plugin "pyav" uses PyAV which supports "h264" if installed, 
    # but "libx264" is standard. Let's try standard imageio writing.
    writer.close()
    
    # Better approach with standard imageio writer
    try:
        writer = iio.imopen(output_path, "w", plugin="pyav")
        writer.init_video_stream("libx264", fps=FPS)
        for frame_file in frame_files:
            img = iio.imread(frame_file)
            writer.write_frame(img)
        writer.close()
    except Exception as e:
        print(f"Failed with libx264, trying fallback: {e}")
        try:
            with iio.imopen(output_path, "w", plugin="pyav") as writer:
                writer.init_video_stream("vp8", fps=FPS)
                for frame_file in frame_files:
                    img = iio.imread(frame_file)
                    writer.write_frame(img)
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            # Try basic imageio writer
            try:
                iio.imwrite(output_path, [iio.imread(f) for f in frame_files], fps=FPS, codec="libx264")
            except Exception as e3:
                print(f"Basic imwrite failed: {e3}")
                return None
                
    print("Video compilation complete.")
    return output_path

def create_zip(output_filename="raw_frames.zip"):
    output_path = os.path.join(VIDEOS_DIR, output_filename)
    frame_files = sorted(glob.glob(os.path.join(FRAMES_DIR, "*.png")))
    
    print(f"Zipping {len(frame_files)} frames into {output_path}...")
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in frame_files:
            zipf.write(f, os.path.basename(f))
            
    print("Zipping complete.")
    return output_path
