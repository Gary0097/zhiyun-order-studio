# -*- coding: utf-8 -*-

import base64
import io
import unittest
import zipfile

from backend.document_parser import extract_document_text


class DocumentParserTests(unittest.TestCase):
    def test_txt_file(self) -> None:
        result = extract_document_text("合同.txt", base64.b64encode("甲方：智造云".encode()).decode())
        self.assertEqual(result["text"], "甲方：智造云")

    def test_docx_file_without_extra_dependency(self) -> None:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("word/document.xml", '<w:document><w:body><w:p><w:r><w:t>合同金额：100元</w:t></w:r></w:p></w:body></w:document>')
        result = extract_document_text("合同.docx", base64.b64encode(stream.getvalue()).decode())
        self.assertIn("合同金额：100元", result["text"])

    def test_unsupported_file(self) -> None:
        with self.assertRaises(ValueError):
            extract_document_text("合同.exe", base64.b64encode(b"abc").decode())


if __name__ == "__main__":
    unittest.main()
