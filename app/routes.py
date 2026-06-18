from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, mail, limiter
from app.models import User, Watchlist, PriceAlert
from flask_mail import Message
import requests
import os
from app.models import User, Watchlist, PriceAlert, Portfolio, Holding, Trade

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')

@main.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('main.register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password, is_verified=False)
        db.session.add(new_user)
        db.session.commit()

        token = new_user.get_verification_token()
        msg = Message('Verify Your Email - InvestDash', recipients=[email])
        msg.body = f'''Welcome to InvestDash, {username}!

Please click the link below to verify your email address:

http://127.0.0.1:5000/verify-email/{token}

This link expires in 24 hours.
'''
        mail.send(msg)

        flash('Account created! Please check your email to verify your account.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Please verify your email before logging in. Check your inbox!', 'warning')
                return redirect(url_for('main.login'))
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/watchlist')
@login_required
def watchlist():
    return render_template('watchlist.html')

@main.route('/news')
@login_required
def news():
    return render_template('news.html')

@main.route('/calculator')
@login_required
def calculator():
    return render_template('calculator.html')

@main.route('/compare')
@login_required
def compare():
    return render_template('compare.html')

@main.route('/alerts')
@login_required
def alerts_page():
    return render_template('alerts.html')

@main.route('/profile')
@login_required
def profile():
    watchlist_count = Watchlist.query.filter_by(user_id=current_user.id).count()
    return render_template('profile.html', watchlist_count=watchlist_count)

@main.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not bcrypt.check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect!', 'danger')
        return redirect(url_for('main.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match!', 'danger')
        return redirect(url_for('main.profile'))

    current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    flash('Password updated successfully!', 'success')
    return redirect(url_for('main.profile'))

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@main.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'''To reset your password, click the link below:

http://127.0.0.1:5000/reset-password/{token}

This link expires in 30 minutes.

If you did not request a password reset, please ignore this email.
'''
            mail.send(msg)
        flash('If that email exists, a reset link has been sent!', 'info')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')

@main.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset link!', 'danger')
        return redirect(url_for('main.forgot_password'))
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.reset_password', token=token))
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash('Password reset successfully! Please login.', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', token=token)

@main.route('/verify-email/<token>')
def verify_email(token):
    user = User.verify_email_token(token)
    if not user:
        flash('Invalid or expired verification link!', 'danger')
        return redirect(url_for('main.login'))
    if user.is_verified:
        flash('Email already verified! Please login.', 'info')
    else:
        user.is_verified = True
        db.session.commit()
        flash('Email verified successfully! You can now login.', 'success')
    return redirect(url_for('main.login'))

@main.route('/api/news')
@login_required
def get_news():
    category = request.args.get('category', 'general')
    api_key = os.getenv('FINNHUB_API_KEY')
    url = f'https://finnhub.io/api/v1/news?category={category}&token={api_key}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return jsonify(data[:12])
    except Exception as e:
        return jsonify([])

@main.route('/api/watchlist')
@login_required
def get_watchlist():
    items = Watchlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'symbol': item.symbol, 'note': item.note or ''} for item in items])

@main.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    symbol = request.json.get('symbol')
    existing = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    if existing:
        return jsonify({'success': False, 'message': 'Stock already in watchlist!'})
    new_stock = Watchlist(symbol=symbol, user_id=current_user.id)
    db.session.add(new_stock)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/watchlist/remove', methods=['POST'])
@login_required
def remove_from_watchlist():
    symbol = request.json.get('symbol')
    item = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({'success': True})

@main.route('/api/watchlist/note', methods=['POST'])
@login_required
def update_note():
    symbol = request.json.get('symbol')
    note = request.json.get('note')
    item = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    if item:
        item.note = note
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@main.route('/api/stock-price')
@login_required
def get_stock_price():
    symbol = request.args.get('symbol')
    api_key = os.getenv('FINNHUB_API_KEY')
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}'
    try:
        response = requests.get(url, timeout=10)
        return jsonify(response.json())
    except:
        return jsonify({})

