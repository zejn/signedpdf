

class TestWriting(object):
    def test_writing_pdf(self):
        from signedpdf.pdfparser import PDF, Page
        from StringIO import StringIO

        s = StringIO()

        p = PDF()
        p1 = Page()
        p.pages.add_page(p1)

        p.write(s)

        print(s)
        import sys
        d = s.getvalue()
        sys.stderr.write(d)

        with open('testpdf.pdf', 'wb') as out:
            out.write(s.getvalue())

        # assert must fail in order for pytest to print output :)
        assert len(d) == 0