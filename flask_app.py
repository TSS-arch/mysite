from flask import Flask, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os, uuid, json, base64
from flask import url_for
import re

app = Flask(__name__)

# --------------------
# CONFIG
# --------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///certificates.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf"}

db = SQLAlchemy(app)
UPLOAD_FOLDER = "/home/bfgtc/mysite/static/qr"
UPLOAD_FOLDER2 = "/home/bfgtc/mysite/static/fs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER2, exist_ok=True)  # Ensure the upload directory exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2

@app.route("/uploader", methods=["POST"])
def save_uploader():
    if request.method == "POST":
        f = request.files['send_file']
        if f:
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'File saved successfully!'
        else:
            return 'No file uploaded!', 400

# --------------------
# MODEL - UPDATED with image fields
# --------------------
class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certificate_no = db.Column(db.String(50), unique=True, nullable=False)
    date_time = db.Column(db.String(120))
    customer_name = db.Column(db.String(120))
    article = db.Column(db.String(120))
    weight = db.Column(db.Float)
    purity = db.Column(db.String(50))
    gold_percentage = db.Column(db.Float)
    pdf_filename = db.Column(db.String(200))
    ggg = db.Column(db.String(200),nullable=True)
    joint = db.Column(db.String(200),nullable=True)
    elements = db.Column(db.Text)      # stored as JSON
    # New fields for base64 images
    image1_base64 = db.Column(db.Text)  # Base64 encoded image 1
    image2_base64 = db.Column(db.Text)  # Base64 encoded image 2
    image3_base64 = db.Column(db.Text)  # Base64 encoded image 3
    # Optional: store image types (jpeg, png, etc.)
    image1_type = db.Column(db.String(20))
    image2_type = db.Column(db.String(20))
    image3_type = db.Column(db.String(20))

    def to_dict(self):
        return {
            "certificate_no": self.certificate_no,
            "date_time": self.date_time,
            "customer_name": self.customer_name,
            "article": self.article,
            "weight": self.weight,
            "purity": self.purity,
            "gold_percentage": self.gold_percentage,
            "pdf_filename": self.pdf_filename,
            "elements": json.loads(self.elements or "[]"),
            "ggg":self.ggg,
            "joint":self.joint,
            # Include image data in dictionary
            "image1_base64": self.image1_base64,
            "image2_base64": self.image2_base64,
            "image3_base64": self.image3_base64,
            "image1_type": self.image1_type,
            "image2_type": self.image2_type,
            "image3_type": self.image3_type
        }


with app.app_context():
    db.create_all()


# --------------------
# HELPERS
# --------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_base64_image(data):
    """Check if the string is a valid base64 image"""
    if not data or not isinstance(data, str):
        return False
    # Check if it looks like a data URL or base64
    if data.startswith('data:image'):
        return True
    try:
        # Try to decode it
        base64.b64decode(data, validate=True)
        return True
    except:
        return False

def extract_image_type_from_base64(base64_str):
    """Extract image type from base64 data URL"""
    if not base64_str:
        return None
    if base64_str.startswith('data:image/'):
        # Extract from data URL: data:image/jpeg;base64,...
        match = re.match(r'data:image/([^;]+)', base64_str)
        if match:
            return match.group(1)
    return 'jpeg'  # Default

# --------------------
# 1️⃣ POST — CREATE CERTIFICATE (UPDATED)
# --------------------
@app.route("/api/certificates", methods=["POST"])
def create_certificate():

    def safe_str(value, default="None"):
        if value is None:
            return default
        value = str(value).strip()
        return value if value != "" else default

    def safe_float(value, default=0):
        try:
            if value is None or value == "":
                return default
            return float(value)
        except:
            return default

    certificate_no = safe_str(request.form.get("certificate_no"), "")

    if certificate_no == "":
        return jsonify({"success": False, "message": "certificate_no required"}), 400

    # --- duplicate check ---
    existing = Certificate.query.filter_by(certificate_no=certificate_no).first()
    if existing:
        return jsonify({"success": False, "message": "Certificate already exists"}), 400

    # --- PDF upload ---

    pdf_filename = ""


    # --- elements ---
    elements_str = request.form.get("elements", "[]")
    try:
        elements = json.loads(elements_str)
    except:
        elements = []

    date_time_str = safe_str(request.form.get("date_time"), "")

    # --- Process base64 images ---
    image1_base64 = request.form.get("image1_base64", "")
    image2_base64 = request.form.get("image2_base64", "")
    image3_base64 = request.form.get("image3_base64", "")

    # Validate and store images
    image1_type = ""
    image2_type = ""
    image3_type = ""
    # Only store if valid


    cert = Certificate(
        certificate_no=certificate_no,
        date_time=date_time_str,
        customer_name=safe_str(request.form.get("customer_name")),
        article=safe_str(request.form.get("article")),
        weight=safe_float(request.form.get("weight"), 0),
        purity=safe_str(request.form.get("purity")),
        gold_percentage=safe_float(request.form.get("gold_percentage"), 0),
        ggg = request.form.get("ggg"),
        joint = request.form.get("joint"),
        pdf_filename=pdf_filename,
        elements=json.dumps(elements),
        # Store images
        image1_base64=image1_base64,
        image2_base64=image2_base64,
        image3_base64=image3_base64,
        image1_type=image1_type,
        image2_type=image2_type,
        image3_type=image3_type
    )

    db.session.add(cert)
    db.session.commit()

    return jsonify({"success": True, "certificate": cert.to_dict()}), 201

