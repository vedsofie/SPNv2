from HTMLParser import HTMLParser
import bleach
VALID_TAGS = ['sub', 'em', 'sup', 'span']
styles = ['font-size']
attrs = {'*': ['style']}

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def sanitize_html(value, valid_tags=None):
    valid_tags = VALID_TAGS if valid_tags is None else valid_tags

    if value is None:
        return ""
    return bleach.clean(value,
                        attributes=attrs,
                        tags=valid_tags,
                        styles=styles,
                        strip=True)

if __name__ == "__main__":
    import pdb
    pdb.set_trace()
