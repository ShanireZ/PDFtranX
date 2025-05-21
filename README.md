# PDFtranX
PDF翻译器，将PDF中内容通过OCR提取，并翻译为指定语言。
---
## 依赖库
```Python
pip install openai deepl pymupdf pillow pytesseract
```

## 参数
- input_pdf : 输入文件及路径
- output_txt : 输出文件及路径
- --src : 源语言，默认 auto
- --dest : 目标语言，默认 zh-cn
- --engine : 翻译引擎(deepl 或 deepseek)
- --model : Deepseek 模型,deepseek-chat 或 deepseek-reasoner
- --api-key : 使用 deepl 或 deepseek 时传入对应的 API Key
- --pages : 要翻译的页码范围，如 1-5，默认为空

## 注意事项
第 $24$ 行中，可修改OCR的识别语言，详情参考 https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
