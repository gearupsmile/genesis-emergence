import os
import imageio.v2 as iio

def compile_existing_frames():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    frames_dir = os.path.join(root_dir, 'demo_output', 'frames')
    out_file = os.path.join(root_dir, 'demo_output', 'genesis_v5_demo.mp4')
    
    print("Compiling video from existing frames...")
    
    # We use imageio.v2 because v3 deprecated get_writer
    writer = iio.get_writer(out_file, fps=30)
    
    # We expect 1800 frames
    for frame in range(1800):
        path = os.path.join(frames_dir, f"frame_{frame:04d}.png")
        if os.path.exists(path):
            writer.append_data(iio.imread(path))
            
    writer.close()
    print(f"Video compiled successfully! Saved to {out_file}")

if __name__ == '__main__':
    compile_existing_frames()
