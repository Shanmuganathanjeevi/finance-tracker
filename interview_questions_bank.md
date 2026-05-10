# PostgreSQL & API Design - Interview Question Bank

## Level 1: Fundamentals (Warm-up)

### Q1: What is a primary key and why do we need it?
**Answer:**
- Unique identifier for each row
- Ensures no duplicate records
- Enables fast lookups and relationships
- Every table should have one

**Follow-up:** "Why not just use the data itself as a key (e.g., email as PK)?"
- Email can change, lose uniqueness
- Primary key is immutable identifier
- Easier to reference in foreign keys

---

### Q2: What's the difference between PRIMARY KEY and UNIQUE constraint?
**Answer:**
| Feature | PK | UNIQUE |
|---------|----|----|
| Null values | NOT allowed | Allowed |
| Multiple per table | Only 1 | Multiple |
| Auto-indexed | Yes | Yes |
| Uniqueness | Enforced | Enforced |

**Example:** Account name is UNIQUE but not PK (PK is id)

---

### Q3: What are FOREIGN KEYS and what do they do?
**Answer:**
- Link rows in one table to another table
- Enforce referential integrity
- Prevent creating transactions for non-existent accounts
- Enable database to maintain relationships

**In your project:**
```sql
account_id INTEGER NOT NULL REFERENCES accounts(id)
-- This ensures account_id in transactions must exist in accounts.id
```

---

### Q4: What is data normalization?
**Answer:**
- Organizing data to reduce redundancy
- Your schema uses 3 tables instead of 1 mega table
- Benefits:
  - No duplicate category names
  - Easy updates (change category name once)
  - Smaller storage
  - Faster queries

**Bad design (denormalized):**
```
transactions: id, amount, date, category_name, category_type, account_name
-- category_name and category_type repeat for every transaction
```

**Good design (normalized):**
```
transactions: id, amount, date, category_id, account_id
categories: id, name, type
accounts: id, name, balance
```

---

## Level 2: Intermediate (Schema & Design)

### Q5: Explain your database schema design for the Finance Tracker
**Answer:**
"I designed a 3-table normalized schema:

1. **accounts**: Stores financial accounts with id (PK), name (UNIQUE), balance, created_at
2. **categories**: Reusable transaction types (income/expense) with CHECK constraint
3. **transactions**: Links accounts and categories via foreign keys

Foreign keys ensure:
- Can't create transaction for non-existent account
- Can't create transaction for non-existent category
- Deleting account auto-deletes transactions (CASCADE)

This avoids storing category/account names in every transaction row."

---

### Q6: What happens if you delete an account?
**Answer:**
- With CASCADE: All transactions automatically deleted
- Without CASCADE: Delete fails (referential integrity error)

**Your choice (CASCADE):**
```sql
account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE
```

"This is appropriate for accounts because when an account is deleted, its transactions are meaningless without the account context."

---

### Q7: Why did you use CHECK constraints on amount?
**Answer:**
- Prevents negative amounts at database level
- Better than application validation alone
- Database enforces rules even if app has bugs
- Atomic (instantly prevented)

```sql
amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0)
```

"If someone bypasses the Flask app and inserts directly via SQL, the constraint still prevents invalid data."

---

### Q8: What are indexes and why did you add them?
**Answer:**
- Speed up SELECT queries by organizing data
- Your indexes:
  - `idx_transactions_account_id`: Speeds up "get all transactions for account X"
  - `idx_transactions_category_id`: Speeds up filtering by category
  - `idx_transactions_date`: Speeds up date range queries (very common in finance)

**How they work:**
- Like a book index (alphabetical)
- Instead of scanning all 1M rows, jump to matching rows
- Tradeoff: Slower writes, faster reads (worth it for finance apps)

**Without index on date:**
```sql
SELECT * FROM transactions WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
-- Scans all rows (slow if millions)
```

**With index:**
```sql
-- Jumps to rows with matching dates (fast)
```

---

### Q9: What is a relationship? Name the 3 types
**Answer:**
1. **One-to-Many (1:N):** One account has many transactions
   ```
   accounts.id → transactions.account_id
   ```

2. **One-to-One (1:1):** One user has one profile
   ```
   users.id → profiles.user_id (UNIQUE)
   ```

