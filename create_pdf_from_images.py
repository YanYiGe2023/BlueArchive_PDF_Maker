import os
import glob
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfdoc
import argparse


def get_image_files(folder_path, extensions=None):
    """
    获取文件夹中的所有图像文件
    """
    if extensions is None:
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff', '*.webp']

    image_files = []
    for ext in extensions:
        pattern = os.path.join(folder_path, '**', ext)  # 包含子目录
        image_files.extend(glob.glob(pattern, recursive=True))

        # 同时检查大写扩展名
        pattern_upper = os.path.join(folder_path, '**', ext.upper())
        image_files.extend(glob.glob(pattern_upper, recursive=True))

    return sorted(image_files)


def calculate_image_size(img_width, img_height, page_width, page_height, margin=50):
    """
    计算图像在PDF页面中的自适应大小和位置
    """
    # 计算可用的页面区域（考虑边距）
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin

    # 计算缩放比例
    width_ratio = available_width / img_width
    height_ratio = available_height / img_height

    # 选择较小的缩放比例以确保图像完全适应页面
    scale_ratio = min(width_ratio, height_ratio)

    # 计算缩放后的尺寸
    new_width = img_width * scale_ratio
    new_height = img_height * scale_ratio

    # 计算居中位置
    x = (page_width - new_width) / 2
    y = (page_height - new_height) / 2

    return x, y, new_width, new_height


def create_pdf_from_images(folder_path, output_pdf, page_size='A4', margin=50, include_subfolders=True):
    """
    从图像创建PDF文档
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在")
        return False

    # 获取图像文件
    if include_subfolders:
        image_files = get_image_files(folder_path)
    else:
        # 只在当前文件夹中查找
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff', '*.webp']
        image_files = []
        for ext in extensions:
            pattern = os.path.join(folder_path, ext)
            image_files.extend(glob.glob(pattern))

            pattern_upper = os.path.join(folder_path, ext.upper())
            image_files.extend(glob.glob(pattern_upper))
        image_files = sorted(image_files)

    if not image_files:
        print(f"在 '{folder_path}' 中未找到图像文件")
        return False

    print(f"找到 {len(image_files)} 个图像文件")

    # 设置页面尺寸
    if page_size.upper() == 'A4':
        page_width, page_height = A4
    elif page_size.upper() == 'LETTER':
        page_width, page_height = letter
    else:
        # 自定义尺寸，格式为 "宽度,高度"，单位是点（1 inch = 72 points）
        try:
            width_pt, height_pt = map(float, page_size.split(','))
            page_width, page_height = width_pt, height_pt
        except:
            print("使用默认的A4页面尺寸")
            page_width, page_height = A4

    # 创建PDF
    try:
        c = canvas.Canvas(output_pdf, pagesize=(page_width, page_height))

        for i, image_path in enumerate(image_files):
            try:
                print(f"处理图像 {i + 1}/{len(image_files)}: {os.path.basename(image_path)}")

                # 打开图像
                with Image.open(image_path) as img:
                    # 转换为RGB（如果必要）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 获取图像尺寸
                    img_width, img_height = img.size

                    # 计算自适应尺寸和位置
                    x, y, display_width, display_height = calculate_image_size(
                        img_width, img_height, page_width, page_height, margin
                    )

                    # 将图像保存为临时文件或使用ImageReader
                    # 这里我们使用ImageReader直接读取图像
                    img_reader = ImageReader(image_path)

                    # 在PDF上绘制图像
                    c.drawImage(img_reader, x, y, display_width, display_height)

                    # 添加新页面
                    if i < len(image_files) - 1:  # 最后一页后不添加空白页
                        c.showPage()

            except Exception as e:
                print(f"处理图像 '{image_path}' 时出错: {str(e)}")
                continue

        # 保存PDF
        c.save()
        print(f"PDF已成功生成: {output_pdf}")
        return True

    except Exception as e:
        print(f"生成PDF时出错: {str(e)}")
        return False


def main():
    """
    主函数，处理命令行参数
    """
    parser = argparse.ArgumentParser(description='将文件夹中的图像转换为PDF')
    parser.add_argument('folder', help='包含图像的文件夹路径')
    parser.add_argument('-o', '--output', default='output.pdf', help='输出PDF文件名 (默认: output.pdf)')
    parser.add_argument('-s', '--page-size', default='A4',
                        help='页面尺寸: A4, LETTER 或 自定义尺寸如 "595,842" (默认: A4)')
    parser.add_argument('-m', '--margin', type=int, default=50,
                        help='页面边距，单位: 点 (默认: 50)')
    parser.add_argument('--no-subfolders', action='store_true',
                        help='不包含子文件夹中的图像')

    args = parser.parse_args()

    # 如果未提供命令行参数，使用交互式输入
    if not args.folder:
        args.folder = input("请输入图像文件夹路径: ")
        args.output = input("请输入输出PDF文件名 (默认: output.pdf): ") or "output.pdf"
        args.page_size = input("请输入页面尺寸 (A4, LETTER 或 自定义尺寸) (默认: A4): ") or "A4"
        args.margin = int(input("请输入页面边距 (默认: 50): ") or "50")
        include_subfolders = input("是否包含子文件夹? (y/n, 默认: y): ").lower() != 'n'
    else:
        include_subfolders = not args.no_subfolders

    # 创建PDF
    success = create_pdf_from_images(
        folder_path=args.folder,
        output_pdf=args.output,
        page_size=args.page_size,
        margin=args.margin,
        include_subfolders=include_subfolders
    )

    if success:
        print("转换完成!")
    else:
        print("转换失败!")


if __name__ == "__main__":
    # 如果没有命令行参数，运行交互模式
    import sys

    if len(sys.argv) == 1:
        print("=== 图像转PDF工具 ===")
        folder = input("请输入图像文件夹路径: ")
        output = input("请输入输出PDF文件名 (默认: output.pdf): ") or "output.pdf"
        page_size = input("请输入页面尺寸 (A4, LETTER 或 自定义尺寸如 '595,842') (默认: A4): ") or "A4"
        margin = int(input("请输入页面边距 (默认: 50): ") or "50")
        include_subfolders = input("是否包含子文件夹? (y/n, 默认: y): ").lower() != 'n'

        success = create_pdf_from_images(
            folder_path=folder,
            output_pdf=output,
            page_size=page_size,
            margin=margin,
            include_subfolders=include_subfolders
        )

        if success:
            print("转换完成!")
        else:
            print("转换失败!")
    else:
        main()