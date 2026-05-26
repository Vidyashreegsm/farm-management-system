from flask import Flask, render_template, request, redirect, session, url_for, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "farmproject123"

# ---------------- MYSQL CONNECTION ----------------

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vidya@123",
        database="farm_management"
    )


# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        username = request.form['username']
        password = request.form['password']

        cursor.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            session['farmer_id'] = user[4]

            return redirect(url_for('home'))

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

    if 'user_id' not in session:

        return redirect(url_for('login'))

    return render_template(
        'index.html',
        role=session['role']
    )


# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    conn = get_db_connection()
    cursor = conn.cursor()

    # TOTAL FARMERS
    cursor.execute("SELECT COUNT(*) FROM farmers")
    total_farmers = cursor.fetchone()[0]

    # TOTAL FERTILIZERS
    cursor.execute("SELECT COUNT(*) FROM fertilizers")
    total_fertilizers = cursor.fetchone()[0]

    # TOTAL STOCK
    cursor.execute("SELECT IFNULL(SUM(quantity_available),0) FROM fertilizers")
    total_stock = cursor.fetchone()[0]

    # TOTAL USAGE
    cursor.execute("SELECT IFNULL(SUM(quantity_used),0) FROM fertilizer_usage")
    total_usage = cursor.fetchone()[0]

    # PROFIT CHART DATA
    cursor.execute("""
        SELECT crop_name,
        (yield_kg * selling_price - cost_price) AS profit
        FROM farmer_crops
    """)

    data = cursor.fetchall()

    crop_names = []
    profits = []

    for row in data:

        crop_names.append(row[0])
        profits.append(float(row[1]))

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total_farmers=total_farmers,
        total_fertilizers=total_fertilizers,
        total_stock=total_stock,
        total_usage=total_usage,
        crop_names=crop_names,
        profits=profits
    )

# ---------------- ADD FARMER ----------------

@app.route('/add_farmer', methods=['GET', 'POST'])
def add_farmer():

    if session['role'] != 'admin':

        return "Access Denied"

    if request.method == 'POST':

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        name = request.form['name']
        phone = request.form['phone']
        village = request.form['village']

        cursor.execute("""
            INSERT INTO farmers(name, phone, village)
            VALUES(%s,%s,%s)
        """, (name, phone, village))

        conn.commit()

        # CREATE FARMER LOGIN
        farmer_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users(username, password, role, farmer_id)
            VALUES(%s,%s,%s,%s)
        """, (
            name.lower(),
            "1234",
            "farmer",
            farmer_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('view_farmers'))

    return render_template('add_farmer.html')


# ---------------- VIEW FARMERS ----------------

@app.route('/view_farmers')
def view_farmers():

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    cursor.execute("""
        SELECT * FROM farmers
    """)

    farmers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'view_farmers.html',
        farmers=farmers
    )


# ---------------- SEARCH FARMER ----------------

@app.route('/search_farmer', methods=['GET', 'POST'])
def search_farmer():

    farmers = []

    if request.method == 'POST':

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        keyword = request.form['keyword']

        cursor.execute("""
            SELECT * FROM farmers
            WHERE name LIKE %s
            OR village LIKE %s
        """, (
            '%' + keyword + '%',
            '%' + keyword + '%'
        ))

        farmers = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template(
        'search_farmer.html',
        farmers=farmers
    )


# ---------------- ADD CROP ----------------

@app.route('/add_crop', methods=['GET', 'POST'])
def add_crop():

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':

        if session['role'] == 'farmer':

            farmer_id = session['farmer_id']

        else:

            farmer_id = request.form['farmer_id']

        crop_name = request.form['crop_name']
        fertilizer = request.form['fertilizer']
        season = request.form['season']
        area = request.form['area']
        yield_kg = request.form['yield_kg']
        selling_price = request.form['selling_price']
        cost_price = request.form['cost_price']

        cursor.execute("""
            INSERT INTO farmer_crops
            (
                farmer_id,
                crop_name,
                fertilizer,
                season,
                area,
                yield_kg,
                selling_price,
                cost_price
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            farmer_id,
            crop_name,
            fertilizer,
            season,
            area,
            yield_kg,
            selling_price,
            cost_price
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('view_crops'))

    cursor.execute("""
        SELECT farmer_id, name
        FROM farmers
    """)

    farmers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'add_crop.html',
        farmers=farmers
    )


