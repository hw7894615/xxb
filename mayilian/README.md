# 蚂蚁链存证系统（企业版）

基于蚂蚁链技术构建的安全、可信的电子数据存证服务，为企业提供专业的区块链存证解决方案。

## 🌟 功能特性

### 核心功能
- ✅ **企业信息管理** - 完善的企业身份信息管理
- ✅ **文本存证** - 支持文本内容的区块链存证
- ✅ **文件存证** - 支持多种格式文件的哈希存证
- ✅ **批量存证** - 支持多文件批量上传存证（新增）
- ✅ **记录导出** - 支持存证记录CSV格式导出（新增）
- ✅ **存证验证** - 实时验证存证数据的完整性和真实性
- ✅ **区块链查询** - 查询蚂蚁链上的存证事务信息

### 技术特点
- 🔒 **区块链技术** - 基于蚂蚁链，确保数据不可篡改
- 🔐 **加密存储** - SHA-256哈希算法，保护用户隐私
- 📊 **数据管理** - 完整的存证记录管理和查询功能
- 🌐 **Web界面** - 直观易用的用户界面
- 📤 **数据导出** - 支持CSV格式数据导出

## 📋 系统要求

- Python 3.8+
- Flask 3.1+
- SQLAlchemy
- 蚂蚁链SDK (antchain_sdk_twc)

## 🚀 安装和部署

### 1. 克隆项目

```bash
git clone <项目地址>
cd mayilian
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

### 3. 激活虚拟环境

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置蚂蚁链SDK

确保蚂蚁链SDK已安装在虚拟环境中：
```bash
pip install antchain_sdk_twc
```

### 6. 配置应用参数

编辑 `app_new_enterprise.py` 中的配置参数：

```python
# 蚂蚁链配置
app.config['ANTCHAIN_ACCESS_KEY'] = "your_access_key"
app.config['ANTCHAIN_SECRET_KEY'] = "your_secret_key"
app.config['ANTCHAIN_ENDPOINT'] = "openapi.antchain.antgroup.com"

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mayilian_enterprise.db'

# 文件上传配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### 7. 启动应用


**使用命令行：**
```bash
必须指向完整路径D:/git_xxb/xxb/mayilian/.venv/Scripts/python.exe d:/git_xxb/xxb/mayilian/app_new_enterprise.py
```

应用将在 `http://127.0.0.1:5002` 启动

## 📖 使用说明

### 首次使用流程

1. **设置企业信息**
   - 访问首页，点击"设置企业信息"
   - 填写企业名称、法定代表人、统一社会信用代码等信息
   - 保存企业信息

2. **单个文件/文本存证**
   - 点击"新增加密存证"
   - 选择存证类型（文本或文件）
   - 填写文本内容或上传文件
   - 提交存证

3. **批量文件存证**
   - 点击"批量文件存证"
   - 选择多个文件（按住 Ctrl 或 Shift）
   - 点击"批量提交存证"
   - 查看处理结果

4. **导出存证记录**
   - 点击"导出记录"按钮
   - 自动下载CSV文件
   - 用Excel或其他工具打开查看

### 功能详解

#### 企业信息管理
- **路径：** `/enterprise`
- **功能：** 管理企业基本信息，包括：
  - 企业名称
  - 法定代表人
  - 法定代表人身份证号
  - 统一社会信用代码
  - 联系电话
  - 企业地址

#### 单个存证
- **路径：** `/notarize`
- **功能：** 单个文件或文本的区块链存证
- **支持格式：** .txt, .pdf, .doc, .docx, .jpg, .png, .gif, .zip, .rar, .xlsx, .xls
- **文件大小限制：** 单个文件最大16MB

#### 批量存证
- **路径：** `/batch_notarize`
- **功能：** 多文件批量上传存证
- **特点：**
  - 一次可上传多个文件
  - 每个文件独立处理
  - 实时显示处理进度
  - 失败文件不影响其他文件

