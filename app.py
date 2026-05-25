from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "farmproject123"

# ---------------- MYSQL CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Vidya@123",
    database="farm_management"
)

cursor = db.cursor()


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            session['farmer_id'] = user[4]

            # ADMIN LOGIN
            if user[3] == 'admin':

                return redirect(url_for('home'))

            # FARMER LOGIN
            else:

                return redirect(
                    url_for(
                        'farmer_details',
                        farmer_id=user[4]
                    )
                )

        else:

            return "Invalid Username or Password"

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# ---------------- HOME ----------------
@app.route('/')
def home():

    if 'role' not in session:

        return redirect(url_for('login'))

    # FARMERS CANNOT ACCESS ADMIN HOME
    if session['role'] != 'admin':

        return redirect(
            url_for(
                'farmer_details',
                farmer_id=session['farmer_id']
            )
        )

    return render_template('index.html')


# ---------------- ADD FARMER ----------------
@app.route('/add_farmer', methods=['GET', 'POST'])
def add_farmer():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        village = request.form['village']

        sql = "INSERT INTO farmers(name, phone, village) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, phone, village))
        db.commit()

        return redirect(url_for('view_farmers'))

    return render_template('add_farmer.html')


# ---------------- VIEW FARMERS ----------------
@app.route('/view_farmers')
def view_farmers():

    if session['role'] != 'admin':

        return "Access Denied"

    cursor.execute("SELECT * FROM farmers")

    farmers = cursor.fetchall()

    return render_template(
        'view_farmers.html',
        farmers=farmers
    )


# ---------------- SEARCH FARMER ----------------
@app.route('/search_farmer', methods=['GET', 'POST'])
def search_farmer():
    farmers = []

    if request.method == 'POST':
        keyword = request.form['keyword']

        sql = """
        SELECT * FROM farmers
        WHERE name LIKE %s OR village LIKE %s
        """
        cursor.execute(sql, ('%' + keyword + '%', '%' + keyword + '%'))
        farmers = cursor.fetchall()

    return render_template('search_farmer.html', farmers=farmers)