# ---------------- VIEW CROPS ----------------

@app.route('/view_crops')
def view_crops():

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if session['role'] == 'farmer':

        cursor.execute("""
            SELECT
                crop_id,
                farmer_id,
                crop_name,
                fertilizer,
                season,
                area,
                yield_kg,
                selling_price,
                cost_price,
                ((yield_kg * selling_price) - cost_price) AS profit

            FROM farmer_crops

            WHERE farmer_id=%s
        """, (session['farmer_id'],))

    else:

        cursor.execute("""
            SELECT
                crop_id,
                farmer_id,
                crop_name,
                fertilizer,
                season,
                area,
                yield_kg,
                selling_price,
                cost_price,
                ((yield_kg * selling_price) - cost_price) AS profit

            FROM farmer_crops
        """)

    crops = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'view_crops.html',
        crops=crops
    )


# ---------------- DELETE FARMER ----------------

@app.route('/delete_farmer/<int:id>')
def delete_farmer(id):

    if session['role'] != 'admin':

        return "Access Denied"

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    try:

        cursor.execute("""
            DELETE FROM fertilizer_usage
            WHERE farmer_id=%s
        """, (id,))

        cursor.execute("""
            DELETE FROM farmer_crops
            WHERE farmer_id=%s
        """, (id,))

        cursor.execute("""
            DELETE FROM users
            WHERE farmer_id=%s
        """, (id,))

        cursor.execute("""
            DELETE FROM farmers
            WHERE farmer_id=%s
        """, (id,))

        conn.commit()

    except Exception as e:

        conn.rollback()
        print(e)

    cursor.close()
    conn.close()

    return redirect(url_for('view_farmers'))

# ---------------- DELETE CROP ----------------

