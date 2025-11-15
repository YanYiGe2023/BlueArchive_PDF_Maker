import json

import os
import re
import requests
from PIL import Image, ImageDraw, ImageFont


class CharacterCardGenerator:
    def __init__(self, config_file="config.json"):
        # 加载配置文件
        self.config = self.load_config(config_file)

        # API格式列表
        self.avatar_url_patterns = [
            "https://static.kivo.wiki/images/students/{}/avatar.png",
            "https://static.kivo.wiki/images/students/{}/original/avatar.png"
        ]

        self.sd_model_url_patterns = [
            "https://static.kivo.wiki/images/students/{}/sd_model.png",
            "https://static.kivo.wiki/images/students/{}/original/sd_model.png"
        ]

        # 从配置中获取字体路径
        self.font_path = self.config.get("font_path")
        self.output_path = self.config.get("cards_folder")

        # 如果没有配置字体路径，尝试查找系统字体
        if not self.font_path:
            possible_fonts = [
                "C:/Windows/Fonts/simhei.ttf",
                "/System/Library/Fonts/PingFang.ttc",
            ]
            for font in possible_fonts:
                if os.path.exists(font):
                    self.font_path = font
                    break

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

    def safe_filename(self, name):
        """生成安全的文件名，删除空格"""
        # 删除空格和其他不安全字符
        safe_name = re.sub(r'[\\/*?:"<>|\s]', "", name)
        return safe_name

    def format_display_name(self, character_name):
        """格式化显示名称，将特殊形态转换为 {角色名}({形态}) 格式"""
        if '/' in character_name:
            base_name, form_name = character_name.split('/', 1)
            return f"{base_name}({form_name})"
        else:
            return character_name

    def download_image_with_fallback(self, url_patterns, save_path, image_type, character_name):
        """尝试多种URL格式下载图像"""
        for pattern in url_patterns:
            url = pattern.format(character_name)
            try:
                response = requests.get(url, stream=True, timeout=30)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"成功下载{image_type}: {url}")
                    return True
            except Exception as e:
                print(f"尝试下载{image_type}失败: {url}, 错误: {str(e)}")
                continue

        # 如果所有URL都失败，询问用户
        print(f"所有{image_type}URL尝试失败")
        manual_url = input(f"是否手动指定{character_name}的{image_type}URL? (y/n): ").strip().lower()
        if manual_url == 'y':
            custom_url = input(f"请输入{character_name}的{image_type}URL: ").strip()
            if custom_url:
                try:
                    response = requests.get(custom_url, stream=True, timeout=30)
                    response.raise_for_status()
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"使用手动URL成功下载{image_type}")
                    return True
                except Exception as e2:
                    print(f"使用手动URL下载{image_type}失败: {str(e2)}")

        # 询问是否使用本地文件
        use_local = input(f"是否使用本地文件作为{character_name}的{image_type}? (y/n): ").strip().lower()
        if use_local == 'y':
            local_path = input(f"请输入本地{image_type}文件路径: ").strip()
            if local_path and os.path.exists(local_path):
                try:
                    if image_type == "头像":
                        target_size = (404, 456)
                    else:
                        target_size = (452, 452)

                    processed_img = self.process_local_image(local_path, target_size, image_type)
                    if processed_img:
                        processed_img.save(save_path, quality=95)
                        print(f"使用本地文件成功: {local_path}")
                        return True
                except Exception as e2:
                    print(f"处理本地文件失败: {str(e2)}")

        return False

    def process_local_image(self, image_path, target_size, image_type):
        """处理本地图像，缩放和裁剪到目标尺寸"""
        try:
            img = Image.open(image_path)
            target_width, target_height = target_size
            img_width, img_height = img.size

            scale_ratio = max(target_width / img_width, target_height / img_height)
            new_width = int(img_width * scale_ratio)
            new_height = int(img_height * scale_ratio)

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height

            img_cropped = img_resized.crop((left, top, right, bottom))

            print(f"成功处理{image_type}图像: {os.path.basename(image_path)} -> {target_size[0]}x{target_size[1]}")
            return img_cropped

        except Exception as e:
            print(f"处理本地图像失败: {str(e)}")
            return None

    def get_special_form_urls(self, character_name):
        """检查角色是否有特殊形态"""
        if '/' in character_name:
            base_name, form_name = character_name.split('/', 1)
            base_name_encoded = requests.utils.quote(base_name)
            form_name_encoded = requests.utils.quote(form_name)

            avatar_url = f"https://static.kivo.wiki/images/students/{base_name_encoded}/{form_name_encoded}/avatar.png"
            sd_model_url = f"https://static.kivo.wiki/images/students/{base_name_encoded}/{form_name_encoded}/sd_model.png"
            return avatar_url, sd_model_url, True
        else:
            character_name_encoded = requests.utils.quote(character_name)
            avatar_url = self.avatar_url_patterns[0].format(character_name_encoded)
            sd_model_url = self.sd_model_url_patterns[0].format(character_name_encoded)
            return avatar_url, sd_model_url, False

    def create_character_card(self, character_name):
        """创建角色信息卡"""
        # 删除角色名中的空格
        safe_character_name = self.safe_filename(character_name)
        display_name = self.format_display_name(character_name)

        print(f"开始为角色 '{display_name}' 创建信息卡...")

        # 创建临时文件夹
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        # 获取正确的URL（处理特殊形态）
        avatar_url, sd_model_url, is_special_form = self.get_special_form_urls(character_name)

        if is_special_form:
            print(f"检测到特殊形态角色，使用特殊URL格式")

        avatar_path = os.path.join(temp_dir, f"{safe_character_name}_avatar.png")
        sd_model_path = os.path.join(temp_dir, f"{safe_character_name}_sd_model.png")

        # 下载图像，使用回退机制
        avatar_available = False
        sd_model_available = False

        # 如果是特殊形态，直接使用特殊URL
        if is_special_form:
            avatar_available = self.download_image_with_fallback([avatar_url], avatar_path, "头像", character_name)
            sd_model_available = self.download_image_with_fallback([sd_model_url], sd_model_path, "SD模型",
                                                                   character_name)
        else:
            # 普通形态，尝试多种URL格式
            avatar_available = self.download_image_with_fallback(self.avatar_url_patterns, avatar_path, "头像",
                                                                 character_name)
            sd_model_available = self.download_image_with_fallback(self.sd_model_url_patterns, sd_model_path, "SD模型",
                                                                   character_name)

        # 如果两个图像都下载失败，则返回失败
        if not avatar_available and not sd_model_available:
            print(f"角色 '{display_name}' 的头像和SD模型都无法下载，跳过此角色")
            return False

        try:
            # 处理图像
            avatar_img = None
            sd_model_img = None

            avatar_placeholder_size = (404, 456)
            sd_model_placeholder_size = (452, 452)

            # 处理头像图像
            if avatar_available:
                avatar_img = Image.open(avatar_path)
                if avatar_img.mode in ('RGBA', 'LA') or (avatar_img.mode == 'P' and 'transparency' in avatar_img.info):
                    background = Image.new('RGB', avatar_img.size, (255, 255, 255))
                    if avatar_img.mode in ('RGBA', 'LA'):
                        background.paste(avatar_img, mask=avatar_img.split()[-1])
                    else:
                        background.paste(avatar_img)
                    avatar_img = background
            else:
                avatar_img = Image.new('RGB', avatar_placeholder_size, (240, 240, 240))
                draw_placeholder = ImageDraw.Draw(avatar_img)
                try:
                    font = ImageFont.truetype(self.font_path, 24) if self.font_path else ImageFont.load_default()
                    text = "头像不可用"
                    bbox = draw_placeholder.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (avatar_placeholder_size[0] - text_width) // 2
                    y = (avatar_placeholder_size[1] - text_height) // 2
                    draw_placeholder.text((x, y), text, font=font, fill=(150, 150, 150))
                except:
                    pass

            # 处理SD模型图像
            if sd_model_available:
                sd_model_img = Image.open(sd_model_path)
                if sd_model_img.mode in ('RGBA', 'LA') or (
                        sd_model_img.mode == 'P' and 'transparency' in sd_model_img.info):
                    background = Image.new('RGB', sd_model_img.size, (255, 255, 255))
                    if sd_model_img.mode in ('RGBA', 'LA'):
                        background.paste(sd_model_img, mask=sd_model_img.split()[-1])
                    else:
                        background.paste(sd_model_img)
                    sd_model_img = background
            else:
                sd_model_img = Image.new('RGB', sd_model_placeholder_size, (240, 240, 240))
                draw_placeholder = ImageDraw.Draw(sd_model_img)
                try:
                    font = ImageFont.truetype(self.font_path, 24) if self.font_path else ImageFont.load_default()
                    text = "SD模型不可用"
                    bbox = draw_placeholder.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (sd_model_placeholder_size[0] - text_width) // 2
                    y = (sd_model_placeholder_size[1] - text_height) // 2
                    draw_placeholder.text((x, y), text, font=font, fill=(150, 150, 150))
                except:
                    pass

            # 计算合成图像的尺寸
            card_width = 50 + avatar_img.width + 50 + sd_model_img.width + 50
            card_height = 150 + max(avatar_img.height, sd_model_img.height) + 50

            # 创建新图像
            card = Image.new('RGB', (card_width, card_height), 'white')
            draw = ImageDraw.Draw(card)

            # 添加角色名称
            self.add_character_name(draw, display_name, 50, 43)

            # 计算图像位置
            avatar_x = 50
            avatar_y = card_height - 50 - avatar_img.height

            sd_model_x = 50 + avatar_img.width + 50
            sd_model_y = card_height - 50 - sd_model_img.height

            # 粘贴图像
            card.paste(avatar_img, (avatar_x, avatar_y))
            card.paste(sd_model_img, (sd_model_x, sd_model_y))

            # 添加边框和装饰
            self.add_decorations(draw, card_width, card_height)

            # 保存结果
            output_path = self.config.get("cards_folder")
            print(f"输出路径: {output_path}")
            os.makedirs(output_path, exist_ok=True)
            output_path = os.path.join(output_path, f"{safe_character_name}_card.png")

            card.save(output_path, quality=95)
            print(f"角色信息卡已保存: {output_path}")

            # 清理临时文件
            try:
                if os.path.exists(avatar_path):
                    os.remove(avatar_path)
                if os.path.exists(sd_model_path):
                    os.remove(sd_model_path)
            except:
                pass

            return True

        except Exception as e:
            print(f"创建角色信息卡时出错: {str(e)}")
            return False

    def add_character_name(self, draw, name, x, y):
        """添加角色名称到图像左上方"""
        try:
            font_size = 60
            if self.font_path:
                try:
                    font = ImageFont.truetype(self.font_path, font_size)
                except:
                    font = ImageFont.load_default()
            else:
                font = ImageFont.load_default()

            text_color = (0, 0, 0)
            draw.text((x, y), name, font=font, fill=text_color)

        except Exception as e:
            print(f"添加文字时出错: {str(e)}")

    def add_decorations(self, draw, width, height):
        """添加装饰元素"""
        border_color = (200, 200, 200)
        draw.rectangle([10, 10, width - 10, height - 10], outline=border_color, width=3)

        line_color = (150, 150, 150)
        draw.line([10, 120, width - 10, 120], fill=line_color, width=2)

    def batch_create_cards(self, character_names, output_dir="character_cards"):
        """批量创建多个角色的信息卡"""
        os.makedirs(output_dir, exist_ok=True)

        success_count = 0
        for name in character_names:
            safe_name = self.safe_filename(name)
            output_path = os.path.join(output_dir, f"{safe_name}_card.png")
            if self.create_character_card(name):
                success_count += 1

        print(f"\n批量创建完成: {success_count}/{len(character_names)} 个角色信息卡创建成功")
        return success_count

def main():
    """主函数"""
    generator = CharacterCardGenerator()

    print("=== 角色信息卡生成器 ===")
    print("1. 单个角色")
    print("2. 批量创建")

    choice = input("请选择模式 (1 或 2): ").strip()

    if choice == "1":
        character_name = input("请输入角色名称: ").strip()
        if character_name:
            generator.create_character_card(character_name)
        else:
            print("角色名称不能为空")

    elif choice == "2":
        names_input = input("请输入角色名称，用逗号分隔: ").strip()
        if names_input:
            character_names = [name.strip() for name in names_input.split(",")]
            generator.batch_create_cards(character_names)
        else:
            print("请输入有效的角色名称")
    else:
        print("无效选择")

if __name__ == "__main__":
    main()