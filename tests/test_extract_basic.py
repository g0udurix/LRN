import os
from lrn.extract import find_inner_xhtml

def test_find_inner_xhtml_extracts_div():
    sample = '''<html><body><div id="content"><!-- noise --></div>
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<div xmlns="http://www.w3.org/1999/xhtml">hello</div>'''
    frag = find_inner_xhtml(sample)
    assert frag.strip().startswith(("<?xml", "<!DOCTYPE"))
    assert ">hello</div>" in frag
