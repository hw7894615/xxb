from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response, abort
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import hashlib
from datetime import datetime
import uuid
import csv
from io import BytesIO, StringIO
import tempfile
import logging

# 首先定义基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置日志记录
LOG_FILE = os.path.join(BASE_DIR, 'antchain_logs.log')

# 配置根日志器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建专门的antchain日志器
logger = logging.getLogger('antchain')
logger.setLevel(logging.INFO)

# 确保日志器传播到根日志器
logger.propagate = True

# 测试日志写入
logger.info("="*80)
logger.info("[系统] 日志系统初始化完成")
logger.info(f"[系统] 日志文件路径: {LOG_FILE}")
logger.info("="*80)

# 添加antchain_sdk_twc路径
SDK_PATH = os.path.join(BASE_DIR, '.venv', 'Lib', 'site-packages', 'antchain_sdk_twc')
sys.path.append(SDK_PATH)

from antchain_sdk_twc.client import Client as TWCClient
from antchain_sdk_twc import models as twc_models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mayilian_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'mayilian_enterprise.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = None  # 不限制上传文件大小

# 新增蚂蚁链产品实例ID配置（替代硬编码沙箱环境）
app.config['ANTCHAIN_PRODUCT_INSTANCE_ID'] = "notarycore-api-sandbox"

# 创建上传目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# 数据库模型
class EnterpriseInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    legal_person = db.Column(db.String(100), nullable=False)
    legal_person_id = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.String(100), nullable=False)  # 统一社会信用代码
    mobile_no = db.Column(db.String(20))
    address = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EnterpriseInfo {self.company_name}>'

class NotaryRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(db.Integer, db.ForeignKey('enterprise_info.id'), nullable=False)
    text_content = db.Column(db.Text)  # 文本内容
    file_name = db.Column(db.String(256))  # 文件名
    file_path = db.Column(db.String(512))  # 文件路径
    hash_value = db.Column(db.String(256), nullable=False)
    transaction_id = db.Column(db.String(256))
    proof_url = db.Column(db.String(512))  # 存证证明URL
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    notary_type = db.Column(db.String(20), default='text')  # text或file

    enterprise = db.relationship('EnterpriseInfo', backref=db.backref('notary_records', lazy=True))

    def __repr__(self):
        return f'<NotaryRecord {self.id}>'

