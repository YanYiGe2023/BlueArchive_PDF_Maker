from PIL import Image, ImageDraw, ImageFont
import os
import time

# 硬编码配置
CONFIG = {
    'font_path': '/Users/yanyige/Library/Fonts/Aa复古小猫画报集.ttf',  # 替换为您的字体路径
    'output_dir': 'text_output',
    'font_size': 120,
    'text_color': (0, 0, 0),  # 黑色
    'bg_color': (255, 255, 255, 0),  # 透明背景
    'padding': 50
}


def create_text_image(text, output_path):
    """
    使用硬编码配置渲染文字并保存为图片
    """
    try:
        # 加载字体
        font = ImageFont.truetype(CONFIG['font_path'], CONFIG['font_size'])

        # 创建临时绘图对象来计算文字尺寸
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # 计算文字边界框
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算图片尺寸
        img_width = text_width + CONFIG['padding'] * 2
        img_height = text_height + CONFIG['padding'] * 2

        # 创建图片
        img = Image.new('RGBA', (img_width, img_height), CONFIG['bg_color'])
        draw = ImageDraw.Draw(img)

        # 计算文字位置（居中）
        x = (img_width - text_width) / 2
        y = (img_height - text_height) / 2

        # 绘制文字
        draw.text((x, y), text, font=font, fill=CONFIG['text_color'])

        # 保存图片
        img.save(output_path, 'PNG')
        print(f"文字图片已保存: {output_path}")

        return True

    except Exception as e:
        print(f"创建文字图片失败: {str(e)}")
        return False


def main():
    """主函数 - 持续运行模式"""
    # 确保输出目录存在
    os.makedirs(CONFIG['output_dir'], exist_ok=True)

    print("=== 文字渲染工具 (持续运行模式) ===")
    print(f"字体: {CONFIG['font_path']}")
    print(f"字体大小: {CONFIG['font_size']}")
    print(f"输出目录: {CONFIG['output_dir']}")
    print("输入 '退出' 或 'exit' 结束程序")
    print("-" * 50)

    counter = 1

    while True:
        # 获取用户输入
        text = input("请输入要渲染的文字: ").strip()

        # 检查退出条件
        if text.lower() in ['退出', 'exit', 'quit', 'q']:
            print("程序结束")
            break

        if not text:
            print("文字不能为空，请重新输入")
            continue

        # 生成输出文件名
        timestamp = int(time.time())
        filename = f"text_{counter:03d}_{timestamp}.png"
        output_path = os.path.join(CONFIG['output_dir'], filename)

        # 创建文字图片
        success = create_text_image(text, output_path)

        if success:
            print(f"已生成第 {counter} 张图片")
            counter += 1
        else:
            print("生成失败，请重试")


if __name__ == "__main__":
    # 安装依赖提示
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("请安装Pillow库: pip install pillow")
        exit(1)

    # 检查字体文件是否存在
    if not os.path.exists(CONFIG['font_path']):
        print(f"错误: 字体文件不存在 - {CONFIG['font_path']}")
        print("请修改 CONFIG 中的 font_path 为正确的字体文件路径")
        exit(1)

    main()