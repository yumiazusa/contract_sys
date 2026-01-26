from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# 数据库配置
# 临时切换到本地SQLite数据库以解决远程连接权限问题
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contract.db'
# 原MySQL配置（如需恢复远程连接，请取消注释下方代码并注释掉上方SQLite配置）
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ProjectDB:4100282Ly@47.108.254.13/projectdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 数据库模型
class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    contract_no = db.Column(db.String(50), unique=True, nullable=False)
    contract_name = db.Column(db.String(200), nullable=False)
    project_no = db.Column(db.String(500))
    contract_type = db.Column(db.String(20), nullable=False)
    platform = db.Column(db.String(10), nullable=False)
    contract_amount = db.Column(db.Numeric(15, 2))
    sign_date = db.Column(db.Date)
    company_name = db.Column(db.String(200), nullable=False)
    contact_phone = db.Column(db.String(50), nullable=False)
    manager = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    payment_terms = db.Column(db.Text)
    original_contract_no = db.Column(db.String(50))
    original_contract_name = db.Column(db.String(200))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# 生成合同编号
def generate_contract_no(contract_type, platform):
    prefix = 'KJ' if contract_type == '框架合同' else 'HT'
    platform_code = 'JQ' if platform == '金乾' else 'JC'

    # 查询当前平台和类型的最大流水号
    last_contract = Contract.query.filter(
        Contract.contract_type == contract_type,
        Contract.platform == platform
    ).order_by(Contract.id.desc()).first()

    if last_contract:
        last_no = int(last_contract.contract_no[-4:])
        new_no = last_no + 1
    else:
        new_no = 1

    return f"{prefix}2026{platform_code}{new_no:04d}"


# 登录页面
@app.route('/')
def index():
    return render_template('login.html')


# 登录验证(简单示例,实际应使用数据库验证)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # 简单验证示例,实际应查询数据库
    if username and password:
        session['user'] = username
        return redirect(url_for('dashboard'))
    return redirect(url_for('index'))


# 退出登录
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


# 主页面
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')


# 获取合同列表
@app.route('/api/contracts', methods=['GET'])
def get_contracts():
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'contract_no': c.contract_no,
        'contract_name': c.contract_name,
        'project_no': c.project_no,
        'contract_type': c.contract_type,
        'platform': c.platform,
        'contract_amount': str(c.contract_amount) if c.contract_amount else '',
        'sign_date': c.sign_date.strftime('%Y-%m-%d') if c.sign_date else '',
        'company_name': c.company_name,
        'contact_phone': c.contact_phone,
        'manager': c.manager,
        'department': c.department,
        'payment_terms': c.payment_terms,
        'original_contract_no': c.original_contract_no,
        'original_contract_name': c.original_contract_name,
        'remarks': c.remarks,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else ''
    } for c in contracts])


# 创建合同
@app.route('/api/contracts', methods=['POST'])
def create_contract():
    data = request.json

    # 生成合同编号
    contract_no = generate_contract_no(data['contract_type'], data['platform'])

    contract = Contract(
        contract_no=contract_no,
        contract_name=data['contract_name'],
        project_no=data.get('project_no'),
        contract_type=data['contract_type'],
        platform=data['platform'],
        contract_amount=data.get('contract_amount'),
        sign_date=datetime.strptime(data['sign_date'], '%Y-%m-%d') if data.get('sign_date') else None,
        company_name=data['company_name'],
        contact_phone=data['contact_phone'],
        manager=data['manager'],
        department=data['department'],
        payment_terms=data.get('payment_terms'),
        original_contract_no=data.get('original_contract_no'),
        original_contract_name=data.get('original_contract_name'),
        remarks=data.get('remarks')
    )

    db.session.add(contract)
    db.session.commit()

    return jsonify({'success': True, 'contract_no': contract_no, 'id': contract.id})


# 更新合同
@app.route('/api/contracts/<int:contract_id>', methods=['PUT'])
def update_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    data = request.json

    contract.contract_name = data['contract_name']
    contract.project_no = data.get('project_no')
    contract.contract_amount = data.get('contract_amount')
    contract.sign_date = datetime.strptime(data['sign_date'], '%Y-%m-%d') if data.get('sign_date') else None
    contract.company_name = data['company_name']
    contract.contact_phone = data['contact_phone']
    contract.manager = data['manager']
    contract.department = data['department']
    contract.payment_terms = data.get('payment_terms')
    contract.original_contract_no = data.get('original_contract_no')
    contract.original_contract_name = data.get('original_contract_name')
    contract.remarks = data.get('remarks')

    db.session.commit()

    return jsonify({'success': True})


# 删除合同
@app.route('/api/contracts/<int:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    db.session.delete(contract)
    db.session.commit()

    return jsonify({'success': True})


# 导出Excel
@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()

    # 创建工作簿
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "合同列表"

    # 设置标题样式
    header_fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)

    # 表头
    headers = [
        '合同编号', '合同名称', '项目号', '合同类型', '平台',
        '合同金额', '签订日期', '单位名称', '联系电话',
        '合同负责人', '负责人部门', '支付条件',
        '原合同编号', '原合同名称', '备注'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 数据行
    for row, contract in enumerate(contracts, 2):
        ws.cell(row=row, column=1).value = contract.contract_no
        ws.cell(row=row, column=2).value = contract.contract_name
        ws.cell(row=row, column=3).value = contract.project_no
        ws.cell(row=row, column=4).value = contract.contract_type
        ws.cell(row=row, column=5).value = contract.platform
        ws.cell(row=row, column=6).value = float(contract.contract_amount) if contract.contract_amount else ''
        ws.cell(row=row, column=7).value = contract.sign_date.strftime('%Y-%m-%d') if contract.sign_date else ''
        ws.cell(row=row, column=8).value = contract.company_name
        ws.cell(row=row, column=9).value = contract.contact_phone
        ws.cell(row=row, column=10).value = contract.manager
        ws.cell(row=row, column=11).value = contract.department
        ws.cell(row=row, column=12).value = contract.payment_terms
        ws.cell(row=row, column=13).value = contract.original_contract_no
        ws.cell(row=row, column=14).value = contract.original_contract_name
        ws.cell(row=row, column=15).value = contract.remarks

    # 调整列宽
    column_widths = [15, 30, 20, 12, 10, 12, 12, 25, 15, 12, 18, 30, 15, 30, 30]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

    # 保存到内存
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'合同列表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)