import polars as pl
from minio import Minio
import zipfile
import io
import gc
import sys

# --- IMPORT CENTRALIZED CONFIGURATION ---
from config import MINIO_CONFIG, BUCKET_NAME, STORAGE_OPTIONS, FILES_TO_CONVERT

# 1. MinIO Client Initialization
client = Minio(
    MINIO_CONFIG["endpoint"],
    access_key=MINIO_CONFIG["access_key"],
    secret_key=MINIO_CONFIG["secret_key"],
    secure=MINIO_CONFIG["secure"]
)

bucket_name = BUCKET_NAME
storage_options = STORAGE_OPTIONS

def get_row_counts(zip_name, parquet_name):
    """
    Compares row counts between the source ZIP (TSV) and the target Parquet file.
    Uses streaming for ZIP and metadata-only scan for Parquet to save RAM.
    """
    print(f"\n--- Auditing: {parquet_name} ---")
    res = None
    try:
        # 1. Count Source (ZIP)
        print(f"   Counting source ZIP...")
        res = client.get_object(bucket_name, zip_name)
        
        src_count = 0
        # Load into memory buffer for zipfile processing
        zip_data = io.BytesIO(res.read())
        with zipfile.ZipFile(zip_data) as z:
            tsv_name = zip_name.replace(".zip", "")
            with z.open(tsv_name) as f:
                # Direct line iteration to keep memory footprint low
                for _ in f: 
                    src_count += 1
        
        # Subtract 1 to account for the header row
        src_count = max(0, src_count - 1)

        # Explicitly clean up ZIP objects
        zip_data.close()
        del zip_data
        res.close()
        res.release_conn()
        gc.collect()

        # 2. Count Parquet using METADATA ONLY
        # Polars scan_parquet is optimized to read only the footer for length queries
        print(f"   Counting Parquet metadata...")
        
        q = pl.scan_parquet(f"s3://{bucket_name}/{parquet_name}", storage_options=storage_options)
        
        # Using select(pl.len()) is the most efficient way to fetch row count from metadata
        tgt_count = q.select(pl.len()).collect().item()
        
        del q
        gc.collect()

        print(f"   Result: Source ({src_count:,}) vs Parquet ({tgt_count:,})")
        return src_count == tgt_count

    except Exception as e:
        print(f"   ERROR during audit: {e}")
        return False
    finally:
        gc.collect()

if __name__ == "__main__":
    # Dynamically generate the list of files to audit from config.py
    # This ensures we check exactly what was converted
    files = []
    for tsv_zip in FILES_TO_CONVERT:
        parquet_file = tsv_zip.replace(".tsv.zip", ".parquet")
        files.append((tsv_zip, parquet_file))
    
    overall_success = True
    
    for zip_fn, parquet_fn in files:
        success = get_row_counts(zip_fn, parquet_fn)
        if success:
            print("   => PASS: Row counts match.")
        else:
            print("   => FAIL: Row count mismatch or error.")
            overall_success = False
        
        # Clear internal buffers between file checks
        gc.collect()

    if not overall_success:
        print("\n[!] Audit failed for one or more files.")
        sys.exit(1)
    else:
        print("\n[+] All files verified successfully.")
        sys.exit(0)