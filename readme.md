Patent Data Pipeline: Scalable Green Tech Analysis
Hệ thống xử lý và phân tích dữ liệu bằng sáng chế quy mô lớn (57M+ bản ghi), tập trung vào Green Technologies (CPC Y02). Dự án được tối ưu hóa để chạy mượt mà trên phần cứng hạn chế (8GB RAM) mà không cần server khủng.

Note from Developer: Đây là dự án cá nhân được phát triển trong 1 ngày. Do giới hạn về thời gian và "sự lười biếng" của developer (ưu tiên giải pháp đơn giản mà hiệu quả), hệ thống hiện tại tập trung vào tính thực dụng, giải quyết bài toán dữ liệu lớn trên phần cứng yếu trước khi nghĩ đến các công cụ chuyên nghiệp hơn như airflow, spark,... .

🚀 Key Highlights
📦 Resource Efficiency: Xử lý 57 triệu dòng dữ liệu trên máy 8GB RAM nhờ Polars Streaming.

🌱 Green Insight: Lọc và phân tích Green Patents theo chuẩn CPC Y02 (OECD / EPO).

🐳 Environment Isolation: Kiến trúc Dockerized, tách biệt Storage (MinIO) và Compute (Python).

🛡️ Data Integrity: Tích hợp quy trình Audit & Reconciliation (đối soát) đảm bảo dữ liệu không sai lệch qua các bước.

⚙️ Config-Driven: Quản lý toàn bộ tham số qua config.py, dễ dàng chuyển đổi môi trường.

🏗️ Data Workflow & Structure
Dự án tổ chức luồng dữ liệu theo 3 bước xử lý cơ bản để quản lý tệp tin gọn gàng và tối ưu bộ nhớ:

Raw Storage (Input): Lưu trữ các file .tsv.zip gốc tải từ USPTO S3. Đây là dữ liệu thô, được giữ nguyên vẹn để phục vụ đối soát.

Middle Storage (Temporary Parquet): Dữ liệu được giải nén và chuyển sang định dạng .parquet. Bước này giúp giảm kích thước file và tăng tốc độ truy xuất nhanh hơn cho bước phân tích.

Final Output (Result): Kết quả thống kê cuối cùng được xuất ra file CSV, sẵn sàng để sử dụng ngay trên Excel hoặc các công cụ báo cáo.

📂 Project Structure
Plaintext

.
├── app/
│   ├── main.py                # Ingestion: S3 -> MinIO (MinIO Client)
│   ├── convert_to_parquet.py  # ETL: TSV.ZIP -> Parquet 
│   └── process_data.py        # Analytics: Polars Streaming
├── test/
│   ├── test_main.py           # Audit: Magic Bytes/Zip check
│   ├── test_convert.py        # Audit: Row count reconciliation
│   └── test_process.py        # Audit: Final data verification
├── config.py                  # Centralized configuration
├── docker-compose.yml         # Infrastructure (MinIO + Worker)
└── RUN_ALL.bat                # One-click Orchestrator for Windows
🛠️ Getting Started
1️⃣ Requirements
Docker & Docker Compose.

10GB Disk Space.

8GB RAM.

2️⃣ One-Click Execution
Thay vì gõ từng lệnh thủ công, sử dụng script điều phối đã được thiết lập sẵn:

Bash

# Khởi động hạ tầng (chạy lần đầu)
docker-compose up -d --build

# Chạy toàn bộ Pipeline (Ingest -> Test -> Transform -> Test -> Analyze -> Test)
RUN_ALL.bat
🛡️ Quality Assurance (QA) & Audit
Dự án nhấn mạnh vào việc kiểm soát lỗi dữ liệu thông qua 3 lớp phòng thủ:

Validation: Kiểm tra file ZIP ngay sau khi tải để tránh hỏng dữ liệu đường truyền.

Consistency Check: Đối soát số dòng giữa file TSV gốc và file Parquet sau khi convert.

Reconciliation: So sánh kết quả phân tích cuối cùng với dữ liệu thô bằng phương pháp Brute-force để đảm bảo logic chính xác.

📈 Future Roadmap (Scale-up Plan)
Dự án hiện tại là phiên bản Proof of Concept (PoC). Nếu nhu cầu dữ liệu tăng lên quy mô Petabyte hoặc có yêu cầu thực tế với lượng data lớn cần lưu và xử lý phân tán:

Orchestration: Thay thế .bat script bằng Apache Airflow để lập lịch, quản lý phụ thuộc (DAG) và cơ chế Retry tự động.

Distributed Compute: Chuyển đổi engine xử lý từ Polars sang Apache Spark chạy trên cụm Cluster để phân tán tải.

Data Warehouse Integration: Chuyển đổi lưu trữ từ Flat-files sang các định dạng bảng chuyên nghiệp (Delta Lake/Iceberg) để quản lý dữ liệu tốt hơn.

Observability: Tích hợp Logging tập trung (ELK Stack) và hệ thống cảnh báo.

📊 Project Status
✅ Stability: Đã kiểm thử ổn định trên 57M+ records.

✅ Accuracy: Vượt qua tất cả các bước đối soát tự động.

⚡ Performance: Tổng thời gian thực thi < 10 phút trên phần cứng cơ bản(trừ bước tải).

## 🔧 Environment Setup & Prerequisites

Trước khi chạy dự án, đảm bảo máy của bạn đã cài đặt đầy đủ các thành phần sau:

### 1️⃣ Docker & Docker Compose
- Docker Desktop (Windows / macOS / Linux)
- Docker Compose (đi kèm Docker Desktop)

Kiểm tra cài đặt:
```bash
docker --version
docker-compose --version
```

### 2️⃣ Python
- Python >= 3.9
- Khuyến nghị sử dụng Python 3.10+

Kiểm tra:
```bash
python --version
```

### 3️⃣ Windows Users
- File RUN_ALL.bat được thiết kế cho Windows
- Chạy bằng Command Prompt hoặc PowerShell
- Đảm bảo Docker Desktop đang chạy trước khi execute

### 4️⃣ Network & Firewall
- Cho phép Docker mở cổng nội bộ để MinIO và Worker giao tiếp
- Không yêu cầu public port hoặc external service
