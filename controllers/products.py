from flask import Blueprint, request, make_response, render_template, session, redirect, url_for, g, Response, flash
from models.user import User, db, SOFIEBIO_ACCOUNTID
from models.account import Account
import json
import os
import datetime
import email_sender
import modules.sfdc as sfdc
import threading

SIM_PRODUCTS = os.environ.get('SIM_PRODUCTS', 'True') == 'True'
productscontroller = Blueprint("productscontroller", __name__, template_folder="../templates", url_prefix="/product")

@productscontroller.route("/", methods=["GET"])
def index():
    runningUserAccount = Account.query.filter_by(id=g.user.AccountID).first()
    running_user = g.user.to_hash()
    return render_template('/products/index.html',
                           runninguser=json.dumps(running_user),
                           simProducts=json.dumps(SIM_PRODUCTS),
                           runningUserAccount=json.dumps(runningUserAccount.to_hash()))
@productscontroller.route("/new_order/", methods=["GET"])
def new_order():
    runningUserAccount = Account.query.filter_by(id=g.user.AccountID).first()
    running_user = g.user.to_hash()
    return render_template('/products/product-list.html',
                           runninguser=running_user,
                           simProducts=json.dumps(SIM_PRODUCTS),
                           cart = True,
                           runningUserAccount=json.dumps(runningUserAccount.to_hash()))

@productscontroller.route("/<int:product_id>/", methods=["GET"])
def product_detail(product_id):
    runningUserAccount = Account.query.filter_by(id=g.user.AccountID).first()
    running_user = g.user.to_hash()
    return render_template('/products/detail.html',
                           runninguser=running_user,
                           simProducts=SIM_PRODUCTS,
                           runningUserAccount=json.dumps(runningUserAccount.to_hash()))



@productscontroller.route("/set_cart/", methods=["POST"])
def set_cart():
    cart = request.json
    session['cart'] = cart
    response = Response("OK")
    return response

@productscontroller.route("/cart/", methods=["GET"])
def cart():
    running_user = g.user.to_hash()
    cart = session.get('cart', [])
    #return Response(cart, content_type='application/json')
    return render_template('/products/cart.html',
                           runninguser=running_user,
                           quote_generated = True)

@productscontroller.route("/products", methods=["GET"])
def get_pdts():
    return Response(json.dumps(get_products()), content_type='application/json')

@productscontroller.route("/clear_cart/", methods=["GET"])
def clear_cart():
    if 'cart' in session:
        del session['cart']
    return redirect(url_for(".index"))

@productscontroller.route("/price_points", methods=["POST"])
def get_price_points():
    productids = request.json

    pdt_prices = {}
    pbes = pricepoints(productids)
    for pbe in pbes:
        pdt_prices[pbe['Product2Id']] = pbe['UnitPrice']

    return Response(json.dumps(pdt_prices), content_type='application/json')

@productscontroller.route("/place_order", methods=["POST"])
def place_order():
    line_items = request.json

    account = g.user.account
    account_id = account.SFDC_ID
    opportunity_name = account.Name + ' - SPN ORDER'

    create_thread = threading.Thread(target=create_opportunity_with_olis, args=(account_id,opportunity_name, line_items,))
    create_thread.start()
    return "OK"

def create_opportunity_with_olis(account_sfdc, opportunity_name, products):
    product_ids = [product['Id'] for product in products]
    product_ids = "'" + "\',\'".join(product_ids) + "'"
    try:
        sf = sfdc.get_instance()
        pbes = sf.query("Select Id,Product2Id,UnitPrice from PricebookEntry where Product2Id in (%s) and Pricebook2.IsStandard=True" % product_ids)
        pdt_to_price = {}
        for pdt in pbes['records']:
            pdt_to_price[pdt['Product2Id']] = pdt
    except Exception as e:
        err = str(e) + "\n Please reset your SFDC credentials \n Failed to create Opportunity"
        err += "\n attempting to create %s" % products + \
               "\n Account %s" % account_sfdc
        email_sender.auto_report_bug(err)
        raise e

    close_date = datetime.datetime.now().isoformat()

    try:
        opty = {"AccountId": account_sfdc,
                                         "Name": opportunity_name,
                                         "StageName": "Actively Communicating",
                                         "CloseDate": close_date}
        #
        opportunity = sf.Opportunity.create(opty)
    except Exception as e:
        print 'err'
        err = str(e) + "\n Failed to create the opportunity" + \
                       "\n Opportunity %s " % opty + \
                       "\n %s" % products
        email_sender.auto_report_bug(err)
        raise e

    try:
        opporunity_id = opportunity['id'] if 'id' in opportunity else None
        for line_item in products:
            pdt_id = line_item['Id']
            pbe = pdt_to_price[pdt_id]['Id']
            quantity = int(line_item['Quantity'])
            if quantity > 0:
                unit_price = pdt_to_price[pdt_id]['UnitPrice']
                oli = {
                    "OpportunityId": opporunity_id,
                    "PricebookEntryId": pbe,
                    "UnitPrice": unit_price,
                    "Quantity": quantity
                }
                resp = sf.OpportunityLineItem.create(oli)
    except Exception as e:
        err = str(e) + "Failed to create the OLI" + \
                       "\n For Opportunity %s" % opporunity_id + \
                       "Products %s" % products
        email_sender.auto_report_bug(err)


def get_products():
    sf = sfdc.get_instance()
    products = sf.query("Select Id, Name, Family, Description,UnitType__c,"
                        "                 (Select Name, Product__r.Name, Product__r.Id, Id from AddOnProducts__r order by Product__r.Name),"
                        "                 (Select Name, Id, Quantity__c,Product__r.Name,Product__r.Id from Breakdown_Products__r order by Name) " +
                        "   from Product2 " +
                        "where Display_In_SPN__c=True")

    return products['records']

def pricepoints(productids):
    sf = sfdc.get_instance()
    pdtids = "'" + "\',\'".join(productids) + "'"
    products = sf.query("Select Id,UnitPrice,Product2Id from PricebookEntry where Product2Id in (%s) and Pricebook2.IsStandard = True" % pdtids)

    return products['records']