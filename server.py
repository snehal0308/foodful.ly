from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import time
import folium
from datetime import datetime
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for
app = Flask(__name__)



ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app.secret_key = env.get("APP_SECRET_KEY")


oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# routes

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/select")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# db for user roles
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food06.db'
db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Text, nullable=False)
with app.app_context():
    db.create_all()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    quantity = db.Column(db.String(100))
    date_created = db.column(datetime.now())
    original_price =  db.Column(db.String(100))
    discounted_price  = db.Column(db.String(100))


class Grocery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.Text, nullable=False)
    selling = db.Column(db.Text, nullable=False)
    contact = db.Column(db.Text, primary_key=True)
    store_name = db.Column(db.Text, nullable=False)
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))



@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    quantity1 = request.form.get("quantity")
    original_price = request.form.get("original_price")
    discounted_price = request.form.get("discounted_price")
    new_product = Product(title=title,original_price=original_price,discounted_price=discounted_price, quantity=quantity1)
    db.session.add(new_product)
    db.session.commit()
    return redirect(url_for("grocery"))

@app.route("/update/<int:product_id>")
def update(product_id):
    product = Product.query.filter_by(id=product_id).first()
    db.session.commit()
    return redirect(url_for("grocery"))


@app.route("/delete/<int:product_id>")
def delete(product_id):
    product = Product.query.filter_by(id=product_id).first()
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("grocery"))
@app.route("/grocery", methods=["GET", "POST"])
def grocery():
    if request.method == "POST":
    
        location1 = request.form.get("location")
        if request.form.get("selling")=="pickup":
            type = "pickup"
        elif request.form.get("selling")== "delivery":
            type = "delivery"
        else :
            type = "Both"
        contact1 = request.form.get("contact")
        store_name1 = request.form.get("store_name1")

        new_profile = Grocery(location=location1)
        db.session.add(new_profile)
        db.session.commit()
        return render_template("/grocery")
    else:
        product_list = Product.query.all()
        return render_template("grocery.html", product_list=product_list)
@app.route("/profile")
def profile():
    product_list = Product.query.all()
    return render_template("profile.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4),  product_list=product_list)

@app.route("/map", methods=["GET", "POST"])
def map():
        map = folium.Map(location=[19.024859493205323, 73.01770031221047], zoom_start=10)
        shapesLayer = folium.FeatureGroup(name="circles").add_to(map)

        circlesData = [
    [18.99088229413845, 73.02481844164797, 80000, 'blueberry store'],
    [19.03264897877667, 73.05872737768303, 60000, 'greenberry store'],
    [18.976653936000957, 73.04756938916539, 90000, 'berrylicious store']
]

        pop = []

        for cData in circlesData:
            folium.Marker(location=[cData[0], cData[1]],
            radius=cData[2],
            weight=5,
            color='green',
            fill_color='red',
            
            popup=folium.Popup("""<h2>Greenberry store</h2><br/>
                    <b>contact no: 9123456890</b><br/>
                    <b>Service type: Pick up</b>
                    <img src="static/grocery.jpg" alt="Trulli" style="max-width:100%;max-height:100%">
                    <a href="/profile">Greenberry store</a>""", max_width=500)
                  ).add_to(shapesLayer)

            

        folium.LayerControl().add_to(map)

        return map._repr_html_()


@app.route("/select", methods=["GET", "POST"])
def select():
    if request.method == 'POST':
        if request.form['role'] == 'grocery':
            role = User(role="Grocery")
        elif request.form['role'] == 'customer':
            role = User(role="Customer")
        db.session.add(role)
        db.session.commit()
        print("submitted")
        return redirect('/map')
    return render_template("select.html")
# fix adding updating roles and error: no table user - fixed 


@app.route("/contact", methods=["GET", "POST"])
def contact():
        return render_template("contact.html")




if __name__ == "__main__":
    app.run(debug=True)