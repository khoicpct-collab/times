from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import pandas as pd
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('data/rm_tracking.db')
    c = conn.cursor()
    
    # Bảng dữ liệu tháng
    c.execute('''CREATE TABLE IF NOT EXISTS monthly_data
                 (id INTEGER PRIMARY KEY,
                  month INTEGER,
                  year INTEGER,
                  data_json TEXT,
                  created_at TIMESTAMP)''')
    
    # Bảng nguyên nhân
    c.execute('''CREATE TABLE IF NOT EXISTS causes
                 (id INTEGER PRIMARY KEY,
                  code TEXT UNIQUE,
                  name TEXT,
                  category TEXT,
                  active BOOLEAN DEFAULT 1,
                  sort_order INTEGER)''')
    
    conn.commit()
    conn.close()

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    """Import dữ liệu từ Excel"""
    file = request.files['file']
    month = request.form.get('month')
    year = request.form.get('year')
    
    # Đọc file Excel
    df = pd.read_excel(file, sheet_name=None)
    
    # Xử lý dữ liệu
    processed_data = process_excel_data(df, month, year)
    
    # Lưu vào database
    save_monthly_data(month, year, processed_data)
    
    return jsonify({"success": True, "data": processed_data})

@app.route('/api/get-monthly-data/<int:year>/<int:month>')
def get_monthly_data(year, month):
    """Lấy dữ liệu theo tháng"""
    conn = sqlite3.connect('data/rm_tracking.db')
    c = conn.cursor()
    
    c.execute("SELECT data_json FROM monthly_data WHERE year=? AND month=?", 
              (year, month))
    result = c.fetchone()
    
    conn.close()
    
    if result:
        return jsonify(json.loads(result[0]))
    return jsonify({"error": "No data found"})

@app.route('/api/export-pdf/<int:year>')
def export_pdf(year):
    """Xuất báo cáo năm ra PDF"""
    # Tổng hợp dữ liệu cả năm
    annual_data = get_annual_summary(year)
    
    # Tạo PDF
    pdf_path = generate_pdf_report(annual_data, year)
    
    return send_file(pdf_path, as_attachment=True)

@app.route('/api/causes', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_causes():
    """Quản lý nguyên nhân"""
    if request.method == 'GET':
        # Lấy danh sách nguyên nhân
        conn = sqlite3.connect('data/rm_tracking.db')
        c = conn.cursor()
        c.execute("SELECT * FROM causes WHERE active=1 ORDER BY sort_order")
        causes = [dict(zip([column[0] for column in c.description], row)) 
                 for row in c.fetchall()]
        conn.close()
        return jsonify(causes)
    
    elif request.method == 'POST':
        # Thêm nguyên nhân mới
        data = request.json
        # ... xử lý thêm
        return jsonify({"success": True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
