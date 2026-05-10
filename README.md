# Personal Finance Tracker API

A production-grade REST API for tracking personal finances with proper database design, relationships, and analytics.

**Built with:** Python, Flask, PostgreSQL, SQLAlchemy

---

## Features

✅ **Account Management** - Create and manage multiple accounts
✅ **Transaction Tracking** - Record income and expenses with categories
✅ **Category Management** - Organize transactions by reusable categories
✅ **Analytics** - View account summary and spending by category
✅ **Data Integrity** - Foreign keys, constraints, and ACID transactions
✅ **RESTful API** - Standard HTTP endpoints with JSON responses

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Flask 3.1.3 |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Language | Python 3.8+ |

---

## Project Structure

```
finance-tracker/
├── app.py              # Main Flask API with all endpoints
├── models.py           # SQLAlchemy ORM models (Account, Category, Transaction)
├── config.py           # Configuration and database connection
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (DATABASE_URL)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

---

## Database Schema

### Accounts Table
- `id` (PK): Account identifier
- `name` (UNIQUE): Account name
- `balance`: Current account balance
- `created_at`: Creation timestamp

### Categories Table
- `id` (PK): Category identifier
- `name` (UNIQUE): Category name
- `type`: Category type (income/expense)
- `created_at`: Creation timestamp

### Transactions Table
- `id` (PK): Transaction identifier
- `account_id` (FK): References accounts.id
- `category_id` (FK): References categories.id
- `amount`: Transaction amount (CHECK amount > 0)
- `date`: Transaction date
- `description`: Optional transaction description
- `created_at`: Creation timestamp

**Relationships:**
- One account has many transactions (1:N)
- One category has many transactions (1:N)
- DELETE account cascades to delete transactions

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL running
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/finance-tracker.git
   cd finance-tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create PostgreSQL database**
   ```bash
   createdb finance_tracker
   ```

5. **Create .env file**
   ```bash
   echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/finance_tracker" > .env
   ```
   
   Update `password` with your PostgreSQL password.

6. **Run the application**
   ```bash
   python app.py
   ```
   
   Server runs on `http://localhost:5000`

---

## API Endpoints

### Accounts

**Get all accounts**
```bash
GET /accounts
```

**Create account**
```bash
POST /accounts
Content-Type: application/json

{"name": "Checking Account"}
```

**Get account by ID**
```bash
GET /accounts/<account_id>
```

---

### Categories

**Get all categories**
```bash
GET /categories
```

**Create category**
```bash
POST /categories
Content-Type: application/json

{"name": "Salary", "type": "income"}
```

---

### Transactions

**Get all transactions (with filters)**
```bash
GET /transactions
GET /transactions?account_id=1
GET /transactions?category_id=1
GET /transactions?start_date=2024-01-01&end_date=2024-12-31
```

**Create transaction**
```bash
POST /transactions
Content-Type: application/json

{
  "account_id": 1,
  "category_id": 1,
  "amount": 5000,
  "date": "2024-05-10",
  "description": "Monthly salary"
}
```

**Delete transaction**
```bash
DELETE /transactions/<transaction_id>
```

---

### Analytics

**Get account summary**
```bash
GET /analytics/summary/<account_id>
```

Response:
```json
{
  "account_name": "Checking Account",
  "current_balance": 5000.00,
  "total_income": 5000.00,
  "total_expense": 0.00,
  "net": 5000.00,
  "transaction_count": 1
}
```

**Get spending by category**
```bash
GET /analytics/by-category/<account_id>
```

Response:
```json
[
  {
    "category": "Salary",
    "type": "income",
    "total": 5000.00,
    "count": 1
  }
]
```

---

## Testing

### Example API Flow

```bash
# 1. Create account
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name":"Checking"}'

# 2. Create income category
curl -X POST http://localhost:5000/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Salary","type":"income"}'

# 3. Create expense category
curl -X POST http://localhost:5000/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Groceries","type":"expense"}'

# 4. Add income transaction
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -d '{"account_id":1,"category_id":1,"amount":5000,"date":"2024-05-10","description":"Salary"}'

# 5. Add expense transaction
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -d '{"account_id":1,"category_id":2,"amount":200,"date":"2024-05-11","description":"Weekly groceries"}'

# 6. View summary
curl http://localhost:5000/analytics/summary/1

# 7. View by category
curl http://localhost:5000/analytics/by-category/1
```

---

## Deployment

### Deploy to Railway

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit: Finance Tracker API"
   git push origin main
   ```

2. **Create Railway project**
   - Go to [railway.app](https://railway.app)
   - Connect your GitHub repository
   - Select this project

3. **Add PostgreSQL plugin**
   - In Railway dashboard, click "Add"
   - Select "PostgreSQL"
   - Railway auto-configures DATABASE_URL

4. **Deploy**
   - Railway auto-deploys on push to main
   - View logs in dashboard

---

## Key Design Decisions

### Schema Design
- **Normalization:** 3-table design avoids redundancy
- **Foreign Keys:** Enforce referential integrity at DB level
- **Cascading Deletes:** Account deletion auto-removes transactions
- **Constraints:** CHECK ensures amount > 0

### API Design
- **RESTful:** Standard HTTP verbs (GET, POST, DELETE)
- **Separation of Concerns:** Each endpoint does one thing
- **Error Handling:** Meaningful error messages with HTTP status codes
- **Data Validation:** Database constraints + application validation

### ORM Usage
- **SQLAlchemy:** Cross-database compatibility, SQL injection prevention
- **Relationships:** Auto-handle JOINs and foreign key management
- **Query Optimization:** Indexing for frequently queried columns

---

## Learning Outcomes

This project teaches:

1. **Database Design**
   - Normalization and relationships
   - Foreign keys and constraints
   - Index optimization

2. **Python Web Framework**
   - Flask routing and request handling
   - SQLAlchemy ORM patterns
   - Error handling and validation

3. **API Design**
   - RESTful principles
   - JSON serialization
   - HTTP status codes

4. **Data Integrity**
   - ACID transactions
   - Referential integrity
   - Constraint enforcement

5. **Deployment**
   - Environment management
   - Cloud deployment
   - Production considerations

---

## Future Enhancements

- [ ] User authentication (JWT)
- [ ] Budget limits and alerts
- [ ] Recurring transactions
- [ ] Data export (CSV/PDF)
- [ ] Transaction tags/notes
- [ ] Multi-user support
- [ ] Advanced analytics (charts, trends)
- [ ] Mobile app integration

---

## License

MIT License - feel free to use this project for learning and portfolio purposes.

---

## Author

Built as a learning project for understanding PostgreSQL, SQLAlchemy, and REST API design.
