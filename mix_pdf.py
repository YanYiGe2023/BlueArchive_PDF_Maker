import os
import glob
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def create_pdf_from_pages(config_file="config.json"):
    """将pages文件夹中的PNG页面合并为PDF"""
    # 加载配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {}

    pages_folder = config.get("output_dir", "pages")
    output_pdf = "final_schools_cards.pdf"

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

            # 在PDF上绘制图像
            c.drawImage(png_path, 0, 0, width=A4[0], height=A4[1])

            # 如果不是最后一页，添加新页面
            if i < len(png_files) - 1:
                c.showPage()

        # 保存PDF
        c.save()
        print(f"PDF已成功生成: {output_pdf}")
        return True

    except Exception as e:
        print(f"生成PDF时出错: {str(e)}")
        return False


def main():
    success = create_pdf_from_pages("config.json")

    if success:
        print("PDF合并完成!")
    else:
        print("PDF合并失败!")


if __name__ == "__main__":
    main()