# ---------------- ADD CROP ----------------
@app.route("/add_crop", methods=["GET", "POST"])
def add_crop():

    if request.method == "POST":
        farmer_id = request.form["farmer_id"]
        crop_name = request.form["crop_name"]
        fertilizer = request.form["fertilizer"]
        season = request.form["season"]
        area = request.form["area"]
        yield_kg = request.form["yield_kg"]
        selling_price = request.form["selling_price"]
        cost_price = request.form["cost_price"]

        cursor.execute("""
            INSERT INTO farmer_crops
            (farmer_id, crop_name, fertilizer, season, area, yield_kg, selling_price, cost_price)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (farmer_id, crop_name, fertilizer, season, area, yield_kg, selling_price, cost_price))

        db.commit()

        return redirect(url_for("view_crops"))

    cursor.execute("SELECT farmer_id, name FROM farmers")
    farmers = cursor.fetchall()

    return render_template("add_crop.html", farmers=farmers)


# ---------------- VIEW CROPS ----------------
@app.route("/view_crops")
def view_crops():
    cursor.execute("""
        SELECT 
            farmer_crops.crop_id,
            farmers.name,
            farmer_crops.crop_name,
            farmer_crops.fertilizer,
            farmer_crops.season,
            farmer_crops.area,
            farmer_crops.yield_kg,
            farmer_crops.selling_price,
            farmer_crops.cost_price,
            (farmer_crops.yield_kg * farmer_crops.selling_price - farmer_crops.cost_price) AS profit
        FROM farmer_crops
        JOIN farmers ON farmer_crops.farmer_id = farmers.farmer_id
    """)

    crops = cursor.fetchall()
    return render_template("view_crops.html", crops=crops)

#----------------- DELETE CROP ----------------
@app.route("/delete_crop/<int:id>")
def delete_crop(id):

    cursor.execute("DELETE FROM farmer_crops WHERE crop_id=%s", (id,))
    db.commit()

    return redirect(url_for("view_crops"))


# ---------------- DELETE FARMER ----------------
@app.route('/delete_farmer/<int:id>')
def delete_farmer(id):
    cursor.execute("DELETE FROM farmers WHERE farmer_id = %s", (id,))
    db.commit()
    return redirect(url_for('view_farmers'))


# ---------------- UPDATE FARMER ----------------
@app.route('/update_farmer/<int:id>', methods=['GET', 'POST'])
def update_farmer(id):

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        village = request.form['village']

        cursor.execute("""
            UPDATE farmers
            SET name=%s, phone=%s, village=%s
            WHERE farmer_id=%s
        """, (name, phone, village, id))

        db.commit()
        return redirect(url_for('view_farmers'))

    cursor.execute("SELECT * FROM farmers WHERE farmer_id=%s", (id,))
    farmer = cursor.fetchone()

    return render_template('update_farmer.html', farmer=farmer)


# ---------------- ADD FERTILIZER ----------------
@app.route('/add_fertilizer', methods=['GET', 'POST'])
def add_fertilizer():

    if request.method == 'POST':
        fertilizer_name = request.form['fertilizer_name']
        company = request.form['company']
        quantity_available = request.form['quantity_available']
        price_per_bag = request.form['price_per_bag']

        cursor.execute("""
            INSERT INTO fertilizers
            (fertilizer_name, company, quantity_available, price_per_bag)
            VALUES(%s, %s, %s, %s)
        """, (fertilizer_name, company, quantity_available, price_per_bag))

        db.commit()
        return redirect(url_for('view_fertilizers'))

    return render_template('add_fertilizer.html')


# ---------------- VIEW FERTILIZERS ----------------
@app.route('/view_fertilizers')
def view_fertilizers():
    cursor.execute("SELECT * FROM fertilizers")
    fertilizers = cursor.fetchall()
    return render_template('view_fertilizers.html', fertilizers=fertilizers)


# ---------------- FERTILIZER USAGE ----------------
@app.route('/fertilizer_usage', methods=['GET', 'POST'])
def fertilizer_usage():

    if request.method == 'POST':
        farmer_id = request.form['farmer_id']
        fertilizer_id = request.form['fertilizer_id']
        crop_name = request.form['crop_name']
        quantity_used = request.form['quantity_used']
        usage_date = request.form['usage_date']

        cursor.execute("""
            INSERT INTO fertilizer_usage
            (farmer_id, fertilizer_id, crop_name, quantity_used, usage_date)
            VALUES(%s, %s, %s, %s, %s)
        """, (farmer_id, fertilizer_id, crop_name, quantity_used, usage_date))

        cursor.execute("""
            UPDATE fertilizers
            SET quantity_available = quantity_available - %s
            WHERE fertilizer_id = %s
        """, (quantity_used, fertilizer_id))

        db.commit()
        return redirect(url_for('dashboard'))

    return render_template('fertilizer_usage.html')


# ---------------- FARMER DETAILS (FIXED - ONLY ONE ROUTE) ----------------
@app.route("/farmer_details/<int:farmer_id>")
def farmer_details(farmer_id):

    # FARMER INFO

    cursor.execute("""
        SELECT farmer_id, name, phone, village
        FROM farmers
        WHERE farmer_id = %s
    """, (farmer_id,))

    farmer = cursor.fetchone()

    # CROP DETAILS

    cursor.execute("""
        SELECT
            crop_name,
            fertilizer,
            season,
            area,
            yield_kg,
            selling_price,
            cost_price,
            (yield_kg * selling_price) AS total_income,
            ((yield_kg * selling_price) - cost_price) AS profit

        FROM farmer_crops

        WHERE farmer_id = %s
    """, (farmer_id,))

    crops = cursor.fetchall()

    # FERTILIZER DETAILS

    cursor.execute("""
        SELECT
            f.fertilizer_name,
            fu.quantity_used,
            f.price_per_bag,
            (fu.quantity_used * f.price_per_bag) AS total_cost

        FROM fertilizer_usage fu

        JOIN fertilizers f
        ON fu.fertilizer_id = f.fertilizer_id

        WHERE fu.farmer_id = %s
    """, (farmer_id,))

    fertilizers = cursor.fetchall()

    return render_template(
        "farmer_details.html",
        farmer=farmer,
        crops=crops,
        fertilizers=fertilizers
    )
# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    if session['role'] != 'admin':

        return "Access Denied"

    # Total Farmers
    cursor.execute("SELECT COUNT(*) FROM farmers")
    total_farmers = cursor.fetchone()[0]

    # Total Fertilizers
    cursor.execute("SELECT COUNT(*) FROM fertilizers")
    total_fertilizers = cursor.fetchone()[0]

    # Total Stock
    cursor.execute("SELECT SUM(quantity_available) FROM fertilizers")
    total_stock = cursor.fetchone()[0]

    # Total Usage
    cursor.execute("SELECT SUM(quantity_used) FROM fertilizer_usage")
    total_usage = cursor.fetchone()[0]

    # PROFIT / LOSS DATA
    cursor.execute("""
        SELECT crop_name,
        (yield_kg * selling_price - cost_price) AS profit
        FROM farmer_crops
    """)

    profit_data = cursor.fetchall()

    crop_names = []
    profits = []

    for row in profit_data:
        crop_names.append(row[0])
        profits.append(float(row[1]))

    return render_template(
        'dashboard.html',
        total_farmers=total_farmers,
        total_fertilizers=total_fertilizers,
        total_stock=total_stock,
        total_usage=total_usage,
        crop_names=crop_names,
        profits=profits
    )
# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)