from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from werkzeug.utils import secure_filename
import base64
import cv2
import numpy as np
import math
from scipy.spatial.distance import euclidean
from imutils import perspective
from imutils import contours
import imutils
import sys
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import logging
from fpdf import FPDF
from flask_mail import Mail, Message

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jklo55345@gmail.com'  
app.config['MAIL_PASSWORD'] = 'rkcx nzbe covq nyzn'  
app.config['MAIL_DEFAULT_SENDER'] = 'jklo55345@gmail.com'

mail = Mail(app)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0000@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 設置日誌
logging.basicConfig(level=logging.DEBUG)

# 定義資料模型
class MovingProposal(db.Model):
    __tablename__ = 'moving_services'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(255), nullable=False)
    contact_info = db.Column(db.String(255), nullable=False)
    move_date = db.Column(db.Date, nullable=False)
    plan_type = db.Column(db.String(255), nullable=False)
    from_address = db.Column(db.Text, nullable=False)
    to_address = db.Column(db.Text, nullable=False)
    move_type = db.Column(db.String(255), nullable=False)
    people_count = db.Column(db.Integer, nullable=False)
    estimated_cost = db.Column(db.Float, nullable=False)

# 處理表單提交
@app.route('/submit_proposal', methods=['POST'])
def submit_proposal():
    try:
        # 獲取表單資料
        customer_name = request.form['customerName']
        contact_info = request.form['contactInfo']
        move_date = datetime.strptime(request.form['moveDate'], '%Y-%m-%d')
        plan_type = request.form['planType']
        from_address = request.form['fromAddress']
        to_address = request.form['toAddress']
        move_type = request.form['moveType']
        people_count = int(request.form['peopleCount'])
        estimated_cost = float(request.form['estimatedCost'])

        # 創建並保存提案數據
        new_proposal = MovingProposal(
            customer_name=customer_name,
            contact_info=contact_info,
            move_date=move_date,
            plan_type=plan_type,
            from_address=from_address,
            to_address=to_address,
            move_type=move_type,
            people_count=people_count,
            estimated_cost=estimated_cost
        )

        db.session.add(new_proposal)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Proposal submitted successfully!'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting proposal: {e}")
        return jsonify({'success': False, 'message': 'Internal Server Error'}), 500


# AI演算法函式
def boxconfig():
    return {
        'small': {'width': 47, 'height': 33},
        'medium': {'width': 48, 'height': 45},
        'large': {'width': 69, 'height': 47}
    }

