import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showwarning
import sys


class NotaryContentInput:
    def __init__(self, parent, max_attempts=2):
        self.parent = parent
        self.max_attempts = max_attempts
        self.attempts = 0

        self.entries = {}
        # 创建输入窗口
        self.window = tk.Toplevel(parent)
        self.window.title("公证内容输入验证")
        self.window.geometry("400x200")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)  # 窗口关闭事件处理
        # 🔧 添加关键初始化代码
        self.validated_content = tk.StringVar()  # 使用StringVar替代普通变量
        self.validation_success = tk.BooleanVar(False)  # 新增验证状态标志

        # 绑定变量到父组件
        # self.parent.on_validation_result(self.validation_success, self.validated_content)

        # 字段配置
        self.fields = [
            ("notary_content", "公证内容", True, self.validate_notary_content)
        ]

        self.create_widgets()

    def create_widgets(self):
        """创建输入界面组件"""
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 表头
        header_labels = ["字段", "值"]
        for col, label in enumerate(header_labels):
            ttk.Label(frame, text=label, anchor=tk.E).grid(row=0, column=col, sticky=tk.E)

        # 动态创建输入行
        for row_idx, (field_name, label, required, validate) in enumerate(self.fields, 1):
            ttk.Label(frame, text=label).grid(row=row_idx, column=0, sticky=tk.W, padx=5, pady=2)

            entry = ttk.Entry(frame, width=30)
            entry.grid(row=row_idx, column=1, padx=5, pady=2)
            self.entries[field_name] = entry

            if required:
                self.add_validation(entry, validate, f"{label}不能为空")

        # 操作按钮
        btn_frame = ttk.Frame(frame, padding="10")
        btn_frame.grid(row=len(self.fields) + 1, column=0, columnspan=2, sticky=tk.EW)

        ttk.Button(btn_frame, text="验证", command=self.validate_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

        # 错误提示
        self.error_label = ttk.Label(frame, text="", foreground="red")
        self.error_label.grid(row=len(self.fields) + 2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    def add_validation(self, entry, validate_func, error_msg):
        """为输入框添加验证"""

        def on_validate(event):
            try:
                validate_func(entry.get())
                self.error_label.config(text="", foreground="green")
                self.attempts = 0  # 重置尝试次数
            except ValueError as e:
                self.attempts += 1
                self.error_label.config(
                    text=f"输入错误 ({self.attempts}/{self.max_attempts}): {str(e)}",
                    foreground="red"
                )
                if self.attempts >= self.max_attempts:
                    showwarning("输入验证失败", "已达到最大尝试次数，请检查输入格式")

        entry.config(validatecommand=(entry.register(on_validate), '%P'))

    def validate_notary_content(self, value):
        """公证内容验证逻辑"""
        if not value.strip():
            raise ValueError("内容不能为空")
        if len(value) > 500:
            raise ValueError("内容长度不能超过500字符")
        if not value.isalnum():
            raise ValueError("只能包含字母和数字")

    def validate_input(self):
        """验证输入内容"""
        try:
            content = self.entries["notary_content"].get().strip()
            self.validation_success = True
            self.validated_content.set(content)  # 设置StringVar值
            self.window.destroy()
            return True
        except ValueError as e:
            self.attempts += 1
            if self.attempts >= self.max_attempts:
                showwarning("输入验证失败", "已达到最大尝试次数，请检查输入格式")
                self.window.destroy()
                return False
            self.error_label.config(
                text=f"输入错误 ({self.attempts}/{self.max_attempts}): {str(e)}",
                foreground="red"
            )
            return False

    def on_close(self):
        """窗口关闭处理"""
        self.validated_content = None
        self.parent.on_input_validation_failure()


class NotaryApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口

        # 初始化公证客户端
        # self.client = NotaryClient()

        # 获取交易ID（需要根据实际情况实现）
        # self.req_msg_id = "1234567890"  # 示例值

        # 🌐 正确初始化输入验证器（关键修复）
        self.input_validator = NotaryContentInput(self.root)

        # 绑定验证结果
        self.input_validator.validated_content.trace(
            "w",
            lambda *args: self.handle_validated_content(args[1])  # 确保方法存在
        )
        self.input_validator.validation_success.trace(
            "w",
            lambda *args: self.handle_validation_status(args[1])
        )


def handle_validated_content(self, content):
        if content.strip():
            try:
                # 调用文本创建接口
                # text_response = self.client.create_text(
                #     product_instance_id=self.client._base_config["product_instance_id"],
                #     transaction_id=self.req_msg_id,
                #     text_notary_type='TEXT_HASH',
                #     notary_content=content,
                #     phase='1',
                #     hash_algorithm='SHA256',
                #     location=twc_models.Location(city="上海", ip="192.168.1.1")
                # )
                print("Text Response:", tcontent)
            except Exception as e:
                showerror("操作失败", f"创建文本公证失败: {str(e)}")
                sys.exit(1)
        else:
            showerror("输入验证失败", "未获取有效公证内容")
            sys.exit(1)


def handle_validation_status(self, is_valid):
    """处理验证状态变化"""
    if not is_valid and self.input_validator.attempts >= self.input_validator.max_attempts:
        self.input_validator.window.destroy()

if __name__ == "__main__":
    app = NotaryApp()
    app.input_validator.window.wait_window()  # 等待验证窗口关闭
    sys.exit(0)