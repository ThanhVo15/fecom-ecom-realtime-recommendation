Dưới đây là một tài liệu chi tiết mô tả workflow và cấu trúc folder cho dự án “Realtime Product Recommendation” của Fecom Inc, trong đó dữ liệu được ingest từ CSV (hoặc API) qua 3 tầng: ETL, load lên hệ thống SQL cục bộ (local SQL) và sau đó đẩy lên Data Warehouse trên Cloud. Tôi cũng sẽ gợi ý tên dự án trên GitHub và đánh giá khả năng thực hiện (feasibility) dựa trên tiêu chí dữ liệu hiện có.

---

# 1. Tên Dự Án GitHub & Đánh Giá Khả Năng Thực Hiện

**Tên dự án GitHub gợi ý:**  
`fecom-ecom-realtime-recommendation`

**Đánh giá độ khả thi (feasibility):**  
- **Dữ liệu có đủ không?**  
  - Bộ CSV hiện có của bạn bao gồm các file liên quan đến đơn hàng (orders), khách hàng (customers), sản phẩm (products), feedback/reviews, v.v.  
  - Nếu các file này chứa thông tin như ID, timestamp, trạng thái cập nhật, chúng ta có thể sử dụng để mô phỏng các “event” của hệ thống.  
  - **Tiêu chí:**  
    - Nếu các file CSV có thông tin timestamp và ID duy nhất, bạn có thể phát hiện các thay đổi (mới hoặc cập nhật) cho ETL mô phỏng CDC.
    - Số lượng record có thể đủ để huấn luyện mô hình gợi ý (nếu dataset chứa lịch sử giao dịch và phản hồi từ người dùng).
- **Về kỹ thuật:**  
  - Dữ liệu ban đầu là batch (CSV) nên cần mô phỏng event bằng script hoặc API, chuyển đổi qua 3 tầng:  
    1. ETL (Extract – Transform – Load) để làm sạch và làm phong phú dữ liệu.
    2. Nạp dữ liệu vào local SQL Database (ví dụ: PostgreSQL, MySQL) để kiểm tra nội bộ, phân tích nhỏ, sau đó chuyển sang Cloud Data Warehouse (ví dụ: Google BigQuery, Snowflake hoặc AWS Redshift).
    3. Data Warehouse phục vụ cho các quá trình training, analytics và gợi ý realtime.
  - Công nghệ bổ sung: Kafka, Spark Streaming để chuyển đổi sang realtime processing, Airflow để orchestration, và một API (FastAPI / Flask) cho model serving.

Nhìn chung, nếu dữ liệu CSV của bạn có thông tin đủ (đặc biệt, có timestamp để xác định các bản ghi mới và cập nhật) thì khả năng thực hiện là khả thi. Dự án sẽ ban đầu là một proof-of-concept (POC) và sau đó dần mở rộng thêm các thành phần realtime thật.

---

# 2. Workflow Toàn Bộ Hệ Thống

Dưới đây là workflow chi tiết kết hợp cả hệ thống ingest qua 3 tầng và realtime recommendation:

```
           +----------------------------------------------------+
           |             E-Commerce Platform / API            |
           |        (User Order, product view, feedback)        |
           +-------------------------+--------------------------+
                                     |
         (Trigger – mỗi khi CSV được cập nhật / có API call)
                                     |
                                     v
           +-------------------------+--------------------------+
           |   Data Ingestion Layer: CDC Simulation / API       |
           |   (Script so sánh CSV mới với snapshot cũ)         |
           +-------------------------+--------------------------+
                                     |
             Tạo ra event theo format Avro/JSON
                                     |
                                     v
           +-------------------------+--------------------------+
           |                     Kafka Broker                   |
           |            (Message Bus cho các event)             |
           +-------------------------+--------------------------+
                                     |
                   +-----------------+------------------+
                   |                                    |
         +---------v---------+                  +-------v-------+
         |  Spark/Flink ETL  |                  |  Local SQL DB |
         |  (Stream Processing)                  | (Cục bộ, dùng   |
         |   - Tiền xử lý & tính feature         |  để test, phân tích)|
         +---------+---------+                  +-------+-------+
                   |                                    |
         +---------v---------+                  +-------v-------+
         |   Online Feature  |                  |   Cloud Data  |
         |   Store / Data    |  <--- Batch ETL -->|   Warehouse   |
         |   Lake            |   (ETL 3 tầng:   | (BigQuery,    |
         | (Redis/Cassandra) |    - Raw -->     |  Snowflake,   |
         |                   |    - Local SQL   |  AWS Redshift)|
         +---------+---------+    --> Cloud Data  +---------------+
                   |
         +---------v---------+
         |  Recommendation  |
         |  Model Serving   |
         |  (Ray Serve,     |
         |   Flask, FastAPI)|
         +---------+---------+
                   |
     Client call: API trả về top product gợi ý  
                   |
         +---------v---------+
         | KPI Dashboard     |
         | (Superset, Grafana|
         |  ElasticSearch)   |
         +-------------------+
```

### Giải thích các tầng:
1. **Data Ingestion:**  
   - Sử dụng script CDC/cron để so sánh CSV hiện tại với snapshot cũ, sau đó tạo ra “event” cho những bản ghi mới hoặc cập nhật.
   - Có thể cung cấp API để trigger ingest thủ công.

2. **Message Broker:**  
   - Event được gửi lên Kafka làm dữ liệu stream cho các pipeline realtime.