def process_image(image_data, dist_in_cm=30.0, dist_in_pixel=100.0):
    # 读取和处理图像
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    edged = cv2.Canny(blur, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    # 计算每厘米的像素数
    pixel_per_cm = dist_in_pixel / dist_in_cm

    # 找寻并排序轮廓
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    (cnts, _) = contours.sort_contours(cnts)

    cv2.putText(image, "Ref size: {:.2f}cm".format(dist_in_cm), (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    items = []

    # 绘制其余轮廓并计算尺寸
    for cnt in cnts:
        box = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(box)
        box = np.array(box, dtype="int")
        box = perspective.order_points(box)
        area = cv2.contourArea(box)
        if area > dist_in_cm ** 2:
            (tl, tr, br, bl) = box
            cv2.drawContours(image, [box.astype("int")], -1, (0, 0, 255), 2)
            mid_pt_horizontal = (tl[0] + int(abs(tr[0] - tl[0]) / 2), tl[1] + int(abs(tr[1] - tl[1]) / 2))
            mid_pt_verticle = (tr[0] + int(abs(tr[0] - br[0]) / 2), tr[1] + int(abs(tr[1] - br[1]) / 2))
            wid = euclidean(tl, tr) / pixel_per_cm
            ht = euclidean(tr, br) / pixel_per_cm
            # 這邊預設物品深度是 15 公分。
            items.append(wid * ht * 15)
            cv2.putText(image, "{:.1f}cm".format(wid), (int(mid_pt_horizontal[0] - 15), int(mid_pt_horizontal[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            cv2.putText(image, "{:.1f}cm".format(ht), (int(mid_pt_verticle[0] + 10), int(mid_pt_verticle[1])),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # 将处理后的图像转换为base64编码
    _, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    print("Encoded image size:", len(encoded_image))

    return encoded_image, items

def fit_boxes(items):
    large = 69 * 47 * 47  
    medium = 48 * 45 * 42  
    small = 47 * 33 * 30  

    r_small = 0
    r_medium = 0
    r_large = 0
	
    for tmp in items:
        print(tmp)
        while tmp >= large:
            tmp -= large
            r_large += 1

        print(tmp)
        while large > tmp >= medium:
            tmp -= medium
            r_medium += 1

        print(tmp)
        while medium > tmp >= small:
            tmp -= small
            r_small += 1

    if tmp > 0:
        r_small += 1

    print(r_small, r_medium, r_large)

    return r_small, r_medium, r_large

def calculate_car_count(small, medium, large):
    small_volume = small * 47 * 33 * 30
    medium_volume = medium * 48 * 45 * 42
    large_volume = large * 69 * 47 * 47

    total_volume = small_volume + medium_volume + large_volume
    car_count = total_volume / 1000000  # Convert cubic cm to cubic meters
    car_count = math.ceil(car_count * 2) / 2  # Round up to the nearest 0.5

    return car_count

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)

    def __init__(self, email, password, name, gender, birthday, phone, address):
        self.email = email
        self.password = password
        self.name = name
        self.gender = gender
        self.birthday = birthday
        self.phone = phone
        self.address = address

login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('total.html')

@app.route('/load_section', methods=['POST'])
def load_section():
    section = request.form.get('section')
    if section == 'home':
        return render_template('home.html')
    elif section == 'services':
        return render_template('services.html')
    elif section == 'declutter':
        return render_template('declutter.html')
    elif section == 'large_furniture':
        return render_template('large-furniture.html')
    elif section == 'services_steps':
        return render_template('services_steps.html')
    return '', 404

@app.route('/load_about_section', methods=['POST'])
def load_about_section():
    section = request.form.get('section')
    try:
        with open('static/aboutus.html', 'r', encoding='utf-8') as file:
            content = file.read()
        start = content.find(f'id="{section}"')
        end = content.find('</div>', start) + 6
        section_content = content[start:end]
        return section_content
    except Exception as e:
        app.logger.error(f"Error loading about section: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            
            if user and user.password == password:
                login_user(user)
                return jsonify({'success': True, 'redirect': url_for('valuation')}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials, please try again.'}), 401
        except Exception as e:
            app.logger.error(f"Error in login: {e}")
            return jsonify({'success': False, 'message': 'Internal Server Error'}), 500
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    try:
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        gender = request.form['gender']
        birthday = request.form['birthday']
        phone = request.form['phone']
        address = request.form['address']

        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400

        new_user = User(
            email=email,
            password=password,
            name=name,
            gender=gender,
            birthday=datetime.strptime(birthday, '%Y-%m-%d'),
            phone=phone,
            address=address
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in register: {e}")
        return jsonify({'success': False, 'message': 'Internal Server Error'}), 500

@app.route('/main')
@login_required
def main():
    return "Welcome to the main page!"

@app.route('/valuation')
@login_required
def valuation():
    return render_template('Valuation.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data_url = request.json.get('image')
        scale = request.json.get('scale', 'normal')

        # 呼叫主機B上的 /process API
        api_url = 'https://140.116.179.17:8092/api'
        response = requests.post(api_url, verify=False, json={
            'image': data_url,
            'scale': scale
        })

        # 確認 API 返回成功
        if response.status_code == 200:
            data = response.json()
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Failed to process image'}), 500

    except Exception as e:
        app.logger.error(f"Error calling process API: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/proposal')
@login_required
def proposal():
    return render_template('Proposal.html')

@app.route('/send_pdf_email', methods=['POST'])
def send_pdf_email():
    try:
        data = request.get_json()
        recipient_email = data.get('email')
        pdf_data = data.get('pdf')
        
        if not recipient_email or not pdf_data:
            return jsonify({'message': 'Email and PDF data are required'}), 400
        
        pdf_file = base64.b64decode(pdf_data.split(',')[1])

        msg = Message(
            subject="搬家建議書報告",
            recipients=[recipient_email]
        )
        msg.body = "請查收附加的搬家建議書報告。"
        msg.attach("搬家建議書.pdf", "application/pdf", pdf_file)

        mail.send(msg)

        return jsonify({'message': 'Email sent successfully!'}), 200

    except Exception as e:
        app.logger.error(f"Error sending email: {e}")
        return jsonify({'message': 'Failed to send email', 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    context = ('cert.pem', 'key.pem')    
    app.run(debug=True, host='0.0.0.0', port=8092, ssl_context=context)