# 公证客户端单例
class NotaryClient:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._twc_client = cls._create_client()
        return cls._instance
    
    @staticmethod
    def _create_client():
        # 从配置文件读取配置
        config = twc_models.Config(
            access_key_id=app.config.get('ANTCHAIN_ACCESS_KEY', "ACsbgRMccEcJSqJ6"),
            access_key_secret=app.config.get('ANTCHAIN_SECRET_KEY', "LJTenkppqtQDG2UhGKQcWM6tnuW6dQ3Q"),
            endpoint=app.config.get('ANTCHAIN_ENDPOINT', "openapi.antchain.antgroup.com"),
            read_timeout=20000,
            connect_timeout=20000,
            max_idle_conns=100,
        )
        return TWCClient(config)
    
    def create_trans(self, **kwargs):
        """ 创建存证事务接口 - twc.notary.trans.create """
        logger.info("="*80)
        logger.info(f"[AntChain] 【接口】twc.notary.trans.create (create_trans)")
        logger.info(f"[AntChain] 【请求参数】{kwargs}")
        logger.info(f"[AntChain] 【请求时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        try:
            from antchain_sdk_twc.models import CreateTransRequest
            request = CreateTransRequest(**kwargs)
            response = self._twc_client.create_trans(request)
            
            # 详细记录响应参数
            response_dict = response.__dict__ if hasattr(response, '__dict__') else str(response)
            logger.info(f"[AntChain] 【响应状态】成功")
            logger.info(f"[AntChain] 【响应时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.info(f"[AntChain] 【响应参数】{response_dict}")
            
            # 提取关键信息
            if hasattr(response, 'req_msg_id'):
                logger.info(f"[AntChain] 【关键信息】事务ID: {response.req_msg_id}")
            if hasattr(response, 'code'):
                logger.info(f"[AntChain] 【关键信息】响应码: {response.code}")
            if hasattr(response, 'msg'):
                logger.info(f"[AntChain] 【关键信息】响应消息: {response.msg}")
            
            logger.info("="*80)
            return response
        except Exception as e:
            logger.error(f"[AntChain] 【响应状态】失败")
            logger.error(f"[AntChain] 【异常时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.error(f"[AntChain] 【异常信息】{str(e)}", exc_info=True)
            logger.error("="*80)
            raise
    
    def create_text(self, **kwargs):
        """ 创建文本存证接口 - twc.notary.text.create """
        logger.info("="*80)
        logger.info(f"[AntChain] 【接口】twc.notary.text.create (create_text)")
        logger.info(f"[AntChain] 【请求参数】{kwargs}")
        logger.info(f"[AntChain] 【请求时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        try:
            from antchain_sdk_twc.models import CreateTextRequest
            request = CreateTextRequest(**kwargs)
            response = self._twc_client.create_text(request)
            
            # 详细记录响应参数
            response_dict = response.__dict__ if hasattr(response, '__dict__') else str(response)
            logger.info(f"[AntChain] 【响应状态】成功")
            logger.info(f"[AntChain] 【响应时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.info(f"[AntChain] 【响应参数】{response_dict}")
            
            # 提取关键信息
            if hasattr(response, 'req_msg_id'):
                logger.info(f"[AntChain] 【关键信息】请求ID: {response.req_msg_id}")
            if hasattr(response, 'code'):
                logger.info(f"[AntChain] 【关键信息】响应码: {response.code}")
            if hasattr(response, 'msg'):
                logger.info(f"[AntChain] 【关键信息】响应消息: {response.msg}")
            
            logger.info("="*80)
            return response
        except Exception as e:
            logger.error(f"[AntChain] 【响应状态】失败")
            logger.error(f"[AntChain] 【异常时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.error(f"[AntChain] 【异常信息】{str(e)}", exc_info=True)
            logger.error("="*80)
            raise
    
    def get_file(self, **kwargs):
        """ 获取存证内容接口 - twc.notary.text.get """
        logger.info("="*80)
        logger.info(f"[AntChain] 【接口】twc.notary.text.get (get_file)")
        logger.info(f"[AntChain] 【请求参数】{kwargs}")
        logger.info(f"[AntChain] 【请求时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        try:
            from antchain_sdk_twc.models import GetFileRequest
            request = GetFileRequest(**kwargs)
            response = self._twc_client.get_file(request)
            
            # 详细记录响应参数
            response_dict = response.__dict__ if hasattr(response, '__dict__') else str(response)
            logger.info(f"[AntChain] 【响应状态】成功")
            logger.info(f"[AntChain] 【响应时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.info(f"[AntChain] 【响应参数】{response_dict}")
            
            # 提取关键信息
            if hasattr(response, 'req_msg_id'):
                logger.info(f"[AntChain] 【关键信息】请求ID: {response.req_msg_id}")
            if hasattr(response, 'code'):
                logger.info(f"[AntChain] 【关键信息】响应码: {response.code}")
            if hasattr(response, 'msg'):
                logger.info(f"[AntChain] 【关键信息】响应消息: {response.msg}")
            if hasattr(response, 'notary_content'):
                logger.info(f"[AntChain] 【关键信息】存证内容长度: {len(response.notary_content) if response.notary_content else 0}")
            
            logger.info("="*80)
            return response
        except Exception as e:
            logger.error(f"[AntChain] 【响应状态】失败")
            logger.error(f"[AntChain] 【异常时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.error(f"[AntChain] 【异常信息】{str(e)}", exc_info=True)
            logger.error("="*80)
            raise
    
    def get_trans(self, **kwargs):
        """ 获取事务存证信息接口 - twc.notary.trans.get """
        logger.info("="*80)
        logger.info(f"[AntChain] 【接口】twc.notary.trans.get (get_trans)")
        logger.info(f"[AntChain] 【请求参数】{kwargs}")
        logger.info(f"[AntChain] 【请求时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        try:
            from antchain_sdk_twc.models import GetTransRequest
            request = GetTransRequest(**kwargs)
            response = self._twc_client.get_trans(request)
            
            # 详细记录响应参数
            response_dict = response.__dict__ if hasattr(response, '__dict__') else str(response)
            logger.info(f"[AntChain] 【响应状态】成功")
            logger.info(f"[AntChain] 【响应时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.info(f"[AntChain] 【响应参数】{response_dict}")
            
            # 提取关键信息
            if hasattr(response, 'req_msg_id'):
                logger.info(f"[AntChain] 【关键信息】请求ID: {response.req_msg_id}")
            if hasattr(response, 'code'):
                logger.info(f"[AntChain] 【关键信息】响应码: {response.code}")
            if hasattr(response, 'msg'):
                logger.info(f"[AntChain] 【关键信息】响应消息: {response.msg}")
            if hasattr(response, 'transaction'):
                logger.info(f"[AntChain] 【关键信息】事务信息: 存在")
            
            logger.info("="*80)
            return response
        except Exception as e:
            logger.error(f"[AntChain] 【响应状态】失败")
            logger.error(f"[AntChain] 【异常时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.error(f"[AntChain] 【异常信息】{str(e)}", exc_info=True)
            logger.error("="*80)
            raise
    
    def get_proof(self, **kwargs):
        """ 获取蚂蚁链存证证明接口 - twc.notary.certificate.detail.get """
        logger.info("="*80)
        logger.info(f"[AntChain] 【接口】twc.notary.certificate.detail.get (get_proof)")
        logger.info(f"[AntChain] 【请求参数】{kwargs}")
        logger.info(f"[AntChain] 【请求时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        try:
            from antchain_sdk_twc.models import GetProofRequest
            request = GetProofRequest(**kwargs)
            response = self._twc_client.get_proof(request)
            
            # 详细记录响应参数
            response_dict = response.__dict__ if hasattr(response, '__dict__') else str(response)
            logger.info(f"[AntChain] 【响应状态】成功")
            logger.info(f"[AntChain] 【响应时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.info(f"[AntChain] 【响应参数】{response_dict}")
            
            # 提取关键信息
            if hasattr(response, 'req_msg_id'):
                logger.info(f"[AntChain] 【关键信息】请求ID: {response.req_msg_id}")
            if hasattr(response, 'code'):
                logger.info(f"[AntChain] 【关键信息】响应码: {response.code}")
            if hasattr(response, 'msg'):
                logger.info(f"[AntChain] 【关键信息】响应消息: {response.msg}")
            if hasattr(response, 'proof_url'):
                logger.info(f"[AntChain] 【关键信息】存证证明URL: {response.proof_url}")
            
            logger.info("="*80)
            return response
        except Exception as e:
            logger.error(f"[AntChain] 【响应状态】失败")
            logger.error(f"[AntChain] 【异常时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
            logger.error(f"[AntChain] 【异常信息】{str(e)}", exc_info=True)
            logger.error("="*80)
            raise

# 创建数据库
with app.app_context():
    db.create_all()

# 企业信息管理
@app.route('/enterprise', methods=['GET', 'POST'])
def enterprise_info():
    enterprise = EnterpriseInfo.query.first()
    
    if request.method == 'POST':
        if enterprise:
            # 更新企业信息
            enterprise.company_name = request.form['company_name']
            enterprise.legal_person = request.form['legal_person']
            enterprise.legal_person_id = request.form['legal_person_id']
            enterprise.company_id = request.form['company_id']  # 统一社会信用代码
            enterprise.mobile_no = request.form['mobile_no']
            enterprise.address = request.form['address']
        else:
            # 创建新的企业信息
            enterprise = EnterpriseInfo(
                company_name=request.form['company_name'],
                legal_person=request.form['legal_person'],
                legal_person_id=request.form['legal_person_id'],
                company_id=request.form['company_id'],  # 统一社会信用代码
                mobile_no=request.form['mobile_no'],
                address=request.form['address']
            )
            db.session.add(enterprise)
        
        db.session.commit()
        flash('企业信息已保存', 'success')
        return redirect(url_for('index'))
    
    return render_template('enterprise_info.html', enterprise=enterprise)

@app.route('/')
def index():
    # 从请求参数获取查询关键词
    search_query = request.args.get('search', '')
    
    # 构建查询条件
    query = NotaryRecord.query.join(EnterpriseInfo)
    
    if search_query:
        # 支持对企业名称、文件名称和内容的模糊查询
        query = query.filter(
            db.or_(
                EnterpriseInfo.company_name.like(f'%{search_query}%'),
                NotaryRecord.file_name.like(f'%{search_query}%'),
                NotaryRecord.text_content.like(f'%{search_query}%')
            )
        )
    
    records = query.order_by(NotaryRecord.create_time.desc()).all()
    enterprise = EnterpriseInfo.query.first()
    return render_template('index.html', records=records, enterprise=enterprise, search_query=search_query)

def calculate_file_hash(file_path, chunk_size=4096):
    """ 计算文件的SHA-256哈希值 """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()

@app.route('/notarize', methods=['GET', 'POST'])
def notarize():
    enterprise = EnterpriseInfo.query.first()
    if not enterprise:
        flash('请先填写企业信息', 'warning')
        return redirect(url_for('enterprise_info'))
    
    if request.method == 'POST':
        text_content = request.form.get('text_content')
        file = request.files.get('file')
        
        if not text_content and not file:
            flash('请输入文本内容或上传文件', 'error')
            return redirect(url_for('notarize'))
        
        try:
            record = None
            hash_value = None
            
            # 处理文本存证
            if text_content and text_content.strip():
                hash_value = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
                record = NotaryRecord(
                    enterprise_id=enterprise.id,
                    text_content=text_content,
                    hash_value=hash_value,
                    notary_type='text'
                )
            # 处理文件存证
            elif file and file.filename:
                # 保存文件
                filename = str(uuid.uuid4()) + '_' + file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # 计算文件哈希
                hash_value = calculate_file_hash(file_path)
                
                record = NotaryRecord(
                    enterprise_id=enterprise.id,
                    file_name=file.filename,
                    file_path=file_path,
                    hash_value=hash_value,
                    notary_type='file'
                )
            
            if not record:
                flash('无法创建存证记录', 'error')
                return redirect(url_for('notarize'))
            
            # 保存到数据库
            db.session.add(record)
            db.session.commit()
            logger.info(f"[Notarize] 创建存证记录成功，ID：{record.id}")
            
            # 连接蚂蚁链并创建存证
            client = NotaryClient.get_instance()
            
            # 步骤1：创建企业身份信息（从数据库读取）
            identity = twc_models.Identity(
                user_type='ENTERPRISE',  # 企业类型
                cert_type='UNIFIED_SOCIAL_CREDIT_CODE',  # 统一社会信用代码
                cert_name=enterprise.company_name,  # 企业名称
                cert_no=enterprise.company_id,  # 统一社会信用代码
                legal_person=enterprise.legal_person,  # 法定代表人
                legal_person_id=enterprise.legal_person_id,  # 法定代表人身份证号
                mobile_no=enterprise.mobile_no,  # 企业联系电话
            )
            
            # 步骤2：创建存证事务（从配置读取产品实例ID）
            trans_response = client.create_trans(
                product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID'),
                properties='',
                customer=identity
            )
            
            if hasattr(trans_response, 'req_msg_id'):
                transaction_id = trans_response.req_msg_id
                logger.info(f"[Notarize] 蚂蚁链事务创建成功，事务ID：{transaction_id}")
                
                # 步骤3：创建文本存证（文本哈希或文件哈希）
                text_response = client.create_text(
                    product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID'),
                    transaction_id=transaction_id,
                    text_notary_type='TEXT_HASH',
                    notary_content=hash_value,
                    phase='1',
                    hash_algorithm='SHA256',
                )
                
                # 更新数据库记录
                record.transaction_id = transaction_id
                record.status = 'completed'
                db.session.commit()
                logger.info(f"[Notarize] 存证成功，记录ID：{record.id}")
                
                flash(f'存证成功！事务ID: {transaction_id}', 'success')
            else:
                record.status = 'failed'
                db.session.commit()
                logger.error(f"[Notarize] 蚂蚁链事务创建失败，记录ID：{record.id}")
                flash('存证失败：无法获取事务ID', 'error')
                
        except Exception as e:
            if record:
                record.status = 'failed'
                db.session.commit()
                logger.error(f"[Notarize] 存证失败，记录ID：{record.id if record else '未知'}，错误：{str(e)}", exc_info=True)
            flash(f'存证失败：{str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    return render_template('notarize.html', enterprise=enterprise)

# 批量存证路由（补充缺失的路由）
@app.route('/batch_notarize', methods=['GET', 'POST'])
def batch_notarize():
    enterprise = EnterpriseInfo.query.first()
    if not enterprise:
        flash('请先填写企业信息', 'warning')
        return redirect(url_for('enterprise_info'))
    
    if request.method == 'POST':
        # 处理批量文件上传
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            flash('请选择要上传的文件', 'error')
            return redirect(url_for('batch_notarize'))
        
        success_count = 0
        failed_count = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                # 保存文件
                filename = str(uuid.uuid4()) + '_' + file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # 计算文件哈希
                hash_value = calculate_file_hash(file_path)
                
                # 创建存证记录
                record = NotaryRecord(
                    enterprise_id=enterprise.id,
                    file_name=file.filename,
                    file_path=file_path,
                    hash_value=hash_value,
                    notary_type='file'
                )
                db.session.add(record)
                db.session.commit()
                logger.info(f"[BatchNotarize] 创建存证记录成功，ID：{record.id}")
                
                # 连接蚂蚁链并创建存证
                client = NotaryClient.get_instance()
                
                # 步骤1：创建企业身份信息
                identity = twc_models.Identity(
                    user_type='ENTERPRISE',
                    cert_type='UNIFIED_SOCIAL_CREDIT_CODE',
                    cert_name=enterprise.company_name,
                    cert_no=enterprise.company_id,
                    legal_person=enterprise.legal_person,
                    legal_person_id=enterprise.legal_person_id,
                    mobile_no=enterprise.mobile_no,
                )
                
                # 步骤2：创建存证事务
                trans_response = client.create_trans(
                    product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID'),
                    properties='',
                    customer=identity
                )
                
                if hasattr(trans_response, 'req_msg_id'):
                    transaction_id = trans_response.req_msg_id
                    logger.info(f"[BatchNotarize] 蚂蚁链事务创建成功，事务ID：{transaction_id}")
                    
                    # 步骤3：创建文本存证
                    text_response = client.create_text(
                        product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID'),
                        transaction_id=transaction_id,
                        text_notary_type='TEXT_HASH',
                        notary_content=hash_value,
                        phase='1',
                        hash_algorithm='SHA256',
                    )
                    
                    # 更新数据库记录
                    record.transaction_id = transaction_id
                    record.status = 'completed'
                    db.session.commit()
                    logger.info(f"[BatchNotarize] 存证成功，记录ID：{record.id}")
                    
                    success_count += 1
                else:
                    record.status = 'failed'
                    db.session.commit()
                    logger.error(f"[BatchNotarize] 蚂蚁链事务创建失败，记录ID：{record.id}")
                    failed_count += 1
                
            except Exception as e:
                if 'record' in locals():
                    record.status = 'failed'
                    db.session.commit()
                    logger.error(f"[BatchNotarize] 存证失败，记录ID：{record.id if record else '未知'}，错误：{str(e)}", exc_info=True)
                failed_count += 1
                flash(f'文件 {file.filename} 存证失败：{str(e)}', 'error')
        
        flash(f'批量存证完成！成功：{success_count}，失败：{failed_count}', 'success' if failed_count == 0 else 'warning')
        logger.info(f"[BatchNotarize] 批量存证完成，成功：{success_count}，失败：{failed_count}")
        return redirect(url_for('index'))
    
    # GET请求：渲染批量存证页面
    return render_template('batch_notarize.html', enterprise=enterprise)

# 导出存证记录路由（补充缺失的路由）
@app.route('/export_records')
def export_records():
    """ 导出所有存证记录为CSV文件 """
    try:
        # 查询所有存证记录并关联企业信息
        records = NotaryRecord.query.join(EnterpriseInfo).order_by(NotaryRecord.create_time.desc()).all()
        
        if not records:
            flash('没有可导出的存证记录', 'warning')
            return redirect(url_for('index'))
        
        # 创建CSV文件对象，使用UTF-8编码
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入CSV表头
        writer.writerow([
            '企业名称',
            '存证类型',
            '文件名/内容',
            '哈希值',
            '事务ID',
            '状态',
            '创建时间'
        ])
        
        # 写入记录数据
        for record in records:
            enterprise = record.enterprise
            # 处理内容摘要（文本取前100字符，文件取文件名）
            content = record.text_content[:100] + '...' if record.notary_type == 'text' and record.text_content else record.file_name
            writer.writerow([
                enterprise.company_name,
                '文本存证' if record.notary_type == 'text' else '文件存证',
                content,
                record.hash_value,
                record.transaction_id or '',
                '成功' if record.status == 'completed' else '失败',
                record.create_time.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # 设置CSV文件响应
        output.seek(0)
        
        # 使用ASCII文件名避免中文编码问题
        filename = f"notary_records_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # 创建响应，使用UTF-8编码
        response = make_response(output.getvalue().encode('utf-8'))
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    
    except Exception as e:
        flash(f'导出记录失败：{str(e)}', 'error')
        logger.error(f"[ExportRecords] 导出记录失败，错误：{str(e)}", exc_info=True)
        return redirect(url_for('index'))

# 存证详情路由（补充缺失的路由）
@app.route('/view_record/<int:record_id>')
def view_record(record_id):
    """ 查看存证记录详情 """
    try:
        # 查询存证记录并关联企业信息
        record = NotaryRecord.query.join(EnterpriseInfo).filter(NotaryRecord.id == record_id).first()
        
        if not record:
            flash('存证记录不存在', 'error')
            logger.error(f"[ViewRecord] 存证记录不存在，ID：{record_id}")
            return redirect(url_for('index'))
        
        # 渲染存证详情页面（使用已存在的record_detail.html）
        return render_template('record_detail.html', record=record, enterprise=record.enterprise)
    
    except Exception as e:
        flash(f'查看记录失败：{str(e)}', 'error')
        logger.error(f"[ViewRecord] 查看记录失败，ID：{record_id}，错误：{str(e)}", exc_info=True)
        return redirect(url_for('index'))

# 下载存证文件路由（补充缺失的路由）
@app.route('/download_file/<int:record_id>')
def download_file(record_id):
    """ 下载存证文件 """
    try:
        # 查询存证记录
        record = NotaryRecord.query.filter(NotaryRecord.id == record_id).first()
        if not record or record.notary_type != 'file' or not record.file_path:
            flash('存证文件不存在', 'error')
            logger.error(f"[DownloadFile] 存证文件不存在，记录ID：{record_id}")
            return redirect(url_for('index'))
        
        # 构造文件完整路径
        file_path = os.path.join(BASE_DIR, record.file_path)
        if not os.path.exists(file_path):
            flash('存证文件不存在', 'error')
            logger.error(f"[DownloadFile] 存证文件不存在，路径：{file_path}")
            return redirect(url_for('index'))
        
        # 返回文件下载
        return send_file(
            file_path,
            as_attachment=True,
            download_name=record.file_name,
            mimetype='application/octet-stream'
        )
    
    except Exception as e:
        flash(f'下载文件失败：{str(e)}', 'error')
        logger.error(f"[DownloadFile] 下载文件失败，记录ID：{record_id}，错误：{str(e)}", exc_info=True)
        return redirect(url_for('index'))

# 新增：获取存证内容接口
@app.route('/api/get_file/<int:record_id>', methods=['GET'])
def api_get_file(record_id):
    """ 获取存证内容接口，返回JSON格式数据 """
    try:
        # 查询存证记录
        record = NotaryRecord.query.filter(NotaryRecord.id == record_id).first()
        if not record or not record.transaction_id:
            return jsonify({'code': -1, 'message': '存证记录不存在或无事务ID'})
        
        # 调用蚂蚁链get_file接口
        client = NotaryClient.get_instance()
        response = client.get_file(
            product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID'),
            transaction_id=record.transaction_id,
            tx_hash=record.hash_value
        )
        
        # 返回JSON格式数据
        return jsonify({'code': 0, 'message': '成功', 'data': response.__dict__})
    
    except Exception as e:
        logger.error(f"[API] 获取存证内容失败，记录ID：{record_id}，错误：{str(e)}", exc_info=True)
        return jsonify({'code': -1, 'message': f'获取存证内容失败：{str(e)}'})

# 新增：获取事务所有存证接口
@app.route('/api/get_trans/<int:record_id>', methods=['GET'])
def api_get_trans(record_id):
    """ 获取事务所有存证接口，返回JSON格式数据 """
    try:
        # 查询存证记录
        record = NotaryRecord.query.filter(NotaryRecord.id == record_id).first()
        if not record or not record.transaction_id:
            return jsonify({'code': -1, 'message': '存证记录不存在或无事务ID'})
        
        # 调用蚂蚁链get_trans接口
        client = NotaryClient.get_instance()
        response = client.get_trans(
            transaction_id=record.transaction_id,
            product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID')
        )
        
        # 返回JSON格式数据
        return jsonify({'code': 0, 'message': '成功', 'data': response.__dict__})
    
    except Exception as e:
        logger.error(f"[API] 获取事务所有存证失败，记录ID：{record_id}，错误：{str(e)}", exc_info=True)
        return jsonify({'code': -1, 'message': f'获取事务所有存证失败：{str(e)}'})

# 新增：获取存证证明接口
@app.route('/api/get_proof/<int:record_id>', methods=['GET'])
def api_get_proof(record_id):
    """ 获取存证证明接口，返回JSON格式数据 """
    try:
        # 查询存证记录
        record = NotaryRecord.query.filter(NotaryRecord.id == record_id).first()
        if not record or not record.transaction_id:
            return jsonify({'code': -1, 'message': '存证记录不存在或无事务ID'})
        
        # 调用蚂蚁链get_proof接口
        client = NotaryClient.get_instance()
        response = client.get_proof(
            product_instance_id=app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID'),
            transaction_id=record.transaction_id
        )
        
        # 更新数据库中的存证证明URL
        record.proof_url = response.proof_url
        db.session.commit()
        logger.info(f"[API] 获取存证证明成功，记录ID：{record_id}，证明URL：{response.proof_url}")
        
        # 返回JSON格式数据
        return jsonify({'code': 0, 'message': '成功', 'data': response.__dict__})
    
    except Exception as e:
        logger.error(f"[API] 获取存证证明失败，记录ID：{record_id}，错误：{str(e)}", exc_info=True)
        return jsonify({'code': -1, 'message': f'获取存证证明失败：{str(e)}'})

# 新增：验证哈希值接口
@app.route('/api/verify_hash/<int:record_id>', methods=['GET'])
def api_verify_hash(record_id):
    """ 验证哈希值接口，返回JSON格式数据 """
    try:
        # 查询存证记录
        record = NotaryRecord.query.filter(NotaryRecord.id == record_id).first()
        if not record:
            return jsonify({'code': -1, 'message': '存证记录不存在'})
        
        # 重新计算哈希值
        calculated_hash = None
        
        if record.notary_type == 'text' and record.text_content:
            # 文本存证：重新计算文本哈希
            calculated_hash = hashlib.sha256(record.text_content.encode('utf-8')).hexdigest()
        elif record.notary_type == 'file' and record.file_path:
            # 文件存证：重新计算文件哈希
            file_path = os.path.join(BASE_DIR, record.file_path)
            if os.path.exists(file_path):
                calculated_hash = calculate_file_hash(file_path)
            else:
                return jsonify({'code': -1, 'message': '存证文件不存在'})
        else:
            return jsonify({'code': -1, 'message': '无效的存证类型或内容'})
        
        # 对比哈希值
        is_match = calculated_hash == record.hash_value
        
        # 返回验证结果
        return jsonify({
            'code': 0,
            'message': '成功',
            'is_match': is_match,
            'stored_hash': record.hash_value,
            'calculated_hash': calculated_hash
        })
    
    except Exception as e:
        logger.error(f"[API] 哈希值验证失败，记录ID：{record_id}，错误：{str(e)}", exc_info=True)
        return jsonify({'code': -1, 'message': f'哈希值验证失败：{str(e)}'})

# 其他路由（所有涉及product_instance_id的地方均已修改）
# ...（以下路由中的product_instance_id均改为app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID')）

@app.route('/config', methods=['GET', 'POST'])
def config():
    """ 网关配置管理页面 """
    if request.method == 'POST':
        # 保存配置到Flask配置中
        app.config['ANTCHAIN_ACCESS_KEY'] = request.form.get('access_key', "ACsbgRMccEcJSqJ6")
        app.config['ANTCHAIN_SECRET_KEY'] = request.form.get('secret_key', "LJTenkppqtQDG2UhGKQcWM6tnuW6dQ3Q")
        app.config['ANTCHAIN_ENDPOINT'] = request.form.get('endpoint', "openapi.antchain.antgroup.com")
        # 新增产品实例ID配置
        app.config['ANTCHAIN_PRODUCT_INSTANCE_ID'] = request.form.get('product_instance_id', "notarycore-api-sandbox")
        
        # 重启NotaryClient以加载新配置
        global NotaryClient
        NotaryClient._instance = None
        
        flash('配置已保存', 'success')
        logger.info(f"[Config] 蚂蚁链配置已更新，产品实例ID：{app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID')}")
        return redirect(url_for('config'))
    
    # 获取当前配置
    config_data = {
        'access_key': app.config.get('ANTCHAIN_ACCESS_KEY', "ACsbgRMccEcJSqJ6"),
        'secret_key': app.config.get('ANTCHAIN_SECRET_KEY', "LJTenkppqtQDG2UhGKQcWM6tnuW6dQ3Q"),
        'endpoint': app.config.get('ANTCHAIN_ENDPOINT', "openapi.antchain.antgroup.com"),
        # 新增产品实例ID配置
        'product_instance_id': app.config.get('ANTCHAIN_PRODUCT_INSTANCE_ID', "notarycore-api-sandbox")
    }
    
    return render_template('config.html', config=config_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)