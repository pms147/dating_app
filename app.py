from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length
from pymongo import MongoClient
from email_validator import validate_email, EmailNotValidError

# Flask App Config
app = Flask(__name__)
app.secret_key = "sang1407"

# MongoDB Connection
try:
    client = MongoClient("mongodb://localhost:27017/")  # MongoDB Server
    client.admin.command("ping")  # Kiểm tra kết nối
    print("MongoDB connection successful!")
except Exception as e:
    print("Failed to connect to MongoDB:", e)
    exit(1)  # Thoát chương trình nếu không kết nối được

db = client.dating_app  # Database
users_collection = db.users  # Collection


# Form đăng ký người dùng
class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=1)])
    gender = SelectField("Gender", choices=[("male", "Male"), ("female", "Female")])
    preference = SelectField(
        "Looking For", choices=[("male", "Male"), ("female", "Female")]
    )
    submit = SubmitField("Sign Up")


@app.route("/", methods=["GET", "POST"])
def index():
    # Handle user login
    if request.method == "POST":
        email = request.form.get("email")  # Fetch the email from form
        password = request.form.get("password")  # Fetch the password from form
        print(email, password)

        # Query the user from MongoDB
        user = users_collection.find_one({"email": email})

        if user:
            # Validate password (if hashed, use bcrypt or similar to verify)
            if user.get("password") == password:  # Replace with hash comparison
                session["email"] = email
                return redirect(url_for("matches"))
            else:
                return "Invalid email or password", 400
        else:
            return "Invalid email or password", 400

    # Render the login form for GET requests
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        # Kiểm tra tính hợp lệ của email
        try:
            valid_email = validate_email(form.email.data)
            email = valid_email.email  # Dùng email đã được chuẩn hóa
        except EmailNotValidError as e:
            return f"Invalid email: {e}", 400  # Trả lỗi nếu email không hợp lệ

        # Kiểm tra email đã tồn tại hay chưa
        if users_collection.find_one({"email": email}):
            return "Email already exists", 400  # Trả lỗi nếu email đã tồn tại

        # Lưu thông tin người dùng vào MongoDB
        users_collection.insert_one(
            {
                "name": form.name.data,
                "email": email,
                "password": form.password.data,  # Mã hóa mật khẩu trong thực tế
                "gender": form.gender.data,
                "preference": form.preference.data,
                # "profile_picture": form.profile_picture.data
            }
        )
        return redirect(url_for("index"))
    return render_template("signup.html", form=form)


@app.route("/matches")
def matches():
    # Lấy người dùng hiện tại (đã đăng nhập)
    current_user = users_collection.find_one({"email": session.get("email")})

    # Tìm kiếm người dùng phù hợp
    matches = users_collection.find(
        {"gender": current_user["preference"], "preference": current_user["gender"]}
    )

    # Loai bỏ người dùng hiện tại khỏi danh sách kết quả
    matches = [match for match in matches if match["email"] != current_user["email"]]

    return render_template("matches.html", matches=matches)


if __name__ == "__main__":
    app.run(debug=True)
