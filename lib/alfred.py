from lxml import etree


class ScriptFilterList(object):
    def __init__(self):
        self.items = etree.Element('items')

    def __str__(self):
        return etree.tostring(self.items, xml_declaration=True,
                              encoding='utf-8').decode('utf-8')

    def add_item(self, item):
        if type(item) is etree.Element:
            self.items.append(item)
        elif type(item) is ScriptFilterListItem:
            self.items.append(item.xml_element())
        else:
            raise TypeError()

    def xml_element(self):
        return self.items


class ScriptFilterListItem(object):
    def __init__(self, uid=None, arg=None, valid=True, autocomplete=None,
                 item_type=None):
        self.root = etree.Element('item')

        if uid:
            self.root.attrib['uid'] = str(uid)
        if arg:
            self.root.attrib['arg'] = str(arg)
        self.root.attrib['valid'] = 'yes' if valid else 'no'
        if autocomplete:
            self.root.attrib['autocomplete'] = str(autocomplete)
        if item_type and item_type in ['default', 'file', 'file:skipcheck']:
            self.root.attrib['type'] = str(item_type)

    def __str__(self):
        return str(etree.tostring(self.root)).decode('utf-8')

    def add_title(self, title):
        title_elem = etree.Element('title')
        title_elem.text = title
        self.root.append(title_elem)

    def add_subtitle(self, subtitle, mod=None):
        st_elem = etree.Element('subtitle')
        st_elem.text = subtitle
        if mod and mod in ['shift', 'fn', 'ctrl', 'alt', 'cmd']:
            st_elem.attrib['mod'] = str(mod)
        self.root.append(st_elem)

    def add_icon(self, icon, icon_type=None):
        icon_elem = etree.Element('icon')
        icon_elem.text = icon
        if icon_type and icon_type in ['fileicon', 'filetype']:
            icon_elem.attrib['type'] = icon_type
        self.root.append(icon_elem)

    def add_arg(self, arg):
        arg_elem = etree.Element('arg')
        arg_elem.text = arg
        self.root.append(arg_elem)

    def add_text(self, text, txt_type=None):
        txt_elem = etree.Element('text')
        txt_elem.text = text
        if txt_type and txt_type in ['copy', 'largetype']:
            txt_elem.attrib['type'] = text_type
        self.root.append(txt_elem)

    def xml_element(self):
        return self.root
