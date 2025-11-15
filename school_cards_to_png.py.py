import glob
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont


class SchoolCardsToPNG:
    def __init__(self, config_file="config.json"):
        # 加载配置文件
        self.config = self.load_config(config_file)

        # 从配置中读取参数
        dpi = self.config.get("dpi", 300)
        margin = self.config.get("margin", 80)
        font_path = self.config.get("font_path")

        # A4尺寸 (8.27x11.69英寸) 乘以DPI得到像素尺寸
        self.width = int(8.27 * dpi)  # 2481像素
        self.height = int(11.69 * dpi)  # 3507像素
        self.margin = margin
        self.dpi = dpi

        # 预加载字体
        self.title_font = None
        if font_path and os.path.exists(font_path):
            try:
                self.title_font = ImageFont.truetype(font_path, 60)
            except:
                print(f"无法加载字体: {font_path}")

    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 不存在，使用默认配置")
            return {}
        except Exception as e:
            print(f"读取配置文件失败: {str(e)}，使用默认配置")
            return {}

    def get_school_folders(self, root_folder):
        return sorted([item for item in os.listdir(root_folder)
            if os.path.isdir(os.path.join(root_folder, item))])

    def get_card_files(self, folder_path):
        extensions = ['*.png', '*.jpg', '*.jpeg']
        card_files = []
        for ext in extensions:
            pattern = os.path.join(folder_path, ext)
            files = [f for f in glob.glob(pattern) if not f.endswith('icon.png')]
            card_files.extend(files)

        # 按数字顺序排序
        def extract_number(filename):
            base = os.path.basename(filename)
            name, _ = os.path.splitext(base)
            numbers = ''.join(filter(str.isdigit, name))
            return int(numbers) if numbers else 0

        return sorted(card_files, key=extract_number)

    def create_pages_by_schools(self):
        """从配置中读取参数创建页面"""
        # 从配置中读取参数
        root_folder = self.config.get("cards_folder")
        output_dir = self.config.get("pages_folder")
        cards_per_row = self.config.get("cards_per_row", 4)
        school_order = self.config.get("school_order", [])

        # 获取所有学院文件夹并按指定顺序排序
        all_schools = self.get_school_folders(root_folder)

        # 按指定顺序排序，不在顺序列表中的学院放在最后
        school_folders = []
        for school in school_order:
            if school in all_schools:
                school_folders.append(school)
                all_schools.remove(school)

        # 添加未在顺序列表中指定的学院
        school_folders.extend(sorted(all_schools))

        if not school_folders:
            return False

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        page_count = 0

        try:
            for school_index, school_name in enumerate(school_folders):
                print(f"处理学院: {school_name}")
                school_path = os.path.join(root_folder, school_name)
                card_files = self.get_card_files(school_path)
                icon_path = os.path.join(school_path, "icon.png")

                if not card_files:
                    print(f"  - 没有找到角色卡，跳过")
                    continue

                print(f"  - 找到 {len(card_files)} 张角色卡，每行 {cards_per_row} 张")

                # 计算卡片尺寸
                available_width = self.width - 2 * self.margin
                card_width = available_width // cards_per_row - 20  # 减去间距

                # 获取第一张卡片的尺寸比例
                with Image.open(card_files[0]) as img:
                    aspect_ratio = img.height / img.width
                    card_height = int(card_width * aspect_ratio)

                # 计算每页可以显示的行数
                available_height = self.height - 2 * self.margin - 180  # 为标题预留更多空间
                vertical_spacing = 20
                cards_per_column = available_height // (card_height + vertical_spacing)

                total_pages = math.ceil(len(card_files) / (cards_per_row * cards_per_column))
                print(
                    f"  - 每页 {cards_per_row} x {cards_per_column} = {cards_per_row * cards_per_column} 张卡片，共 {total_pages} 页")

                for page_num in range(total_pages):
                    # 创建空白A4页面
                    page = Image.new('RGB', (self.width, self.height), 'white')
                    draw = ImageDraw.Draw(page)

                    # 只在学院第一页添加图标和名称
                    if page_num == 0:
                        # 添加学院图标 - 增大尺寸
                        if os.path.exists(icon_path):
                            icon = Image.open(icon_path)
                            icon_width, icon_height = 240, 180  # 增大图标尺寸
                            icon = icon.resize((icon_width, icon_height), Image.Resampling.LANCZOS)
                            page.paste(icon, (self.margin, self.margin))

                        # 添加学院名称
                        if self.title_font:
                            draw.text((self.margin + 250, self.margin + 60), school_name, font=self.title_font,
                                      fill=(0, 0, 0))
                        else:
                            # 如果没有字体，使用默认字体
                            try:
                                font = ImageFont.truetype("Arial", 60)
                                draw.text((self.margin + 250, self.margin + 60), school_name, font=font, fill=(0, 0, 0))
                            except:
                                draw.text((self.margin + 250, self.margin + 60), school_name, fill=(0, 0, 0))

                    # 绘制当前页的卡片
                    start_index = page_num * cards_per_row * cards_per_column
                    end_index = min(start_index + cards_per_row * cards_per_column, len(card_files))

                    for i in range(start_index, end_index):
                        card_path = card_files[i]
                        position_in_page = i - start_index

                        row = position_in_page // cards_per_row
                        col = position_in_page % cards_per_row

                        x = self.margin + col * (card_width + 20)
                        y = self.margin + 180 + row * (card_height + vertical_spacing)  # 调整起始位置

                        # 加载并调整卡片大小
                        card_img = Image.open(card_path)
                        card_img = card_img.resize((card_width, card_height), Image.Resampling.LANCZOS)

                        # 粘贴卡片到页面
                        page.paste(card_img, (x, y))

                    # 保存页面
                    page_count += 1
                    png_path = f"{output_dir}/{page_count:03d}.png"
                    page.save(png_path, 'PNG', dpi=(self.dpi, self.dpi))

                    print(f"  - 生成第 {page_num + 1}/{total_pages} 页: {png_path}")

                print(f"  - 完成")

            print(f"所有页面已保存到 {output_dir} 文件夹，共 {page_count} 页")
            return True

        except Exception as e:
            print(f"Error: {str(e)}")
            return False




def main():
    # 从配置文件创建生成器
    merger = SchoolCardsToPNG("config.json")
    success = merger.create_pages_by_schools()

    if success:
        print("PNG页面生成成功")
    else:
        print("PNG页面生成失败")

if __name__ == '__main__':
    main()