@main.route('/api/stock-history')
@login_required
def get_stock_history():
    symbol = request.args.get('symbol')
    resolution = request.args.get('resolution', 'D')
    import yfinance as yf

    period_map = {'W': '1mo', 'M': '6mo', 'D': '1y'}
    interval_map = {'W': '1d', 'M': '1d', 'D': '1d'}

    period = period_map.get(resolution, '1y')
    interval = interval_map.get(resolution, '1d')

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return jsonify({})
        timestamps = [int(t.timestamp()) for t in hist.index]
        closes = [round(float(c), 2) for c in hist['Close']]
        return jsonify({'t': timestamps, 'c': closes, 's': 'ok'})
    except:
        return jsonify({})

@main.route('/api/alerts')
@login_required
def get_alerts():
    alerts = PriceAlert.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': a.id, 'symbol': a.symbol, 'target_price': a.target_price,
        'direction': a.direction, 'triggered': a.triggered
    } for a in alerts])

@main.route('/api/alerts/add', methods=['POST'])
@login_required
def add_alert():
    data = request.json
    alert = PriceAlert(
        symbol=data['symbol'].upper(),
        target_price=float(data['target_price']),
        direction=data['direction'],
        user_id=current_user.id
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/alerts/remove', methods=['POST'])
@login_required
def remove_alert():
    alert_id = request.json.get('id')
    alert = PriceAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    if alert:
        db.session.delete(alert)
        db.session.commit()
    return jsonify({'success': True})

@main.route('/api/alerts/check')
@login_required
def check_alerts():
    alerts = PriceAlert.query.filter_by(user_id=current_user.id, triggered=False).all()
    triggered_now = []
    api_key = os.getenv('FINNHUB_API_KEY')
    for alert in alerts:
        try:
            url = f'https://finnhub.io/api/v1/quote?symbol={alert.symbol}&token={api_key}'
            res = requests.get(url, timeout=5).json()
            price = res.get('c', 0)
            hit = (alert.direction == 'above' and price >= alert.target_price) or \
                  (alert.direction == 'below' and price <= alert.target_price)
            if hit:
                alert.triggered = True
                db.session.commit()
                triggered_now.append({
                    'symbol': alert.symbol, 'target_price': alert.target_price,
                    'direction': alert.direction, 'current_price': price
                })
        except:
            pass
    return jsonify(triggered_now)

@main.route('/trading')
@login_required
def trading():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id, cash_balance=10000.0)
        db.session.add(portfolio)
        db.session.commit()
    return render_template('trading.html')

@main.route('/api/portfolio')
@login_required
def get_portfolio():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id, cash_balance=10000.0)
        db.session.add(portfolio)
        db.session.commit()

    holdings = Holding.query.filter_by(user_id=current_user.id).all()
    api_key = os.getenv('FINNHUB_API_KEY')

    holdings_data = []
    total_holdings_value = 0
    for h in holdings:
        try:
            url = f'https://finnhub.io/api/v1/quote?symbol={h.symbol}&token={api_key}'
            res = requests.get(url, timeout=5).json()
            current_price = res.get('c', 0)
        except:
            current_price = 0
        market_value = current_price * h.quantity
        profit_loss = market_value - (h.avg_price * h.quantity)
        profit_loss_pct = (profit_loss / (h.avg_price * h.quantity) * 100) if h.avg_price > 0 else 0
        total_holdings_value += market_value
        holdings_data.append({
            'symbol': h.symbol, 'quantity': h.quantity, 'avg_price': h.avg_price,
            'current_price': current_price, 'market_value': market_value,
            'profit_loss': profit_loss, 'profit_loss_pct': profit_loss_pct
        })

    total_value = portfolio.cash_balance + total_holdings_value
    total_profit_loss = total_value - 10000.0

    return jsonify({
        'cash_balance': portfolio.cash_balance,
        'holdings': holdings_data,
        'total_holdings_value': total_holdings_value,
        'total_value': total_value,
        'total_profit_loss': total_profit_loss,
        'total_profit_loss_pct': (total_profit_loss / 10000.0 * 100)
    })