3. **Many-to-Many (M:N):** Many students, many courses (via junction table)
   ```
   students → student_courses → courses
   ```

**In your project:** Only 1:N (accounts-to-transactions, categories-to-transactions)

---

### Q10: What is ACID and why does it matter?
**Answer:**
- **A**tomicity: Transaction all-or-nothing (amount updates OR it doesn't)
- **C**onsistency: Database remains valid (balance can't go to -$10 if CHECK prevents it)
- **I**solation: Concurrent transactions don't interfere
- **D**urability: Saved data persists even if server crashes

**Example in your app:**
```python
# If this crashes midway, ACID ensures:
# - Balance updates AND transaction created (atomic)
# - OR neither happens (no partial state)
db.session.add(transaction)
account.balance += amount
db.session.commit()
```

---

## Level 3: Advanced (Optimization & Scale)

### Q11: How would you optimize the "get summary by category" query for 10M transactions?
**Current query:**
```python
query = db.session.query(
    Category.name,
    func.sum(Transaction.amount)
).join(Transaction).group_by(Category.id)
```

**Optimizations:**
1. **Index on (account_id, date):** For range filtering
2. **Materialized View:** Pre-compute summary hourly
3. **Partitioning:** Split transactions by month/year
4. **Denormalize:** Store category_total in categories table (update on each transaction)

**Tradeoffs:**
- Materialized views: Faster reads, stale data
- Denormalization: Faster reads, harder updates
- Partitioning: Faster queries on recent data

---

### Q12: How would you handle concurrent transactions?
**Scenario:** Two requests add $100 and $200 to account balance simultaneously

**Problem without locking:**
```
Request 1: Read balance (1000) → Add 100 → Write (1100) ❌
Request 2: Read balance (1000) → Add 200 → Write (1200) ❌
Expected: 1300, Got: 1200 (lost $100)
```

**Solution:**
1. **Database transactions (ACID):** Wrap in transaction
   ```python
   db.session.begin()
   account = Account.query.with_for_update().get(account_id)
   account.balance += amount
   db.session.commit()
   ```

2. **Row-level locking:** `with_for_update()` locks row while updating

3. **Optimistic locking:** Add version column, check if changed

**Best for finance:** Option 1 (ACID transactions with locking)

---

### Q13: What if a transaction fails midway (network dies)?
**Answer:**
PostgreSQL's ACID properties handle this:

```python
try:
    db.session.add(transaction)
    account.balance += amount
    db.session.commit()  # All-or-nothing
except Exception:
    db.session.rollback()  # Undo everything
```

**Result:**
- If commit succeeds: Both balance + transaction saved
- If commit fails: Neither saved (no partial state)
- Rollback undoes any changes made so far

---

### Q14: How to audit who changed what (audit trail)?
**Solution: Audit Table**
```sql
CREATE TABLE transaction_audit (
    id SERIAL PRIMARY KEY,
    transaction_id INT,
    action VARCHAR(20),  -- 'INSERT', 'UPDATE', 'DELETE'
    old_amount DECIMAL,
    new_amount DECIMAL,
    changed_at TIMESTAMP,
    changed_by VARCHAR(100)
);
```

**Options:**
1. **Trigger (automatic):** Database logs every change
2. **Explicit logging (app-level):** Log in Python
3. **Temporal tables:** PostgreSQL keeps version history

---

### Q15: How to prevent overdrafts?
**Solution:**
```python
@app.route('/transactions', methods=['POST'])
def create_transaction():
    account = Account.query.get(account_id)
    if account.balance - amount < 0:
        return jsonify({'error': 'Insufficient funds'}), 400
```

**Or at database level:**
```sql
ALTER TABLE accounts ADD CONSTRAINT check_balance 
CHECK (balance >= 0);
```

**Better approach:**
- Validation in app (fast feedback)
- Constraint in DB (final safety net)

---

## Level 4: Design Decisions (Why you made choices)

### Q16: Why did you use SQLAlchemy instead of raw SQL?
**Answer:**
- **ORM abstraction:** Write Python, not SQL
- **Prevents SQL injection:** Parameters auto-escaped
- **Cross-database:** Same code works on PostgreSQL, MySQL, SQLite
- **Relationship loading:** `.relationships` handle JOINs automatically

**Tradeoff:** Slightly slower than raw SQL, but safer and cleaner

---

### Q17: Why separate REST endpoints instead of one mega endpoint?
**Answer:**
- **Separation of concerns:** Each endpoint does one thing
- **Standards:** REST conventions (GET = read, POST = create, DELETE = delete)
- **Caching:** Easy to cache GET requests
- **Testing:** Test each endpoint independently
- **Scalability:** Can optimize each endpoint separately

**Bad design:**
```
POST /query with {"action": "create_account"}  ❌
```

**Good design:**
```
POST /accounts                                 ✅
```

---

### Q18: Why use DECIMAL instead of FLOAT for money?
**Answer:**
- **FLOAT:** Binary representation, rounding errors
  ```
  0.1 + 0.2 = 0.30000000000000004  ❌
  ```
- **DECIMAL:** Exact decimal arithmetic
  ```
  0.1 + 0.2 = 0.3  ✅
  ```

**Never use FLOAT for money!**

---

### Q19: Why return account balance in JSON when you have it in DB?
**Answer:**
- Calculated property not stored (except accounts.balance)
- For transactions: always get from parent account
- Faster reads (don't recalculate every time)
- Single source of truth

**Alternative:** Recalculate on every query (slow for historical data)

---

## Level 5: Real-World Scenarios

### Q20: How would you add recurring transactions (bills)?
**Answer:**
```sql
CREATE TABLE recurring_transactions (
    id SERIAL PRIMARY KEY,
    account_id INT REFERENCES accounts(id),
    category_id INT REFERENCES categories(id),
    amount DECIMAL,
    frequency VARCHAR(20),  -- 'daily', 'weekly', 'monthly'
    next_due_date DATE,
    is_active BOOLEAN DEFAULT true
);
```

**Execution:**
- Cron job every night: Find due recurring transactions
- Auto-create transaction, update next_due_date

---

### Q21: How would you add budgets and alerts?
**Answer:**
```sql
CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    account_id INT REFERENCES accounts(id),
    category_id INT REFERENCES categories(id),
    limit_amount DECIMAL,
    period VARCHAR(20),  -- 'monthly', 'quarterly'
    reset_date DATE
);
```

**Alert logic:**
```python
# When transaction created
spent = sum(Transaction.query.filter_by(category_id=cat_id))
budget = Budget.query.filter_by(category_id=cat_id).first()

if spent > budget.limit_amount * 0.8:
    send_alert("Budget 80% used")
```

---

### Q22: How to export data (CSV/PDF)?
**Answer:**
```python
import csv
from flask import send_file

@app.route('/export/csv/<int:account_id>')
def export_csv(account_id):
    transactions = Transaction.query.filter_by(account_id=account_id).all()
    
    with open('export.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Category', 'Amount', 'Description'])
        for t in transactions:
            writer.writerow([t.date, t.category.name, t.amount, t.description])
    
    return send_file('export.csv', as_attachment=True)
```

---

## Quick Reference: Common Interview Answers

| Question | Quick Answer |
|----------|--------------|
| What is normalization? | Reducing redundancy by splitting tables |
| Why foreign keys? | Enforce referential integrity |
| Why indexes? | Speed up queries on large datasets |
| ACID means? | All-or-nothing, Consistent, Isolated, Durable |
| Why not FLOAT for money? | Rounding errors, use DECIMAL |
| Concurrent update problem? | Use database locking or transactions |
| Why REST not GraphQL? | Simpler for this project, standards-based |
| Why SQLAlchemy? | Safety, cross-database, relationships |

---

## Assessment: Test Yourself

Answer these without looking:

1. Define normalization
2. Name the 3 relationship types
3. What does CASCADE do?
4. Why index on date in finance app?
5. What's the difference between PK and UNIQUE?
6. How to prevent overdrafts?
7. Why DECIMAL not FLOAT?
8. What problem does ORM solve?
9. How to handle concurrent updates?
10. What does ACID guarantee?

**Score Guide:**
- 8-10: Interview ready
- 5-7: Review intermediate concepts
- 0-4: Watch more Udemy sections

