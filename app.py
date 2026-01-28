from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# 数据库配置
# 临时切换到本地SQLite数据库以解决远程连接权限问题
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contract.db'
#原MySQL配置（如需恢复远程连接，请取消注释下方代码并注释掉上方SQLite配置）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ProjectDB:4100282Ly%40@47.108.254.13/projectdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 数据库模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    realname = db.Column(db.String(100))
    department = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.now)

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
    corporate_principal = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    payment_terms = db.Column(db.Text)
    original_contract_no = db.Column(db.String(50))
    original_contract_name = db.Column(db.String(200))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    executive_partner = db.Column(db.String(255))
    filler = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')  # active, invalid


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


# 登录验证
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    
    # 验证逻辑：
    # 1. 如果数据库中存在该用户
    # 2. 检查密码是否匹配（支持明文比对或 Hash 比对，优先 Hash）
    # 3. 如果是 admin/admin123，且数据库中没有该用户，我们稍后通过 init_admin 确保其存在
    
    is_valid = False
    if user:
        if check_password_hash(user.password, password):
            is_valid = True
        elif user.password == password: # 兼容明文存储的情况
            is_valid = True
            
    if is_valid:
        session['user'] = user.username
        session['realname'] = user.realname
        return redirect(url_for('dashboard'))
        
    return render_template('login.html', error='用户名或密码错误')


# 初始化数据库和管理员账号
def init_admin():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                realname='系统管理员',
                department='管理部'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created.")

# 在应用启动时尝试初始化管理员
# init_admin()


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
    query = Contract.query

    # 筛选
    exec_partner = request.args.get('executive_partner')
    filler = request.args.get('filler')
    
    if exec_partner:
        query = query.filter(Contract.executive_partner == exec_partner)
    if filler:
        query = query.filter(Contract.filler == filler)

    contracts = query.order_by(Contract.created_at.desc()).all()
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
        'corporate_principal': c.corporate_principal,
        'department': c.department,
        'payment_terms': c.payment_terms,
        'original_contract_no': c.original_contract_no,
        'original_contract_name': c.original_contract_name,
        'remarks': c.remarks,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else '',
        'executive_partner': c.executive_partner,
        'filler': c.filler,
        'status': c.status
    } for c in contracts])


# 获取筛选选项
@app.route('/api/contracts/filter_options', methods=['GET'])
def get_filter_options():
    partners = db.session.query(Contract.executive_partner).distinct().filter(Contract.executive_partner != None).all()
    fillers = db.session.query(Contract.filler).distinct().filter(Contract.filler != None).all()
    
    return jsonify({
        'executive_partners': [p[0] for p in partners if p[0]],
        'fillers': [f[0] for f in fillers if f[0]]
    })


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
        corporate_principal=data['corporate_principal'],
        department=data['department'],
        payment_terms=data.get('payment_terms'),
        original_contract_no=data.get('original_contract_no'),
        original_contract_name=data.get('original_contract_name'),
        remarks=data.get('remarks'),
        executive_partner=data.get('executive_partner'),
        filler=data.get('filler'),
        status='active'
    )

    db.session.add(contract)
    db.session.commit()

    return jsonify({'success': True, 'contract_no': contract_no, 'id': contract.id})


# 更新合同
@app.route('/api/contracts/<int:contract_id>', methods=['PUT'])
def update_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if contract.status == 'invalid':
        return jsonify({'success': False, 'message': '已作废的合同不可编辑'}), 400
        
    data = request.json

    contract.contract_name = data['contract_name']
    contract.project_no = data.get('project_no')
    contract.contract_amount = data.get('contract_amount')
    contract.sign_date = datetime.strptime(data['sign_date'], '%Y-%m-%d') if data.get('sign_date') else None
    contract.company_name = data['company_name']
    contract.contact_phone = data['contact_phone']
    contract.corporate_principal = data['corporate_principal']
    contract.department = data['department']
    contract.payment_terms = data.get('payment_terms')
    contract.original_contract_no = data.get('original_contract_no')
    contract.original_contract_name = data.get('original_contract_name')
    contract.remarks = data.get('remarks')
    contract.executive_partner = data.get('executive_partner')
    contract.filler = data.get('filler')

    db.session.commit()

    return jsonify({'success': True})