@main.route('/api/trade/buy', methods=['POST'])
@login_required
def buy_stock():
    data = request.json
    symbol = data['symbol'].upper()
    quantity = float(data['quantity'])

    api_key = os.getenv('FINNHUB_API_KEY')
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}'
    res = requests.get(url, timeout=5).json()
    price = res.get('c', 0)

    if price <= 0:
        return jsonify({'success': False, 'message': 'Invalid stock symbol!'})

    total_cost = price * quantity
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()

    if portfolio.cash_balance < total_cost:
        return jsonify({'success': False, 'message': 'Insufficient funds!'})

    portfolio.cash_balance -= total_cost

    holding = Holding.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    if holding:
        new_total_qty = holding.quantity + quantity
        new_avg_price = ((holding.avg_price * holding.quantity) + total_cost) / new_total_qty
        holding.quantity = new_total_qty
        holding.avg_price = new_avg_price
    else:
        holding = Holding(user_id=current_user.id, symbol=symbol, quantity=quantity, avg_price=price)
        db.session.add(holding)

    trade = Trade(user_id=current_user.id, symbol=symbol, trade_type='buy',
                  quantity=quantity, price=price, total=total_cost)
    db.session.add(trade)
    db.session.commit()

    return jsonify({'success': True, 'message': f'Bought {quantity} shares of {symbol} at ${price:.2f}'})

@main.route('/api/trade/sell', methods=['POST'])
@login_required
def sell_stock():
    data = request.json
    symbol = data['symbol'].upper()
    quantity = float(data['quantity'])

    holding = Holding.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    if not holding or holding.quantity < quantity:
        return jsonify({'success': False, 'message': 'You do not own enough shares!'})

    api_key = os.getenv('FINNHUB_API_KEY')
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}'
    res = requests.get(url, timeout=5).json()
    price = res.get('c', 0)

    total_value = price * quantity
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    portfolio.cash_balance += total_value

    holding.quantity -= quantity
    if holding.quantity <= 0.0001:
        db.session.delete(holding)

    trade = Trade(user_id=current_user.id, symbol=symbol, trade_type='sell',
                  quantity=quantity, price=price, total=total_value)
    db.session.add(trade)
    db.session.commit()

    return jsonify({'success': True, 'message': f'Sold {quantity} shares of {symbol} at ${price:.2f}'})

@main.route('/api/trade/history')
@login_required
def trade_history():
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.timestamp.desc()).limit(20).all()
    return jsonify([{
        'symbol': t.symbol, 'type': t.trade_type, 'quantity': t.quantity,
        'price': t.price, 'total': t.total, 'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M')
    } for t in trades])

@main.route('/api/stock-overview')
@login_required
def get_stock_overview():
    symbol = request.args.get('symbol')
    api_key = os.getenv('FINNHUB_API_KEY')

    try:
        profile_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={api_key}'
        profile = requests.get(profile_url, timeout=8).json()

        metrics_url = f'https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={api_key}'
        metrics_res = requests.get(metrics_url, timeout=8).json()
        metric = metrics_res.get('metric', {})

        quote_url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}'
        quote = requests.get(quote_url, timeout=8).json()

        return jsonify({
            'profile': profile,
            'metric': {
                'peTTM': metric.get('peBasicExclExtraTTM'),
                'epsTTM': metric.get('epsBasicExclExtraItemsTTM'),
                'week52High': metric.get('52WeekHigh'),
                'week52Low': metric.get('52WeekLow'),
                'beta': metric.get('beta'),
                'dividendYield': metric.get('dividendYieldIndicatedAnnual'),
                'roe': metric.get('roeTTM'),
                'roa': metric.get('roaTTM'),
                'grossMargin': metric.get('grossMarginTTM'),
                'netMargin': metric.get('netProfitMarginTTM'),
                'operatingMargin': metric.get('operatingMarginTTM'),
                'revenueGrowth': metric.get('revenueGrowthTTMYoy'),
                'epsGrowth': metric.get('epsGrowthTTMYoy'),
                'currentRatio': metric.get('currentRatioAnnual'),
                'debtToEquity': metric.get('totalDebt/totalEquityAnnual'),
                'bookValuePerShare': metric.get('bookValuePerShareAnnual'),
                'revenuePerShare': metric.get('revenuePerShareTTM'),
            },
            'quote': quote
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@main.route('/api/stock-news')
@login_required
def get_stock_news():
    symbol = request.args.get('symbol')
    api_key = os.getenv('FINNHUB_API_KEY')
    import datetime
    to_date = datetime.date.today().isoformat()
    from_date = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()
    try:
        url = f'https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={api_key}'
        response = requests.get(url, timeout=8)
        data = response.json()
        return jsonify(data[:10])
    except Exception as e:
        return jsonify([])