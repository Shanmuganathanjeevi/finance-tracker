# Personal Finance Tracker API - Complete Implementation Guide

## Project Overview
Build a production-grade REST API with PostgreSQL that tracks income/expenses with proper schema design, relationships, and query optimization.

**Tech Stack:** Python, Flask, PostgreSQL, SQLAlchemy

---

## Part 1: Database Schema Design

### Schema Diagram
```
accounts
├── id (PK)
├── name
├── balance
└── created_at

categories
├── id (PK)
├── name
└── type (income/expense)

transactions
├── id (PK)
├── account_id (FK → accounts)
├── category_id (FK → categories)
├── amount
├── date
├── description
└── created_at
```

### SQL Schema (Paste directly into PostgreSQL)

```sql
-- Create accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    balance DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_date ON transactions(date);
```

---

## Part 2: Flask API Implementation

### Project Structure
```
finance-tracker/
├── app.py
├── models.py
├── config.py
├── requirements.txt
└── README.md
```

### requirements.txt
```
Flask==2.3.0
Flask-SQLAlchemy==3.0.0
psycopg2-binary==2.9.0
python-dotenv==1.0.0
```

### config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/finance_tracker'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### models.py
```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'balance': float(self.balance),
            'created_at': self.created_at.isoformat()
        }

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'category_id': self.category_id,
            'amount': float(self.amount),
            'date': self.date.isoformat(),
            'description': self.description,
            'category_name': self.category.name,
            'account_name': self.account.name
        }
```

### app.py
```python
from flask import Flask, request, jsonify
from models import db, Account, Category, Transaction
from config import Config
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

# ==================== ACCOUNTS ====================

@app.route('/accounts', methods=['GET'])
def get_accounts():
    accounts = Account.query.all()
    return jsonify([acc.to_dict() for acc in accounts]), 200

@app.route('/accounts', methods=['POST'])
def create_account():
    data = request.json
    try:
        account = Account(name=data['name'])
        db.session.add(account)
        db.session.commit()
        return jsonify(account.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    account = Account.query.get(account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    return jsonify(account.to_dict()), 200

# ==================== CATEGORIES ====================

@app.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([cat.to_dict() for cat in categories]), 200

@app.route('/categories', methods=['POST'])
def create_category():
    data = request.json
    try:
        category = Category(name=data['name'], type=data['type'])
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ==================== TRANSACTIONS ====================

@app.route('/transactions', methods=['GET'])
def get_transactions():
    account_id = request.args.get('account_id', type=int)
    category_id = request.args.get('category_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Transaction.query
    
    if account_id:
        query = query.filter_by(account_id=account_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    return jsonify([txn.to_dict() for txn in transactions]), 200

@app.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    try:
        # Validate account exists
        account = Account.query.get(data['account_id'])
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Validate category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        transaction = Transaction(
            account_id=data['account_id'],
            category_id=data['category_id'],
            amount=data['amount'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            description=data.get('description')
        )
        
        # Update account balance
        if category.type == 'income':
            account.balance += float(data['amount'])
        else:
            account.balance -= float(data['amount'])
        
        db.session.add(transaction)
        db.session.commit()
        return jsonify(transaction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/transactions/<int:txn_id>', methods=['DELETE'])
def delete_transaction(txn_id):
    try:
        transaction = Transaction.query.get(txn_id)
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        account = transaction.account
        if transaction.category.type == 'income':
            account.balance -= float(transaction.amount)
        else:
            account.balance += float(transaction.amount)
        
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ==================== ANALYTICS ====================

@app.route('/analytics/summary/<int:account_id>', methods=['GET'])
def get_summary(account_id):
    account = Account.query.get(account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    transactions = Transaction.query.filter_by(account_id=account_id).all()
    
    total_income = sum(
        float(t.amount) for t in transactions 
        if t.category.type == 'income'
    )
    total_expense = sum(
        float(t.amount) for t in transactions 
        if t.category.type == 'expense'
    )
    
    return jsonify({
        'account_name': account.name,
        'current_balance': float(account.balance),
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
        'transaction_count': len(transactions)
    }), 200

@app.route('/analytics/by-category/<int:account_id>', methods=['GET'])
def get_by_category(account_id):
    result = db.session.query(
        Category.name,
        Category.type,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).join(Transaction).filter(
        Transaction.account_id == account_id
    ).group_by(Category.id, Category.name, Category.type).all()
    
    return jsonify([
        {
            'category': r[0],
            'type': r[1],
            'total': float(r[2]),
            'count': r[3]
        }
        for r in result
    ]), 200

# ==================== ERROR HANDLING ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Part 3: Setup & Deployment

### Local Setup
```bash
# 1. Create PostgreSQL database
createdb finance_tracker

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/finance_tracker" > .env