# --------------------
# 2️⃣ GET — SHOW TEMPLATE (UPDATED)
# --------------------
@app.route("/certificate/<cert_no>")
def show_certificate(cert_no):
    cert = Certificate.query.filter_by(certificate_no=cert_no).first_or_404()

    # Convert the certificate to a dictionary
    data = cert.to_dict()

    # If the elements field is a string (JSON), parse it
    if isinstance(data.get('elements'), str):
        try:
            data['elements'] = json.loads(data['elements'])
        except:
            data['elements'] = []

    # If elements is None or empty, provide default structure
    if not data.get('elements'):
        # Default structure matching your example
        data['elements'] = [
            ["0.000", "0.000", "0.000", "0.000", "0.000", "0.000"],
            ["0.000", "0.000", "0.000", "0.000", "0.000", "0.000"],
            ["0.000", "0.000", "0.000", "0.000", "0.000", "0.000"],
            ["0.000", "0.000", "0.000", "0.00", "0.00", "0.000"]
        ]

    # Add PDF URL if PDF exists

    # Add logo URL
    logo_url = url_for('static', filename='header.png')
    banner_url = url_for('static', filename='footer.png')

    # Prepare image URLs for template
    # For base64 images, we'll use the data directly in the template
    # You can also create data URLs for easier use in HTML
    def create_image_data_url(base64_data, image_type='jpeg'):
        if not base64_data:
            return None
        if base64_data.startswith('data:image'):
            return base64_data  # Already a data URL
        else:
            return f"data:image/{image_type};base64,{base64_data}"

    image1_url = create_image_data_url(cert.image1_base64,) if cert.image1_base64 != ""  else None
    image2_url = create_image_data_url(cert.image2_base64,) if cert.image2_base64 != ""  else None
    image3_url = create_image_data_url(cert.image3_base64,) if cert.image3_base64 != ""  else None

    return render_template(
        "pdf_viewer.html",
        cert=data,

        logo_url=logo_url,
        banner_url=banner_url,
        # Pass image URLs to template
        image1_url=image1_url,
        image2_url=image2_url,
        image3_url=image3_url,
        # Also pass raw base64 if needed
        image1_base64=cert.image1_base64,
        image2_base64=cert.image2_base64,
        image3_base64=cert.image3_base64,
        # And image types
        image1_type='jpeg',
        image2_type='jpeg',
        image3_type='jpeg'
    )

# --------------------
# 3️⃣ API to update images for existing certificate
# --------------------
@app.route("/api/certificates/<cert_no>/images", methods=["POST"])
def update_certificate_images(cert_no):
    """Update images for an existing certificate"""
    cert = Certificate.query.filter_by(certificate_no=cert_no).first()
    if not cert:
        return jsonify({"success": False, "message": "Certificate not found"}), 404

    # Process base64 images from form data
    image1_base64 = request.form.get("image1_base64")
    image2_base64 = request.form.get("image2_base64")
    image3_base64 = request.form.get("image3_base64")

    # Update only if provided and valid
    if image1_base64 is not None:
        if is_valid_base64_image(image1_base64):
            cert.image1_base64 = image1_base64
            cert.image1_type = extract_image_type_from_base64(image1_base64)
        else:
            cert.image1_base64 = None
            cert.image1_type = None

    if image2_base64 is not None:
        if is_valid_base64_image(image2_base64):
            cert.image2_base64 = image2_base64
            cert.image2_type = extract_image_type_from_base64(image2_base64)
        else:
            cert.image2_base64 = None
            cert.image2_type = None

    if image3_base64 is not None:
        if is_valid_base64_image(image3_base64):
            cert.image3_base64 = image3_base64
            cert.image3_type = extract_image_type_from_base64(image3_base64)
        else:
            cert.image3_base64 = None
            cert.image3_type = None

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Images updated successfully",
        "has_image1": cert.image1_base64 is not None,
        "has_image2": cert.image2_base64 is not None,
        "has_image3": cert.image3_base64 is not None
    })

# --------------------
# 4️⃣ API to get certificate data including images
# --------------------
@app.route("/api/certificates/<cert_no>", methods=["GET"])
def get_certificate_data(cert_no):
    """Get certificate data including images"""
    cert = Certificate.query.filter_by(certificate_no=cert_no).first()
    if not cert:
        return jsonify({"success": False, "message": "Certificate not found"}), 404

    data = cert.to_dict()
    return jsonify({"success": True, "certificate": data})

# --------------------
# RUN
# --------------------
if __name__ == "__main__":
    app.run(debug=True)