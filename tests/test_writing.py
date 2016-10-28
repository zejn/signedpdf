

class TestWriting(object):
    def test_writing_pdf(self):
        from signedpdf.pdfparser import PDF
        from StringIO import StringIO

        s = StringIO()

        p = PDF()
        p.write(s)

        print(s)