# 5. Run app
python app.py
```

### Deploy to Railway
```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git push origin main

# 2. Go to railway.app
# 3. Connect GitHub repo
# 4. Add PostgreSQL plugin
# 5. Deploy
```

---

## Part 4: API Testing (curl examples)

```bash
# Create account
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name":"Checking"}'

# Create categories
curl -X POST http://localhost:5000/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Salary","type":"income"}'

curl -X POST http://localhost:5000/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Groceries","type":"expense"}'

# Create transaction
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "account_id":1,
    "category_id":1,
    "amount":5000,
    "date":"2024-05-10",
    "description":"Monthly salary"
  }'

# Get summary
curl http://localhost:5000/analytics/summary/1

# Get by category
curl http://localhost:5000/analytics/by-category/1
```

---

## Part 5: Knowledge Assessment

### Schema Design Questions

**Q1: Why use FOREIGN KEY constraints?**
- Ensures data integrity (can't add transaction for non-existent account)
- Database enforces relationships automatically
- Prevents orphaned records

**Q2: Why CASCADE on DELETE?**
- When account is deleted, all transactions automatically deleted
- Prevents orphaned transactions
- Maintains referential integrity

**Q3: Why use CHECK constraint on amount?**
- Prevents negative amounts at database level
- Better than application-level validation
- Atomic enforcement

**Q4: Why index on date?**
- Speed up range queries (`WHERE date BETWEEN x AND y`)
- Very common filter in finance apps
- Index = faster query without scanning entire table

**Q5: Why separate accounts and categories?**
- Categories are reusable across accounts
- Normalization avoids data duplication
- Easier to add/modify categories

---

## Part 6: Interview Talking Points

### Schema Design
"I normalized the schema into 3 tables to avoid redundancy. Accounts store financial data, categories define transaction types, and transactions link them via foreign keys. I added CHECK constraints and CASCADE deletes for data integrity."

### Relationships
"Used 1:N relationships—one account has many transactions, one category has many transactions. Foreign keys ensure referential integrity at the database level, not application level."

### Indexing
"Added indexes on frequently queried columns (account_id, category_id, date) to optimize range and filter queries. This prevents full table scans for large datasets."

### Balance Calculation
"Account balance updates atomically during transaction creation. Income adds to balance, expense subtracts. Calculated in application layer but could use database triggers for additional safety."

### Query Optimization
"Used SQL aggregation (GROUP BY, SUM) for analytics instead of loading all records into Python. This is orders of magnitude faster for large datasets."

---

## Part 7: Potential Follow-up Questions

### Technical Depth
- "How would you handle concurrent transactions?" → Use database transactions, ACID properties
- "What if balance goes negative?" → Add CHECK constraint, validation
- "How to audit changes?" → Add audit table, triggers
- "How to handle multi-currency?" → Add currency column, conversion rates

### Scalability
- "How to optimize for 1M transactions?" → Partitioning by date, archiving old data
- "How to handle complex queries?" → Materialized views, read replicas
- "How to ensure high availability?" → Database replication, failover

### Real-world Considerations
- "What about transaction rollback?" → ACID transactions in database
- "How to prevent overdrafts?" → Validation before transaction
- "How to generate reports?" → SQL aggregation queries, exports

---

## Part 8: Resume Impact

**Strong bullet point:**
"Built PostgreSQL-backed REST API with normalized schema (accounts, categories, transactions), foreign key relationships, and CHECK constraints. Implemented 9 REST endpoints with filtering, aggregation analytics, and proper error handling. Deployed to Railway with automated deployments."

**What interviewers will ask:**
- Why 3 tables? (Normalization)
- How do you ensure data integrity? (Constraints, FK)
- How would you optimize queries? (Indexes)
- What about concurrent updates? (Transactions, locks)

---

## Implementation Checklist

- [ ] Udemy course sections 1-4 watched
- [ ] PostgreSQL installed locally
- [ ] Database created with schema
- [ ] Flask app running locally
- [ ] All CRUD endpoints tested
- [ ] Analytics endpoints working
- [ ] Deployed to Railway
- [ ] GitHub repo with README
- [ ] Tested via Postman/curl

---

## Next Steps After Completion

1. Add authentication (JWT tokens)
2. Add budget limits and alerts
3. Add recurring transactions
4. Add data export (CSV/PDF)
5. Add transaction tags/notes
6. Add multi-user support