#### 记录导出
- **路径：** `/export_records`
- **功能：** 导出所有存证记录为CSV文件
- **导出内容：**
  - 序号
  - 企业名称
  - 存证类型
  - 文件名/内容摘要
  - 哈希值
  - 事务ID
  - 状态
  - 创建时间

#### 存证记录查看
- **路径：** `/record/<record_id>`
- **功能：** 查看存证记录详情
- **包含信息：**
  - 存证基本信息
  - 哈希值验证
  - 蚂蚁链事务信息
  - 存证证明

## 🔌 API接口

### 获取存证记录列表
```
GET /api/records?search=关键词
```

### 获取存证内容
```
GET /api/get_file/<record_id>
```

### 获取事务信息
```
GET /api/get_trans/<record_id>
```

### 获取存证证明
```
GET /api/get_proof/<record_id>
```

### 验证哈希值
```
GET /api/verify_hash/<record_id>
```

### 下载存证文件
```
GET /download/<record_id>
```

## 🗄️ 数据库结构

### EnterpriseInfo（企业信息表）
- `id` - 主键
- `company_name` - 企业名称
- `legal_person` - 法定代表人
- `legal_person_id` - 法定代表人身份证号
- `company_id` - 统一社会信用代码
- `mobile_no` - 联系电话
- `address` - 企业地址
- `create_time` - 创建时间
- `update_time` - 更新时间

### NotaryRecord（存证记录表）
- `id` - 主键
- `enterprise_id` - 企业ID（外键）
- `text_content` - 文本内容
- `file_name` - 文件名
- `file_path` - 文件路径
- `hash_value` - 哈希值
- `transaction_id` - 蚂蚁链事务ID
- `proof_url` - 存证证明URL
- `create_time` - 创建时间
- `status` - 状态（pending/completed/failed）
- `notary_type` - 存证类型（text/file）

## 🔧 配置说明

### 蚂蚁链配置
在 `app_new_enterprise.py` 中配置：
```python
app.config['ANTCHAIN_ACCESS_KEY'] = "your_access_key"
app.config['ANTCHAIN_SECRET_KEY'] = "your_secret_key"
app.config['ANTCHAIN_ENDPOINT'] = "openapi.antchain.antgroup.com"
```

### 数据库配置
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mayilian_enterprise.db'
```

### 文件上传配置
```python
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

## 🛡️ 安全说明

1. **数据安全**
   - 所有存证内容使用SHA-256哈希算法加密
   - 原始文件仅保存在本地服务器
   - 哈希值上传至蚂蚁链，确保不可篡改

2. **访问控制**
   - 建议在生产环境中添加用户认证
   - 配置HTTPS加密传输
   - 设置适当的文件访问权限

3. **数据备份**
   - 定期备份数据库文件
   - 备份上传的原始文件
   - 保存蚂蚁链事务ID用于查询验证

## ❓ 常见问题

### 1. 存证失败怎么办？
- 检查蚂蚁链配置是否正确
- 确认网络连接正常
- 查看错误日志获取详细信息

### 2. 如何验证存证的真实性？
- 使用"查看"功能查看存证详情
- 点击"验证哈希"按钮
- 对比本地计算的哈希值与链上哈希值

### 3. 批量存证有数量限制吗？
- 建议单次上传不超过10个文件
- 每个文件大小限制为16MB
- 处理时间与文件数量和大小成正比

### 4. 导出的CSV文件乱码怎么办？
- 使用Excel打开时选择UTF-8编码
- 或使用记事本、文本编辑器打开
- CSV文件已包含UTF-8 BOM，Excel应该能正确识别

### 5. 如何修改企业信息？
- 访问首页，点击企业名称旁的编辑按钮
- 或直接访问 `/enterprise` 路径

## 📞 技术支持

如有问题或建议，请联系技术支持团队。

## 📄 许可证

本项目仅供学习和研究使用。

## 🙏 致谢

- 蚂蚁链团队提供的区块链技术支持
- Flask、SQLAlchemy等开源项目

---

**版本：** 1.0.0  
**更新日期：** 2024-03-11  
**维护者：** 蚂蚁链存证系统开发团队
