# fecom-ecom-realtime-recommendation
 
fecom-ecom-realtime-recommendation/
├── airflow/                      # Airflow orchestration cho pipeline huấn luyện và ingest
│   ├── dags/
│   │   ├── training_dag.py       # DAG định kỳ huấn luyện mô hình
│   │   └── ingestion_dag.py      # DAG kích hoạt ingest CSV (nếu dùng Airflow)
│   ├── Dockerfile                # Image cho Airflow components (scheduler, webserver)
│   └── requirements.txt
│
├── data/                         # Thư mục chứa dữ liệu CSV và snapshots
│   ├── raw/                      # Nơi chứa các file CSV gốc (orders.csv, customers.csv,...)
│   └── processed/                # Snapshot dùng cho CDC simulation (last_snapshot.json,...)
│
├── deployment/                   # Cấu hình triển khai (Docker Compose, Kubernetes YAML)
│   ├── docker-compose.yml        # Khởi chạy toàn bộ hệ thống trên Docker Compose
│   └── kubernetes/               
│       ├── airflow-deployment.yaml
│       ├── kafka-deployment.yaml
│       ├── spark-deployment.yaml
│       └── model-serving-deployment.yaml
│
├── docs/                         # Tài liệu kiến trúc, hướng dẫn triển khai, thiết kế dashboard
│   ├── architecture.md           # Giải thích tổng quan hệ thống
│   └── kpi_dashboard.md          # Định nghĩa các KPI và cách xây dựng dashboard
│
├── ingestion/                    # Phần ingest dữ liệu từ CSV (CDC/ API)
│   ├── cdc/                      
│   │   ├── cdc_simulator.py      # Script so sánh CSV và tạo event
│   │   └── requirements.txt
│   └── api/                     
│       ├── api_event.py          # API endpoint sử dụng FastAPI để trigger ingest
│       └── requirements.txt
│
├── kafka/                        # Cấu hình Kafka và Zookeeper
│   ├── config/
│   │   ├── server.properties
│   │   └── zookeeper.properties
│   └── docker-compose.yml        # Docker Compose cho Kafka & Zookeeper
│
├── local_sql/                    # Cấu hình hoặc script cho Local SQL Database
│   ├── init_db.sql               # Script tạo bảng, seed dữ liệu ban đầu
│   └── Dockerfile                # Image cho Local SQL (ví dụ: PostgreSQL custom image)
│
├── processing/                   # Xử lý realtime và batch ETL
│   ├── streaming_job.py          # Spark/Flink job đọc từ Kafka, tính feature realtime
│   ├── batch_etl.py              # Script ETL chuyển từ Local SQL lên Cloud Warehouse
│   └── requirements.txt
│
├── models/                       # Mã nguồn cho huấn luyện và serving model gợi ý
│   ├── training/                 
│   │   ├── train_model.py        # Huấn luyện mô hình recommendation
│   │   └── requirements.txt
│   └── serving/                  
│       ├── model_server.py       # API serving (Ray Serve, FastAPI, Flask,...)
│       └── requirements.txt
│
├── dashboard/                    # Cấu hình dashboard KPI & giám sát
│   ├── superset/                 # Cấu hình Superset, file JSON dashboard export (nếu có)
│   └── grafana/                  # File cấu hình Grafana, dashboard JSON
│
├── utils/                        # Các hàm tiện ích dùng chung (logging, helper...)
│   └── helper.py
│
├── .gitignore
├── README.md                     # Hướng dẫn tổng quan dự án, cách chạy và deploy
└── requirements.txt              # File tổng hợp các dependency (nếu dùng conda/pipenv)