# 作废合同
@app.route('/api/contracts/<int:contract_id>/void', methods=['POST'])
def void_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    contract.status = 'invalid'
    db.session.commit()
    return jsonify({'success': True})


# 检查是否可以删除
@app.route('/api/contracts/<int:contract_id>/check_delete', methods=['GET'])
def check_delete(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    
    # 检查该合同编号之后是否已有其他项目被创建
    # 逻辑：查询同类型同平台下，ID比当前大的合同
    subsequent = Contract.query.filter(
        Contract.contract_type == contract.contract_type,
        Contract.platform == contract.platform,
        Contract.id > contract.id
    ).first()
    
    if subsequent:
        return jsonify({
            'can_delete': False,
            'message': '该合同编号后续已有项目创建，不可删除。如需停用，请使用“作废”功能。'
        })
    else:
        return jsonify({'can_delete': True})


# 删除合同
@app.route('/api/contracts/<int:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    
    # 再次检查安全性
    subsequent = Contract.query.filter(
        Contract.contract_type == contract.contract_type,
        Contract.platform == contract.platform,
        Contract.id > contract.id
    ).first()
    
    if subsequent:
        return jsonify({'success': False, 'message': '该合同编号后续已有项目创建，不可删除。'}), 400
        
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
        '序号', '合同编号', '合同名称', '项目号', '合同类型', '所属平台',
        '合同金额 (元)', '签订日期', '单位名称', '企业负责人', '联系电话',
        '执行合伙人', '填表人', '所属部门', '支付条件',
        '原合同编号', '原合同名称', '状态', '备注', '创建时间', '更新时间'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 数据行
    total_count = len(contracts)
    for i, contract in enumerate(contracts):
        row = i + 2
        ws.cell(row=row, column=1).value = total_count - i  # 自然序号倒序
        ws.cell(row=row, column=2).value = contract.contract_no
        ws.cell(row=row, column=3).value = contract.contract_name
        ws.cell(row=row, column=4).value = contract.project_no
        ws.cell(row=row, column=5).value = contract.contract_type
        ws.cell(row=row, column=6).value = contract.platform
        ws.cell(row=row, column=7).value = float(contract.contract_amount) if contract.contract_amount else 0
        ws.cell(row=row, column=8).value = contract.sign_date.strftime('%Y-%m-%d') if contract.sign_date else ''
        ws.cell(row=row, column=9).value = contract.company_name
        ws.cell(row=row, column=10).value = contract.corporate_principal
        ws.cell(row=row, column=11).value = contract.contact_phone
        ws.cell(row=row, column=12).value = contract.executive_partner
        ws.cell(row=row, column=13).value = contract.filler
        ws.cell(row=row, column=14).value = contract.department
        ws.cell(row=row, column=15).value = contract.payment_terms
        ws.cell(row=row, column=16).value = contract.original_contract_no
        ws.cell(row=row, column=17).value = contract.original_contract_name
        ws.cell(row=row, column=18).value = '已作废' if contract.status == 'invalid' else '正常'
        ws.cell(row=row, column=19).value = contract.remarks
        ws.cell(row=row, column=20).value = contract.created_at.strftime('%Y-%m-%d %H:%M:%S') if contract.created_at else ''
        ws.cell(row=row, column=21).value = contract.updated_at.strftime('%Y-%m-%d %H:%M:%S') if contract.updated_at else ''

    # 调整列宽
    column_widths = [8, 15, 30, 20, 12, 12, 15, 12, 25, 12, 15, 12, 12, 18, 30, 15, 25, 10, 30, 20, 20]
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
        download_name=f'合同列表_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5600)