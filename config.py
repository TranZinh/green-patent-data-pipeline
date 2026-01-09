import os
from pathlib import Path

# --- THÔNG TIN KẾT NỐI MINIO ---
STORAGE_OPTIONS = {
    "aws_endpoint_url": "http://minio:9000",
    "aws_access_key_id": "admin",
    "aws_secret_access_key": "password123",
    "aws_region": "us-east-1",
    "aws_allow_http": "true"
}

# Dành riêng cho thư viện minio Client (script download dùng)
MINIO_CONFIG = {
    "endpoint": "minio:9000",
    "access_key": "admin",
    "secret_key": "password123",
    "secure": False
}

BUCKET_NAME = "patents-data"

# --- QUẢN LÝ ĐƯỜNG DẪN NGUỒN ---
def load_sources(file_path="data_sources.txt"):
    if not os.path.exists(file_path):
        default_links = [
            "https://s3.amazonaws.com/data.patentsview.org/download/g_patent.tsv.zip",
            "https://s3.amazonaws.com/data.patentsview.org/download/g_application.tsv.zip",
            "https://s3.amazonaws.com/data.patentsview.org/download/g_cpc_current.tsv.zip",
            "https://s3.amazonaws.com/data.patentsview.org/download/g_assignee_disambiguated.tsv.zip"
        ]
        with open(file_path, "w") as f:
            f.write("\n".join(default_links))
        return default_links
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

ALL_SOURCES = load_sources()

def get_base_name(keyword):
    link = next((s for s in ALL_SOURCES if keyword in s.lower()), None)
    if link:
        return link.split('/')[-1].replace('.tsv.zip', '')
    return None

# Tên gốc (Base Name) dùng để tự động cộng đuôi .tsv.zip hoặc .parquet
NAME_PATENT = get_base_name("g_patent")
NAME_APP    = get_base_name("g_application")
NAME_CPC    = get_base_name("g_cpc_current")
NAME_ASS    = get_base_name("g_assignee_disambiguated")

# --- DANH SÁCH CHO CÁC BƯỚC ---

# Dùng cho script DOWNLOAD: { "g_patent.tsv.zip": "URL" }
FILES_TO_DOWNLOAD = { f"{link.split('/')[-1]}": link for link in ALL_SOURCES }

# Dùng cho script CONVERT: [ "g_patent.tsv.zip", ... ]
FILES_TO_CONVERT = [f"{n}.tsv.zip" for n in [NAME_PATENT, NAME_APP, NAME_CPC, NAME_ASS] if n]

# Dùng cho script ANALYSIS (Đường dẫn S3 Parquet)
S3_PATH_PATENT = f"s3://{BUCKET_NAME}/{NAME_PATENT}.parquet"
S3_PATH_APP    = f"s3://{BUCKET_NAME}/{NAME_APP}.parquet"
S3_PATH_CPC    = f"s3://{BUCKET_NAME}/{NAME_CPC}.parquet"
S3_PATH_ASS    = f"s3://{BUCKET_NAME}/{NAME_ASS}.parquet"

# --- THÔNG SỐ KHÁC ---
TEMP_DIR = Path("./temp_downloads")
OUTPUT_CSV = "top_green_innovators.csv"