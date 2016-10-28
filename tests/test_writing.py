

class TestWriting(object):
    def test_writing_pdf(self):
        from signedpdf.pdfparser import PDF
        from StringIO import StringIO

        s = StringIO()

        p = PDF()
        p.write(s)

        print(s)
        import sys
        d = s.getvalue()
        sys.stderr.write(d)

        # assert must fail in order for pytest to print output :)
        assert len(d) == 0