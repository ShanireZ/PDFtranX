import sys
import argparse
from PyPDF2 import PdfReader


# OCR 依赖：pymupdf, pillow, pytesseract
def ocr_page(pdf_path, pageno):
    try:
        import fitz
        from PIL import Image
        import pytesseract

        # 如果 tesseract.exe 不在 PATH，手动指定：
        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
    except ImportError:
        print("未安装 OCR 依赖，请运行: pip install pymupdf pillow pytesseract")
        sys.exit(1)
    doc = fitz.open(pdf_path)
    page = doc.load_page(pageno)
    pix = page.get_pixmap(dpi=200)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pytesseract.image_to_string(img, lang="jpn")  # 如英文用 'eng'


def translate_pdf(
    input_pdf,
    output_txt,
    src="auto",
    dest="zh-cn",
    engine="google",
    api_key=None,
    pages=None,
    ds_model="deepseek-chat",
):
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    # 解析页码范围参数（如 "1-5"）
    if pages:
        try:
            start_str, end_str = pages.split("-", 1)
            start = max(int(start_str) - 1, 0)
            end = min(int(end_str) - 1, total_pages - 1)
            page_indices = list(range(start, end + 1))
        except Exception:
            print("无效的页码范围，请使用 --pages start-end 格式")
            sys.exit(1)
    else:
        page_indices = list(range(total_pages))
    total = len(page_indices)

    with open(output_txt, "w", encoding="utf-8") as f:
        for count, page_no in enumerate(page_indices, start=1):
            page = reader.pages[page_no]
            text = page.extract_text() or ""
            # 如果提取不到文本，就做 OCR
            if not text.strip():
                text = ocr_page(input_pdf, page_no)
            if not text.strip():
                # 依然没有内容则跳过
                continue

            if engine == "deepl":
                try:
                    import deepl
                except ModuleNotFoundError:
                    print("未安装 deepl 库，请运行: pip install deepl")
                    sys.exit(1)
                translator = deepl.Translator(api_key)
                tr_text = translator.translate_text(text, target_lang=dest.upper()).text

            elif engine == "deepseek":
                # 使用 OpenAI SDK 调用 Deepseek 接口
                try:
                    from openai import OpenAI
                except ModuleNotFoundError:
                    print("未安装 OpenAI SDK，请运行: pip install openai")
                    sys.exit(1)
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
                # 构造翻译提示词：指明源语言和目标语言
                system_prompt = "You are a helpful assistant for translation."
                user_prompt = (
                    f"Please translate the following text from {src} to {dest}:\n{text}"
                )
                resp = client.chat.completions.create(
                    model=ds_model,  # ds_model 可选 'deepseek-chat' 或 'deepseek-reasoner'
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    stream=False,
                )
                tr_text = resp.choices[0].message.content.strip()

            else:
                raise ValueError(f"Unknown engine: {engine}")

            f.write(tr_text + "\n")
            # 实时打印进度
            percent = count / total * 100
            print(
                f"\r翻译进度: {count}/{total} 页 ({percent:.1f}%)", end="", flush=True
            )
        print()  # 完成后换行


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PDF 翻译脚本，支持 googletrans、DeepL、Deepseek"
    )
    parser.add_argument("input_pdf", help="输入 PDF 文件路径")
    parser.add_argument("output_txt", help="输出文本文件路径")
    parser.add_argument("--src", default="auto", help="源语言，默认 auto")
    parser.add_argument("--dest", default="zh-cn", help="目标语言，默认 zh-cn")
    parser.add_argument(
        "--engine",
        choices=["deepl", "deepseek"],
        default="deepl",
        help="翻译引擎(deepl|deepseek)",
    )
    parser.add_argument("--pages", help="要翻译的页码范围，如 1-5", default=None)
    parser.add_argument("--api-key", help="使用 deepl 或 deepseek 时传入对应的 API Key")
    parser.add_argument(
        "--model",
        choices=["deepseek-chat", "deepseek-reasoner"],
        default="deepseek-chat",
        help="Deepseek 模型,deepseek-chat 或 deepseek-reasoner",
    )
    args = parser.parse_args()

    if args.engine in ["deepl", "deepseek"] and not args.api_key:
        print("使用 deepl 或 deepseek 时需要提供 --api-key")
        sys.exit(1)

    translate_pdf(
        args.input_pdf,
        args.output_txt,
        src=args.src,
        dest=args.dest,
        engine=args.engine,
        api_key=args.api_key,
        pages=args.pages,
        ds_model=args.model,
    )
