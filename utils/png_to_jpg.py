import os
import sys
from PIL import Image

def png_to_jpg(input_dir=None, bg_color=(0, 0, 0), quality=100):
    """
    将指定目录下的所有PNG图片转换为JPG格式
    
    Args:
        input_dir: 输入目录，默认为当前目录
        bg_color: 背景颜色，默认为黑色(0, 0, 0)
        quality: JPG质量，默认为100
    """
    # 如果未指定输入目录，使用当前目录
    if input_dir is None:
        input_dir = os.getcwd()
    
    # 确保目录存在
    if not os.path.exists(input_dir):
        print(f"错误: 目录 '{input_dir}' 不存在")
        return False
    
    # 获取所有PNG文件
    png_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.png')]
    
    if not png_files:
        print(f"在目录 '{input_dir}' 中未找到PNG文件")
        return True
    
    print(f"找到 {len(png_files)} 个PNG文件")
    
    # 转换每个PNG文件
    successful = 0
    failed = 0
    
    for png_file in png_files:
        try:
            # 构建完整的文件路径
            png_path = os.path.join(input_dir, png_file)
            
            # 打开PNG图像
            img = Image.open(png_path)
            
            # 如果图像有alpha通道（透明通道），处理透明部分
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建新的RGB图像，背景为指定颜色
                rgb_img = Image.new('RGB', img.size, bg_color)
                
                # 如果是P模式（调色板），先转换为RGBA
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                # 将原图像粘贴到新背景上
                if img.mode == 'RGBA':
                    # RGBA图像需要分离alpha通道
                    rgb_img.paste(img, mask=img.split()[3])  # 使用alpha通道作为蒙版
                elif img.mode == 'LA':
                    # LA模式：L是亮度，A是alpha
                    rgb_img.paste(img.convert('RGBA'), mask=img.split()[1])
            else:
                # 如果没有alpha通道，直接转换为RGB
                rgb_img = img.convert('RGB')
            
            # 生成输出文件名（将.png替换为.jpg）
            jpg_file = os.path.splitext(png_file)[0] + '.jpg'
            jpg_path = os.path.join(input_dir, jpg_file)
            
            # 保存为JPG
            rgb_img.save(jpg_path, 'JPEG', quality=quality, optimize=True)
            
            print(f"✓ 转换成功: {png_file} -> {jpg_file}")
            successful += 1
            
        except Exception as e:
            print(f"✗ 转换失败 {png_file}: {str(e)}")
            failed += 1
    
    print(f"\n转换完成: 成功 {successful} 个, 失败 {failed} 个")
    return failed == 0

def main():
    """主函数，处理命令行参数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='将PNG图片转换为JPG格式，透明背景转为指定颜色',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                     # 转换当前目录所有PNG，黑色背景，质量100
  %(prog)s -d /path/to/images  # 转换指定目录
  %(prog)s -c white -q 90      # 白色背景，质量90
  %(prog)s -c 255,255,255      # 使用RGB值指定白色背景
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        default='.',
        help='输入目录，默认为当前目录'
    )
    
    parser.add_argument(
        '-c', '--color',
        default='black',
        help='背景颜色，支持颜色名或RGB值（如"white"、"255,255,255"），默认为black'
    )
    
    parser.add_argument(
        '-q', '--quality',
        type=int,
        default=100,
        choices=range(1, 101),
        metavar='[1-100]',
        help='JPG质量，1-100，默认为100'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='递归处理子目录（注意：本脚本当前版本不支持，已预留接口）'
    )
    
    args = parser.parse_args()
    
    # 解析颜色参数
    bg_color = (0, 0, 0)  # 默认黑色
    
    if args.color:
        color_str = args.color.lower().strip()
        
        # 预定义颜色
        color_map = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'transparent': None,
        }
        
        if color_str in color_map:
            bg_color = color_map[color_str]
        elif ',' in color_str:
            # 尝试解析RGB值
            try:
                rgb = [int(x.strip()) for x in color_str.split(',')]
                if len(rgb) == 3 and all(0 <= x <= 255 for x in rgb):
                    bg_color = tuple(rgb)
                else:
                    print(f"警告: 颜色值无效，使用默认黑色")
            except ValueError:
                print(f"警告: 颜色格式无效，使用默认黑色")
        else:
            print(f"警告: 颜色 '{args.color}' 不被识别，使用默认黑色")
    
    print(f"设置:")
    print(f"  目录: {args.directory}")
    print(f"  背景色: RGB{bg_color}")
    print(f"  质量: {args.quality}")
    print(f"  递归: {'是' if args.recursive else '否'}")
    print("-" * 40)
    
    # 执行转换
    try:
        success = png_to_jpg(args.directory, bg_color, args.quality)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 130
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
