import pandas as pd
import s3fs
import pyarrow as pa
import pyarrow.parquet as pq
import io
# --- IMPORT CENTRALIZED CONFIGURATION ---
from config import STORAGE_OPTIONS, BUCKET_NAME, FILES_TO_CONVERT

# Configuration for MinIO extracted from config.py
endpoint_url = STORAGE_OPTIONS["aws_endpoint_url"]
access_key = STORAGE_OPTIONS["aws_access_key_id"]
secret_key = STORAGE_OPTIONS["aws_secret_access_key"]
bucket_name = BUCKET_NAME

# Initialize S3 FileSystem to connect to MinIO storage
fs = s3fs.S3FileSystem(
    key=access_key,
    secret=secret_key,
    client_kwargs={'endpoint_url': endpoint_url}
)

def convert_with_s3fs(file_name):
    try:
        # Define target name by replacing extension
        target_name = file_name.replace(".tsv.zip", ".parquet")
        source_path = f"{bucket_name}/{file_name}"
        target_path = f"{bucket_name}/{target_name}"
        
        print(f"--- Processing: {file_name} ---")

        with fs.open(source_path, 'rb') as f:
            # Use dtype=str to preserve data integrity and leading zeros
            reader = pd.read_csv(
                f, 
                sep='\t', 
                compression='zip', 
                chunksize=100000, 
                low_memory=False,
                dtype=str
            )

            writer = None
            # Memory buffer to hold Parquet data before uploading
            parquet_buffer = io.BytesIO()

            for i, chunk in enumerate(reader):
                # Convert Pandas chunk to PyArrow Table
                table = pa.Table.from_pandas(chunk)
                
                if writer is None:
                    # Initialize ParquetWriter with the schema from the first chunk
                    writer = pq.ParquetWriter(parquet_buffer, table.schema)
                
                # Append current chunk to the Parquet file in the buffer
                writer.write_table(table)
                
                if i % 10 == 0:
                    print(f"   Progress: {i * 100000} rows processed...")

            if writer:
                writer.close()

            # Upload finalized Parquet buffer to MinIO
            print(f"   Uploading {target_name} to MinIO...")
            parquet_buffer.seek(0)
            with fs.open(target_path, 'wb') as out_f:
                out_f.write(parquet_buffer.getvalue())
                
        print(f"Success: Created {target_name}\n")

    except Exception as e:
        print(f"Error processing {file_name}: {e}\n")

# List of source files on MinIO retrieved from config.py
files_to_convert = FILES_TO_CONVERT

if __name__ == "__main__":
    for f in files_to_convert:
        # Check if the file exists in the bucket before starting
        if fs.exists(f"{bucket_name}/{f}"):
            convert_with_s3fs(f)
        else:
            print(f"Warning: {f} not found in bucket. Is the download finished?")