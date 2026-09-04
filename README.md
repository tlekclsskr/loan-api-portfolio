# Loan API — Serverless Auto Loan Application System

โปรเจกต์พอร์ตโฟลิโอ: Backend API สำหรับระบบสมัครสินเชื่อเช่าซื้อรถยนต์ สร้างด้วยสถาปัตยกรรม serverless บน AWS ทั้งหมด ตั้งแต่ infrastructure, application code, testing, ไปจนถึง CI/CD deploy ให้อัตโนมัติ

## Live Demo

```
API Base URL: https://cn6erl8kc2.execute-api.ap-southeast-7.amazonaws.com
```

## Tech Stack

- **Compute:** AWS Lambda (Python 3.13)
- **API:** Amazon API Gateway (HTTP API)
- **Database (NoSQL):** Amazon DynamoDB — เก็บข้อมูลคำขอสินเชื่อ (สถานะเปลี่ยนบ่อย, เข้าถึงด้วย key เดี่ยว)
- **Database (SQL):** Amazon RDS (PostgreSQL) — เก็บข้อมูลลูกค้า/สัญญา (ต้องการ relational integrity, foreign key, join)
- **Storage:** Amazon S3 (ผ่าน presigned URL) — เก็บเอกสารประกอบ (สลิปเงินเดือน, บัตรประชาชน)
- **IaC:** AWS SAM (CloudFormation)
- **CI/CD:** GitHub Actions
- **Testing:** pytest + moto (mock AWS services)
- **Third-party integration:** Exchange rate API (open.er-api.com)

## Architecture

```
Client → API Gateway → Lambda → DynamoDB (loan applications)
                              → S3 (documents, via presigned URL)
                              → External API (exchange rate)

[Separate] Lambda → RDS PostgreSQL (customers, contracts)
```

**เหตุผลที่ใช้ทั้ง SQL และ NoSQL:** ข้อมูลคำขอสินเชื่อ (สถานะ pending/approved) เข้าถึงด้วย id เดี่ยวๆ ไม่มีความสัมพันธ์ซับซ้อน เหมาะกับ DynamoDB (เร็ว, schema ยืดหยุ่น, scale อัตโนมัติ ไม่มีปัญหาเรื่อง connection limit กับ Lambda) ส่วนข้อมูลลูกค้า/สัญญาต้องการ referential integrity (ลูกค้า 1 คนมีได้หลายสัญญา, ห้ามมีสัญญาที่ไม่มีเจ้าของ) และ join สำหรับ query เชิงธุรกิจ (เช่น สรุปหนี้รวมของลูกค้า) จึงเหมาะกับ PostgreSQL

## API Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| POST | `/loans` | สมัครสินเชื่อใหม่ |
| GET | `/loans` | ดูรายการคำขอทั้งหมด |
| GET | `/loans/{id}` | ดูรายละเอียดคำขอเดียว |
| PATCH | `/loans/{id}` | เปลี่ยนสถานะ (approved/rejected) |
| DELETE | `/loans/{id}` | ลบคำขอ |
| POST | `/loans/{id}/document` | ขอ presigned URL สำหรับอัปโหลดเอกสาร |
| GET | `/loans/exchange-rate` | เช็คอัตราแลกเปลี่ยน USD→THB (third-party API) |

## การรัน Test

```bash
cd src
pip install pytest moto boto3
pytest -v
```

Test ใช้ `moto` จำลอง AWS services ทั้งหมด ไม่มีการยิง network จริงไปหา AWS หรือเสียค่าใช้จ่ายใดๆ

## การ Deploy

```bash
sam build
sam deploy --guided   # ครั้งแรก
sam deploy             # ครั้งถัดไป
```

หรือปล่อยให้ **GitHub Actions** deploy ให้อัตโนมัติทุกครั้งที่ push ขึ้น branch `main` (ดู `.github/workflows/deploy.yml`) — pipeline จะรัน unit test ก่อนเสมอ ถ้า test fail จะไม่ deploy

## Security & Design Decisions

- **Presigned URL แทนการอัปโหลดผ่าน Lambda โดยตรง** — ลดภาระ Lambda, ไฟล์ไม่ผ่าน compute layer, ปลอดภัยกว่าเพราะสิทธิ์หมดอายุอัตโนมัติ (5 นาที)
- **least privilege IAM policies** — Lambda มีสิทธิ์แค่ table/bucket ที่เกี่ยวข้องเท่านั้น (ผ่าน SAM policy templates เช่น `DynamoDBCrudPolicy`, `S3CrudPolicy`) ไม่ใช่ full access
- **Unit test เป็น gate ก่อน deploy** — CI จะ block การ deploy ถ้า test ไม่ผ่าน ป้องกันโค้ดพังหลุดขึ้น production

## Known Limitations / Future Improvements

- **RDS/VPC ยังจัดการแบบ manual ผ่าน AWS Console** ไม่ได้อยู่ใน IaC เดียวกับ Lambda เพราะ database infrastructure มี lifecycle ต่างจาก application code (ไม่ควรถูกสร้าง/ลบบ่อยเท่า Lambda) — ในทีมจริงมักแยก IaC ของ stateful infrastructure (เช่นด้วย Terraform) ออกจาก application deployment เช่นกัน ขั้นต่อไปคือย้าย RDS+VPC ไปเป็น Terraform module แยก
- **API ยังไม่มี authentication** (เปิดสาธารณะ) ขั้นต่อไปควรเพิ่ม API key หรือ Amazon Cognito authorizer
- **RDS เปิด public access** เพื่อความง่ายในการพัฒนา ควรย้ายเป็น private VPC + bastion host/VPN สำหรับ production จริง
- **third-party API (exchange rate) ยังไม่มี unit test** เพราะเป็นการยิง network จริง ควรเพิ่ม test ด้วย `unittest.mock.patch` แยกจาก integration test