3. **ETL & Local SQL:**  
   - Một job Spark/Flink (hoặc Python script) đọc event từ Kafka, thực hiện tiền xử lý, tính toán feature (ví dụ: số đơn hàng, tần suất mua, sản phẩm phổ biến…).
   - Kết quả lưu vào một Online Feature Store (Redis/Cassandra) để phục vụ nhanh cho API.
   - Đồng thời, quá trình ETL sẽ ghi dữ liệu vào local SQL DB (dùng làm staging, phân tích nhỏ), sau đó đẩy dữ liệu qua Cloud Data Warehouse.

4. **Cloud Data Warehouse:**  
   - Dữ liệu sau khi được chuyển đổi được lưu trữ cho mục đích phân tích sâu và pipeline huấn luyện mô hình.
   - Thông qua job định kỳ (Airflow) sẽ lấy dữ liệu từ Warehouse, huấn luyện mô hình gợi ý và cập nhật model vào MLflow.

5. **Recommendation Model Serving:**  
   - Model gợi ý (đã huấn luyện) được deploy qua API (ví dụ: dùng Ray Serve hoặc FastAPI) trả kết quả realtime khi có yêu cầu từ người dùng.
   
6. **Dashboard & Monitoring:**  
   - KPI như CTR, conversion, throughput, latency… được thu thập từ các hệ thống (Kafka, API, SQL) và hiện thị qua các công cụ dashboard như Superset, Grafana, Kibana.

---

# 3. Cấu Trúc Folder Dự Án Đề Xuất

Dưới đây là cấu trúc folder mở rộng tích hợp cả ingestion từ CSV qua 3 tầng ETL, local SQL, và Cloud Data Warehouse:

```
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
```

---

# 4. Các Bước Triển Khai Cụ Thể

1. **Thiết Lập Data Ingestion:**
   - Đưa các file CSV vào `data/raw/`.
   - Chạy `ingestion/cdc/cdc_simulator.py` (theo cron hoặc Airflow DAG) để so sánh snapshot và tạo event mới → gửi lên Kafka.
   - Nếu cần gọi qua API, triển khai `ingestion/api/api_event.py` và chạy bằng uvicorn.

2. **Cài Đặt Kafka & Local SQL:**
   - Dùng Docker Compose để khởi chạy Kafka (theo folder `kafka/`) và Local SQL (PostgreSQL từ folder `local_sql/`).
   - Thiết lập schema cho Local SQL qua script `local_sql/init_db.sql`.

3. **Xử Lý ETL & Realtime Processing:**
   - Chạy Spark Streaming job (`processing/streaming_job.py`) để đọc từ Kafka, làm sạch dữ liệu, tính feature, và lưu vào Online Feature Store.
   - Chạy script `processing/batch_etl.py` định kỳ (Airflow hoặc cron job) để chuyển dữ liệu từ Local SQL lên Cloud Data Warehouse (ví dụ: thông qua API của cloud hoặc thông qua kết nối trực tiếp).

4. **Huấn Luyện & Deploy Model:**
   - Lập trình và chạy quá trình huấn luyện mô hình từ dữ liệu ở Cloud Warehouse qua Airflow DAG (`airflow/dags/training_dag.py`), log kết quả vào MLflow.
   - Sau khi huấn luyện, deploy mô hình qua `models/serving/model_server.py` sử dụng Ray Serve hoặc FastAPI.

5. **Dashboard & Monitoring:**
   - Cấu hình Superset (trong `dashboard/superset/`) hoặc Grafana (trong `dashboard/grafana/`) kết nối đến Cloud Warehouse và log sources để theo dõi KPI (CTR, conversion, latency, throughput,...).
   - Thiết lập alerts qua Prometheus/Grafana nếu có bất thường.

6. **Orchestration & CI/CD:**
   - Sử dụng Airflow (folder `airflow/`) để điều phối các job định kỳ.
   - Dockerize tất cả các thành phần và triển khai qua Docker Compose (hoặc chuyển sang Kubernetes thông qua file YAML trong `deployment/kubernetes/`).
   - Tích hợp CI/CD pipeline (Jenkins/GitHub Actions) để tự động build và deploy.

---

# 5. Kết Luận

- **Workflow đã hoàn chỉnh:**  
  Từ ingest dữ liệu batch từ CSV (thông qua API hoặc CDC simulation) → gửi event qua Kafka → xử lý realtime qua Spark/Flink, cập nhật vào Local SQL & Cloud Data Warehouse → huấn luyện và deploy model gợi ý → phục vụ API realtime → giám sát KPI qua dashboard (Superset/Grafana).

- **Cấu trúc folder:**  
  Đã được bố cục rõ ràng theo các module: ingestion, processing, models (training & serving), local SQL, dashboard, deployment, airflow, docs, v.v.

- **Tên dự án GitHub:**  
  `fecom-ecom-realtime-recommendation`

- **Đánh giá khả thi:**  
  Dữ liệu CSV ban đầu nếu có thông tin timestamp và ID sẽ đủ để mô phỏng sự kiện thông qua CDC hoặc cron-based polling. Mặc dù dữ liệu gốc là batch, nhưng việc “bơm” event vào Kafka sẽ giúp xây dựng các pipeline realtime và phục vụ API gợi ý. Dự án có đủ yêu cầu cho proof-of-concept và mở rộng khi cần, tuy nhiên cần chú ý đến tính nhất quán và độ trễ trong quá trình ingest từ CSV vào DB (local SQL) và Cloud Warehouse.

Hy vọng tài liệu chi tiết này sẽ giúp bạn có cái nhìn tổng thể về các bước triển khai, kiến trúc workflow cũng như cách tổ chức dự án. Nếu có bất kỳ thắc mắc hoặc cần hỗ trợ thêm chi tiết, hãy trao đổi tiếp để hoàn thiện các module.