import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import threading
import importlib.util

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


# 动态导入模块
def load_module(module_name, class_name=None):
    """动态导入模块和类"""
    try:
        # 尝试直接导入
        if class_name:
            module = __import__(module_name)
            return getattr(module, class_name)
        else:
            return __import__(module_name)
    except ImportError:
        # 如果直接导入失败，尝试从文件导入
        file_path = os.path.join(current_dir, f"{module_name}.py")
        if not os.path.exists(file_path):
            raise ImportError(f"找不到模块文件: {file_path}")

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if class_name:
            return getattr(module, class_name)
        else:
            return module


# 尝试导入模块
try:
    CharacterCardGenerator = load_module("character_card_generator", "CharacterCardGenerator")
except Exception as e:
    print(f"无法导入 CharacterCardGenerator: {e}")
    CharacterCardGenerator = None

try:
    SchoolCardsToPNG = load_module("school_cards_to_png", "SchoolCardsToPNG")
except Exception as e:
    print(f"无法导入 SchoolCardsToPNG: {e}")
    SchoolCardsToPNG = None

try:
    create_pdf_from_pages = load_module("mix_pdf", "create_pdf_from_pages")
except Exception as e:
    print(f"无法导入 create_pdf_from_pages: {e}")
    create_pdf_from_pages = None


class CharacterCardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("角色卡生成器")
        self.root.geometry("600x500")

        # 检查模块是否成功导入
        if not all([CharacterCardGenerator, SchoolCardsToPNG, create_pdf_from_pages]):
            self.show_module_error()
            return

        # 加载配置
        self.config = self.load_config()

        # 创建界面
        self.create_widgets()

        # 更新界面显示
        self.update_display()

    def show_module_error(self):
        """显示模块导入错误"""
        error_text = "无法导入必要的模块。请确保以下文件存在:\n\n"
        error_text += "- character_card_generator.py\n"
        error_text += "- school_cards_to_png.py\n"
        error_text += "- mix_pdf.py\n\n"
        error_text += "这些文件应该与main.py在同一个目录中。"

        label = tk.Label(self.root, text=error_text, justify=tk.LEFT, padx=20, pady=20)
        label.pack(fill=tk.BOTH, expand=True)

        button = tk.Button(self.root, text="退出", command=self.root.quit)
        button.pack(pady=10)

    def load_config(self):
        """加载配置文件"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建默认配置
            default_config = {
                "font_path": "",
                "cards_per_row": 3,
                "cards_folder": "character_cards",
                "pages_folder": "pages",
                "students_pdf": "students.pdf",
                "dpi": 300,
                "margin": 80,
                "school_order": ["阿拜多斯", "圣三一", "格黑娜", "千年"]
            }
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
            return {}

    def save_config(self):
        """保存配置文件"""
        # 更新配置字典
        self.config["font_path"] = self.font_path_var.get()
        self.config["cards_per_row"] = int(self.cards_per_row_var.get())
        self.config["cards_folder"] = self.cards_folder_var.get()
        self.config["pages_folder"] = self.pages_folder_var.get()
        self.config["students_pdf"] = self.students_pdf_var.get()
        self.config["school_order"] = [s.strip() for s in self.school_order_var.get().split(",") if s.strip()]

        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "配置已保存")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            return False

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置行号
        row = 0

        # 字体路径
        ttk.Label(main_frame, text="字体路径:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.font_path_var = tk.StringVar(value=self.config.get("font_path", ""))
        font_entry = ttk.Entry(main_frame, textvariable=self.font_path_var, width=50)
        font_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(main_frame, text="浏览", command=self.browse_font).grid(row=row, column=2, pady=5, padx=(5, 0))
        row += 1

        # 每行卡片数量
        ttk.Label(main_frame, text="每行卡片数量:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cards_per_row_var = tk.StringVar(value=str(self.config.get("cards_per_row", 3)))
        cards_per_row_combo = ttk.Combobox(main_frame, textvariable=self.cards_per_row_var,
                                           values=[2, 3, 4, 5, 6], state="readonly", width=10)
        cards_per_row_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        row += 1

        # 角色卡文件夹
        ttk.Label(main_frame, text="角色卡文件夹:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cards_folder_var = tk.StringVar(value=self.config.get("cards_folder", "character_cards"))
        cards_folder_entry = ttk.Entry(main_frame, textvariable=self.cards_folder_var, width=50)
        cards_folder_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(main_frame, text="浏览", command=self.browse_cards_folder).grid(row=row, column=2, pady=5,
                                                                                   padx=(5, 0))
        row += 1

        # 页面文件夹
        ttk.Label(main_frame, text="页面文件夹:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.pages_folder_var = tk.StringVar(value=self.config.get("pages_folder", "pages"))
        pages_folder_entry = ttk.Entry(main_frame, textvariable=self.pages_folder_var, width=50)
        pages_folder_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(main_frame, text="浏览", command=self.browse_pages_folder).grid(row=row, column=2, pady=5,
                                                                                   padx=(5, 0))
        row += 1

        # 输出PDF文件
        ttk.Label(main_frame, text="输出PDF文件:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.students_pdf_var = tk.StringVar(value=self.config.get("students_pdf", "students.pdf"))
        students_pdf_entry = ttk.Entry(main_frame, textvariable=self.students_pdf_var, width=50)
        students_pdf_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(main_frame, text="浏览", command=self.browse_pdf_file).grid(row=row, column=2, pady=5, padx=(5, 0))
        row += 1

        # 学院顺序
        ttk.Label(main_frame, text="学院顺序 (用逗号分隔):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.school_order_var = tk.StringVar(value=", ".join(self.config.get("school_order", [])))
        school_order_entry = ttk.Entry(main_frame, textvariable=self.school_order_var, width=50)
        school_order_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        row += 1

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)

        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="生成角色卡", command=self.generate_cards).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="生成页面", command=self.generate_pages).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="生成PDF", command=self.generate_pdf).pack(side=tk.LEFT, padx=5)
        row += 1

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1

        # 日志文本框
        ttk.Label(main_frame, text="日志:").grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1

        self.log_text = tk.Text(main_frame, height=10, width=70)
        self.log_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=row, column=3, sticky=(tk.N, tk.S), pady=5)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # 配置权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(row, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def update_display(self):
        """更新界面显示"""
        self.font_path_var.set(self.config.get("font_path", ""))
        self.cards_per_row_var.set(str(self.config.get("cards_per_row", 3)))
        self.cards_folder_var.set(self.config.get("cards_folder", "character_cards"))
        self.pages_folder_var.set(self.config.get("pages_folder", "pages"))
        self.students_pdf_var.set(self.config.get("students_pdf", "students.pdf"))
        self.school_order_var.set(", ".join(self.config.get("school_order", [])))

    def browse_font(self):
        """浏览字体文件"""
        filename = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[("字体文件", "*.ttf *.otf"), ("所有文件", "*.*")]
        )
        if filename:
            self.font_path_var.set(filename)

    def browse_cards_folder(self):
        """浏览角色卡文件夹"""
        folder = filedialog.askdirectory(title="选择角色卡文件夹")
        if folder:
            self.cards_folder_var.set(folder)

    def browse_pages_folder(self):
        """浏览页面文件夹"""
        folder = filedialog.askdirectory(title="选择页面文件夹")
        if folder:
            self.pages_folder_var.set(folder)

    def browse_pdf_file(self):
        """浏览PDF文件"""
        filename = filedialog.asksaveasfilename(
            title="选择输出PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if filename:
            self.students_pdf_var.set(filename)

    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def generate_cards(self):
        """生成角色卡"""
        # 保存配置
        if not self.save_config():
            return

        # 启动进度条
        self.progress.start()
        self.log("开始生成角色卡...")

        # 在新线程中执行生成任务
        thread = threading.Thread(target=self._generate_cards_thread)
        thread.daemon = True
        thread.start()

    def _generate_cards_thread(self):
        """生成角色卡的线程函数"""
        try:
            # 这里需要您提供角色名称列表
            # 暂时使用示例数据
            character_names = ["砂狼 白子", "小鸟游 星野", "奥空 绫音"]

            generator = CharacterCardGenerator("config.json")
            success = generator.batch_create_cards(character_names, self.config["cards_folder"])

            if success:
                self.log("角色卡生成完成")
            else:
                self.log("角色卡生成失败")

        except Exception as e:
            self.log(f"生成角色卡时出错: {str(e)}")

        finally:
            # 停止进度条
            self.progress.stop()

    def generate_pages(self):
        """生成页面"""
        # 保存配置
        if not self.save_config():
            return

        # 启动进度条
        self.progress.start()
        self.log("开始生成页面...")

        # 在新线程中执行生成任务
        thread = threading.Thread(target=self._generate_pages_thread)
        thread.daemon = True
        thread.start()

    def _generate_pages_thread(self):
        """生成页面的线程函数"""
        try:
            generator = SchoolCardsToPNG("config.json")
            success = generator.create_pages_by_schools()

            if success:
                self.log("页面生成完成")
            else:
                self.log("页面生成失败")

        except Exception as e:
            self.log(f"生成页面时出错: {str(e)}")

        finally:
            # 停止进度条
            self.progress.stop()

    def generate_pdf(self):
        """生成PDF"""
        # 保存配置
        if not self.save_config():
            return

        # 启动进度条
        self.progress.start()
        self.log("开始生成PDF...")

        # 在新线程中执行生成任务
        thread = threading.Thread(target=self._generate_pdf_thread)
        thread.daemon = True
        thread.start()

    def _generate_pdf_thread(self):
        """生成PDF的线程函数"""
        try:
            success = create_pdf_from_pages(
                self.config["pages_folder"],
                self.config["students_pdf"]
            )

            if success:
                self.log("PDF生成完成")
            else:
                self.log("PDF生成失败")

        except Exception as e:
            self.log(f"生成PDF时出错: {str(e)}")

        finally:
            # 停止进度条
            self.progress.stop()


def main():
    """主函数"""
    root = tk.Tk()
    app = CharacterCardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()