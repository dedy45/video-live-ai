from huggingface_hub import snapshot_download
import os

checkpoint_dir = os.path.join(os.path.dirname(__file__), "..", "checkpoints", "s2-pro")
os.makedirs(checkpoint_dir, exist_ok=True)

print(f"Downloading fishaudio/s2-pro to {checkpoint_dir}")
print("This will take several minutes (~10GB)...")

snapshot_download(
    repo_id="fishaudio/s2-pro",
    local_dir=checkpoint_dir,
    local_dir_use_symlinks=False
)

print("Download complete!")
