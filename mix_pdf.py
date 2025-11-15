import os
import glob
import json
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def create_pdf_from_pages(pages_folder=None, output_pdf=None, config_file="config.json"):
    """将pages文件夹中的PNG页面合并为PDF"""
    # 加载配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {}

    # 从配置中获取参数
    if pages_folder is None:
        pages_folder = config.get("pages_folder", "pages")
    if output_pdf is None:
        output_pdf = config.get("students_pdf", "students.pdf")

    add_contrast = config.get("add_contrast", False)
    contrast_factor = config.get("contrast_factor", 1.2)

    # 获取所有PNG文件并按数字顺序排序
    png_files = sorted(glob.glob(os.path.join(pages_folder, "*.png")))

    if not png_files:
        print("在pages文件夹中未找到PNG文件")
        return False

    try:
        # 创建PDF
        c = canvas.Canvas(output_pdf, pagesize=A4)

        for i, png_path in enumerate(png_files):
            print(f"添加页面 {i + 1}/{len(png_files)}: {os.path.basename(png_path)}")

            # 如果需要增强对比度
            if add_contrast:
                # 打开图像并增强对比度
                img = Image.open(png_path)
                enhancer = ImageEnhance.Contrast(img)
                img_enhanced = enhancer.enhance(contrast_factor)

                # 保存增强后的临时图像
                temp_path = f"{png_path}_temp.png"
                img_enhanced.save(temp_path, 'PNG')

                # 使用增强后的图像
                c.drawImage(temp_path, 0, 0, width=A4[0], height=A4[1])

                # 删除临时文件
                os.remove(temp_path)
            else:
                # 直接使用原始图像
                c.drawImage(png_path, 0, 0, width=A4[0], height=A4[1])

            # 如果不是最后一页，添加新页面
            if i < len(png_files) - 1:
                c.showPage()

        # 保存PDF
        c.save()
        print(f"PDF已成功生成: {output_pdf}")
        if add_contrast:
            print(f"已应用对比度增强，增强因子: {contrast_factor}")
        return True

    except Exception as e:
        print(f"生成PDF时出错: {str(e)}")
        return False


def main():
    success = create_pdf_from_pages(config_file="config.json")

    if success:
        print("PDF合并完成!")
    else:
        print("PDF合并失败!")


if __name__ == "__main__":
    main()