@app.route('/delete_crop/<int:id>')
def delete_crop(id):

    if session['role'] != 'admin':
        return "Access Denied"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM farmer_crops
            WHERE crop_id = %s
        """, (id,))

        conn.commit()

    except Exception as e:

        conn.rollback()
        print(e)

    finally:

        cursor.close()
        conn.close()

    return redirect(url_for('view_crops'))


# ---------------- UPDATE FARMER ----------------

@app.route('/update_farmer/<int:id>', methods=['GET', 'POST'])
def update_farmer(id):

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    if request.method == 'POST':

        cursor.execute("""
            UPDATE farmers
            SET name=%s,
                phone=%s,
                village=%s
            WHERE farmer_id=%s
        """, (
            request.form['name'],
            request.form['phone'],
            request.form['village'],
            id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('view_farmers'))

    cursor.execute("""
        SELECT * FROM farmers
        WHERE farmer_id=%s
    """, (id,))

    farmer = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'update_farmer.html',
        farmer=farmer
    )


# ---------------- ADD FERTILIZER ----------------

@app.route('/add_fertilizer', methods=['GET', 'POST'])
def add_fertilizer():

    if request.method == 'POST':

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        cursor.execute("""
            INSERT INTO fertilizers
            (
                fertilizer_name,
                company,
                quantity_available,
                price_per_bag
            )
            VALUES(%s,%s,%s,%s)
        """, (
            request.form['fertilizer_name'],
            request.form['company'],
            request.form['quantity_available'],
            request.form['price_per_bag']
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('view_fertilizers'))

    return render_template('add_fertilizer.html')


# ---------------- VIEW FERTILIZERS ----------------

@app.route('/view_fertilizers')
def view_fertilizers():

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    cursor.execute("""
        SELECT * FROM fertilizers
    """)

    fertilizers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'view_fertilizers.html',
        fertilizers=fertilizers
    )


# ---------------- FARMER DETAILS ----------------

@app.route('/farmer_details/<int:farmer_id>')
def farmer_details(farmer_id):

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    # FARMER INFO

    cursor.execute("""
        SELECT
            farmer_id,
            name,
            phone,
            village

        FROM farmers

        WHERE farmer_id=%s
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

        WHERE farmer_id=%s
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

        WHERE fu.farmer_id=%s
    """, (farmer_id,))

    fertilizers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'farmer_details.html',
        farmer=farmer,
        crops=crops,
        fertilizers=fertilizers
    )


# ---------------- DOWNLOAD PDF REPORT ----------------

@app.route("/download_report/<int:farmer_id>")
def download_report(farmer_id):

    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    cursor.execute("""
        SELECT farmer_id, name, phone, village
        FROM farmers
        WHERE farmer_id=%s
    """, (farmer_id,))

    farmer = cursor.fetchone()

    cursor.execute("""
        SELECT
            crop_name,
            season,
            area,
            yield_kg,
            selling_price,
            cost_price,
            ((yield_kg * selling_price) - cost_price) AS profit

        FROM farmer_crops

        WHERE farmer_id=%s
    """, (farmer_id,))

    crops = cursor.fetchall()

    filename = f"Farmer_Report_{farmer_id}.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "<b>Farmer Report</b>",
        styles['Title']
    )

    elements.append(title)
    elements.append(Spacer(1, 20))

    farmer_info = f"""
    <b>Farmer ID:</b> {farmer[0]}<br/>
    <b>Name:</b> {farmer[1]}<br/>
    <b>Phone:</b> {farmer[2]}<br/>
    <b>Village:</b> {farmer[3]}<br/>
    """

    elements.append(
        Paragraph(
            farmer_info,
            styles['BodyText']
        )
    )

    elements.append(Spacer(1, 20))

    data = [[
        'Crop',
        'Season',
        'Area',
        'Yield',
        'Selling Price',
        'Cost Price',
        'Profit'
    ]]

    for crop in crops:

        data.append([
            crop[0],
            crop[1],
            crop[2],
            crop[3],
            crop[4],
            crop[5],
            crop[6]
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.green),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),

    ]))

    elements.append(table)

    doc.build(elements)

    cursor.close()
    conn.close()

    return send_file(
        filename,
        as_attachment=True
    )
# ---------------- FERTILIZER USAGE ----------------

@app.route('/fertilizer_usage', methods=['GET', 'POST'])
def fertilizer_usage():

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':

        try:

            # FARMER LOGIN
            if session['role'] == 'farmer':
                farmer_id = session['farmer_id']

            # ADMIN LOGIN
            else:
                farmer_id = request.form['farmer_id']

            fertilizer_id = request.form['fertilizer_id']
            crop_name = request.form['crop_name']
            quantity_used = request.form['quantity_used']
            usage_date = request.form['usage_date']

            # INSERT USAGE
            cursor.execute("""
                INSERT INTO fertilizer_usage
                (farmer_id, fertilizer_id, crop_name, quantity_used, usage_date)
                VALUES(%s, %s, %s, %s, %s)
            """, (
                farmer_id,
                fertilizer_id,
                crop_name,
                quantity_used,
                usage_date
            ))

            # UPDATE STOCK
            cursor.execute("""
                UPDATE fertilizers
                SET quantity_available = quantity_available - %s
                WHERE fertilizer_id = %s
            """, (
                quantity_used,
                fertilizer_id
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(e)

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('dashboard'))

    # GET REQUEST

    cursor.execute("SELECT farmer_id, name FROM farmers")
    farmers = cursor.fetchall()

    cursor.execute("""
        SELECT fertilizer_id, fertilizer_name
        FROM fertilizers
    """)
    fertilizers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'fertilizer_usage.html',
        farmers=farmers,
        fertilizers=fertilizers
    )


# ---------------- RUN ----------------

if __name__ == '__main__':

    app.run(debug=True)