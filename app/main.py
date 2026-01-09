import subprocess
import sys
# --- IMPORT CENTRALIZED CONFIGURATION ---
from config import MINIO_CONFIG, BUCKET_NAME, FILES_TO_DOWNLOAD

def main():
    """
    Orchestrates data ingestion using the MinIO Client (mc) binary.
    Mimics the exact shell logic used in the Docker entrypoint.
    """
    # Extract connection and bucket settings from config.py
    conf = MINIO_CONFIG
    bucket = BUCKET_NAME
    
    # Initialize the command sequence:
    # 1. Wait for local MinIO to be ready and set the 'myminio' alias
    # 2. Configure the 's3' alias for the public PatentsView source
    # 3. Create the target bucket if it does not already exist
    commands = [
        f"until mc alias set myminio http://{conf['endpoint']} {conf['access_key']} {conf['secret_key']}; do sleep 1; done",
        "mc alias set s3 https://s3.amazonaws.com '' '' --api S3v4",
        f"mc mb --ignore-existing myminio/{bucket}"
    ]

    # 4. Generate 'mc cp' commands for each file defined in config.py
    for file_name, url in FILES_TO_DOWNLOAD.items():
        # Convert HTTPS URL to mc-compatible path (e.g., s3/bucket/path)
        s3_src = url.replace("https://s3.amazonaws.com/", "s3/")
        commands.append(f"mc cp {s3_src} myminio/{bucket}/{file_name}")

    # Chain commands with '&&' to ensure sequential execution and stop on failure
    full_command = " && ".join(commands)

    print(f"--- Executing Data Transfer: S3 -> MinIO (via mc cp) ---")
    
    # Execute the command string via the system shell
    try:
        # Using /bin/sh to ensure compatibility with Docker's entrypoint logic
        subprocess.run(full_command, shell=True, check=True, executable="/bin/sh")
        print(f"\n[SUCCESS] All files successfully transferred to bucket: '{bucket}'")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()