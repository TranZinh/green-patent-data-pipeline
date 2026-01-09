import io
import sys
from minio import Minio

# --- IMPORT CENTRALIZED CONFIGURATION ---
from config import MINIO_CONFIG, BUCKET_NAME, FILES_TO_DOWNLOAD

# 1. MinIO Client Initialization from config.py
client = Minio(
    MINIO_CONFIG["endpoint"],
    access_key=MINIO_CONFIG["access_key"],
    secret_key=MINIO_CONFIG["secret_key"],
    secure=MINIO_CONFIG["secure"]
)

bucket_name = BUCKET_NAME

# Mapping files to test based on the download list in config
files_to_test = FILES_TO_DOWNLOAD

def verify_zip_header_remote(filename):
    """
    Verify Zip Magic Bytes (PK..) without downloading the entire file.
    Zip standard headers always start with: b'PK\x03\x04'
    """
    try:
        # Request only the first 4 bytes of the file from MinIO (Range Request)
        response = client.get_object(bucket_name, filename, offset=0, length=4)
        header = response.read()
        response.close()
        response.release_conn()
        
        if header == b'PK\x03\x04':
            print(f"PASS: Header Check - Valid Zip Signature (PK..)")
            return True
        else:
            print(f"FAIL: Header Check - Invalid Signature. Got {header} instead of Zip header.")
            return False
    except Exception as e:
        print(f"FAIL: Header Check - Error reading header: {e}")
        return False

def test_single_file(filename):
    """
    Performs multiple audits on a specific file stored in MinIO.
    """
    print(f"\n--- Auditing File: {filename} ---")
    
    # 1. Check Existence & Metadata
    try:
        obj = client.stat_object(bucket_name, filename)
        size_mb = obj.size / (1024 * 1024)
        
        if obj.size == 0:
            print(f"FAIL: File is EMPTY (0 bytes).")
            return False
        
        print(f"PASS: Found file. Size: {size_mb:.2f} MB")
        
        # 2. Minimum Size Logic (Ensure file isn't just an error message)
        if obj.size < 1024 * 50: # Threshold: 50KB
            print(f"WARNING: File size is unusually small ({obj.size} bytes). Check source URL.")
            return False

        # 3. Remote Header Check (RAM-efficient validation)
        return verify_zip_header_remote(filename)

    except Exception as e:
        print(f"FAIL: File does not exist or MinIO connection error: {e}")
        return False

def main():
    print("STARTING SMART-TEST INGESTION (RAM-SAFE MODE)")
    print(f"Target Bucket: {bucket_name}")
    
    # Ensure bucket exists before testing files
    if not client.bucket_exists(bucket_name):
        print(f"ERROR: Bucket '{bucket_name}' not found.")
        sys.exit(1)

    results = []
    # Loop through the dynamic file list from config.py
    for filename in files_to_test.keys():
        success = test_single_file(filename)
        results.append(success)

    print("\n" + "="*40)
    if all(results) and len(results) > 0:
        print("SUCCESS: Ingestion data is valid and ready for processing!")
        sys.exit(0)
    else:
        print("FAILURE: One or more files failed validation or no files found.")
        sys.exit(1)

if __name__ == "__main__":
    main()