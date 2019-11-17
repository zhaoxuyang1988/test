#-*- coding:utf-8 -*-


import pdfplumber

f_pdf = "/Users/zhaoxuyang/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/2.0b4.0.9/f4ebfddae17bab807e6cfc88fcc1aa87/Message/MessageTemp/9e20f478899dc29eb19741386f9343c8/File/小说/小说/秘密英文版.pdf"

def get_pdf_text(f_pdf):
    pdf_text = []
    with pdfplumber.open(f_pdf) as fp:

        for page in fp.pages:
            text = page.extract_text()
            if text:
                text = text.replace("   ", " ")
                text = text.replace("  ", " ")
                pdf_text.append(text)
    return "".join(pdf_text)


if __name__ == "__main__":
    text = get_pdf_text(f_pdf)
    print(text)
