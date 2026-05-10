from flask import Flask, request, jsonify
from models import db, Account, Category, Transaction
from config import Config
from datetime import datetime
from sqlalchemy import func
from decimal import Decimal

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
            account.balance += Decimal(str(data['amount']))
        else:
            account.balance -= Decimal(str(data['amount']))
        
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
            account.balance -= Decimal(str(transaction.amount))
        else:
            account.balance += Decimal(str(transaction.amount))
        
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
