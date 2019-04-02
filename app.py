import json
from flask import Flask
from flask import request
from flask import render_template
app = Flask(__name__)

def simulation(roa, price, equity_rate, durable, age, interest_rate, loan_months,
               selling_price_rate=1.0, building_price_rate=0.3, running_cost_rate=0.15,
               income_decreate_rate=0.01, buy_fee_rate=0.06, sell_fee_rate=0.03, 
               loan_break_fee_rate=0.015, running_tax_rate=0.37, selling_tax_rate=0.37):
    """
    def simulation(roa, price, equity_rate, durable, age, interest_rate, loan_months,
                   selling_price_rate=1.0, building_price_rate=0.3, running_cost_rate=0.85,
                   income_decreate_rate=0.01, buy_fee_rate=0.06, sell_fee_rate=0.03, 
                   loan_break_fee_rate=0.015, running_tax_rate=0.37, selling_tax_rate=0.37):
    """
    data = []

    # INVESTMENT
    investment = price * (buy_fee_rate + equity_rate)
    
    # Pricipal on loan
    principal = price * (1 - equity_rate)
    
    # Return On Asset
    income = price * roa
    running_cost = income * running_cost_rate
    
    # monthly interest
    mi = interest_rate / 12.
    
    # Monthly Return On Loan
    mrol = principal * (mi * (1+mi) ** loan_months / ((1+mi) ** loan_months - 1))
    
    # Return On Loan
    rol = mrol * 12
    
    # Return On Loan Rate
    rolr = rol / income
    
    # Depreciation
    # Depreciation years
    dy = (age > durable) and int(0.2 * durable) or int(durable - age + age * 0.2)
    depreciation = price * building_price_rate * (1. / dy)
    
    # ROI
    next_principal = lambda p: p - (mrol - p * mi)

    cf_total = 0
    p0 = principal
    for y in range(int(loan_months/12)):
        p = p0
        for i in range(12):
            p = next_principal(p)

        interest = rol - ( p0 - p)
        p0 = p

        current_income = income * ((1 - income_decreate_rate) ** y)
        taxing_income = current_income - running_cost - interest - (y > dy and 0.1 or depreciation)
        # print("---- year %d ---" % (y + 1))
        running_tax = taxing_income * running_tax_rate
        cf_taxed = current_income - running_cost - rol - running_tax
        cf_total += cf_taxed

        # NAV
        selling_profits = selling_price_rate * price - (price - (y > dy and dy or y) * depreciation)
        selling_tax = selling_profits * selling_tax_rate
        selling_fee = price * selling_price_rate * sell_fee_rate
        loan_break_fee = p0 * loan_break_fee_rate + 6

        nav = cf_total + selling_price_rate * price - selling_tax - selling_fee - loan_break_fee - price * (buy_fee_rate) - p0

        print("CF_TAXED", current_income,  running_cost, rol, running_tax, cf_taxed)
        print('year %d NAV' % (y+1), nav, (nav-investment) / investment)
        data.append({
            'index': y+1,
            'current_income': current_income,
            'taxing_income': taxing_income,
            'running_tax': running_tax,
            'running_cost': running_cost,
            'cf_taxed': cf_taxed,
            'cf_total': cf_total,
            'selling_profits': selling_profits,
            'selling_tax': selling_tax,
            'selling_fee': selling_fee,
            'loan_break_fee': loan_break_fee,
            'nav': nav,
        })
    return {
        "params": dict(
            roa=roa, price=price, equity_rate=equity_rate, durable=durable, age=age, interest_rate=interest_rate, loan_months=loan_months,
            selling_price_rate=selling_price_rate, building_price_rate=building_price_rate, running_cost_rate=running_cost_rate,
            income_decreate_rate=income_decreate_rate, buy_fee_rate=buy_fee_rate, sell_fee_rate=sell_fee_rate, 
            loan_break_fee_rate=loan_break_fee_rate, running_tax_rate=running_tax_rate, selling_tax_rate=selling_tax_rate),
        "simulation": data,
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {}
    if request.method == 'POST':
        params = dict(request.form)
        print(params.items())
        params = dict([(k, float(v[0])) for (k, v) in params.items()])
        data = simulation(**params)
        return render_template('index.html', data=json.dumps(data['simulation']), params=data['params'])
    else :
        data = []
        params = dict(selling_price_rate=1.0, building_price_rate=0.3, running_cost_rate=0.15,
                      income_decreate_rate=0.01, buy_fee_rate=0.06, sell_fee_rate=0.03, 
                      loan_break_fee_rate=0.015, running_tax_rate=0.37, selling_tax_rate=0.37)
        return render_template('index.html', data=data, params=params)
        
