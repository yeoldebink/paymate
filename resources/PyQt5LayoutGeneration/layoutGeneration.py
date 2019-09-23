import sys

from PyQt5 import QtWidgets as gui, QtCore as core

####

# This module is a powerful tool for the automatic generation of box and gridlayouts
# The creation of a layout using these classes should be done roughly as follows:
#
# my_layout = <AutoLayout subclass>(<list of dicts, str, and NoneType>)
#
# For instance:
# my_layout = AutoHBoxLayout('hello, ', dict(WIDGET=gui.QPushButton('world!'), name='button',
# init=lambda d: d.setFixedWidth(300)), None)
#
# will create a horizontal box layout with a label saying 'hello, ' and a button with the text 'world!'
# special attributes to specify as keys in the dict are as follows:
#
# Attributes in ALL CAPS: this is the item itself -- the widget or layout to be added to the layout.
#       See the types below
# name: this key will determine the attribute name the object will be assigned at layout creation. For instance:
#       lo = AutoVBoxLayout(dict(WIDGET=gui.QPushButton("Hi there"), name='button'))
#       In this case lo is a VBoxLayout with a button that says "Hi there". This button may be accessed via lo.button
# init: this is a lambda expression receiving one argument which will be called using the object as its argument
#       when the object is added to the layout. For instance:
#       dict(WIDGET=gui.QPushButton("Close"), init=lambda d: d.clicked.connect(sys.exit))
#       creates a close button whose clicked signal is connected to the sys.exit method. Clicking this button will
#       close the application and end the script


####

# a dict of dicts: {<type> : {get : <attr>, set : <attr>, changed : <signal>}
# default getters, setters, and changed signals for types of UI elements accessed with get_(), set_(*args, **kwargs),
# and changed_, respectively

PROPERTIES = {
    gui.QLabel: dict(get=gui.QLabel.text, set=gui.QLabel.setText),
    gui.QLineEdit: dict(get=gui.QLineEdit.text, set=gui.QLineEdit.setText, changed='textChanged'),
    gui.QPlainTextEdit: dict(get=gui.QPlainTextEdit.toPlainText, set=gui.QPlainTextEdit.setPlainText,
                             changed='textChanged'),
    gui.QRadioButton: dict(get=gui.QRadioButton.isChecked,
                           set=lambda radiobutton, value: radiobutton.setChecked(make_bool(value)),
                           changed='toggled'),
    gui.QCheckBox: dict(get=gui.QCheckBox.isChecked, set=lambda checkbox, value: checkbox.setChecked(make_bool(value)),
                        changed='toggled'),
    gui.QComboBox: dict(get=gui.QComboBox.currentText,
                        set=lambda combobox, qstr: combobox.setCurrentIndex(combobox.findText(qstr)),
                        changed='currentTextChanged'),
    gui.QListWidget: dict(get=gui.QListWidget.currentItem,
                          set=lambda listwidget, qstr: listwidget.setCurrentItem(
                              listwidget.findItems(qstr, core.Qt.MatchExactly)[0]),
                          changed='currentTextChanged'),
    gui.QSpinBox: dict(set=lambda spinbox, value: spinbox.setValue(int(value)), get=gui.QSpinBox.value,
                       changed='valueChanged'),
    gui.QDoubleSpinBox: dict(set=lambda spinbox, value: spinbox.setValue(float(value)), get=gui.QDoubleSpinBox.value,
                             changed='valueChanged')
}


def make_bool(value):
    if isinstance(value, str):
        return value == 'True'
    else:
        return bool(value)


class DuplicateNameError(Exception):  # error raised if there are item name conflicts
    def __init__(self, txt):
        Exception.__init__(self, txt)


class AutoLayoutItem:
    """Used to parse and wrap the dicts the user will provide"""

    def __init__(self, item):
        self.type = None  # type: str
        self.item = None
        self.name = None  # type: str
        self.init = None  # type: function

        self._parse(item)

    def _parse(self, item):
        """Does basic key validation to make sure there is only one type, etc.
        Further attributes will be validated later by each individual layout type"""

        if item is None:
            self.type = 'stretch'
            return
        if isinstance(item, str):
            self.type = 'widget'
            self.item = gui.QLabel(item)
            return
        elif isinstance(item, dict):

            # get item type
            keylist = [k for k in item.keys() if k.isupper()]
            if len(keylist) != 1:
                raise ValueError('Must have exactly one key in all caps for item type')

            # set item
            self.type = keylist[0].lower()
            self.item = item[keylist[0]]

            # set the rest of the attributes
            for k, v in item.items():
                setattr(self, k, v)
        else:
            raise TypeError('Bad argument type: expected str, NoneType, or dict, received \'{}\''.format(type(item)))


class AutoGridLayoutItem(AutoLayoutItem):
    """Layout item for gridlayouts -- adds a few attributes"""

    def __init__(self, item):
        self.row = None  # type: int
        self.col = None  # type: int
        self.align = None  # type: int
        self.label = None  # type: str

        AutoLayoutItem.__init__(self, item)


class AutoLayout:
    """Base class for all autolayouts, should not be instantiated"""

    def __init__(self):
        self.layout_items: list = None
        self.names = dict()
        self.item_type = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _populate(self, item_type: type, *items):

        self.item_type = item_type

        try:
            items = [item_type(item) for item in items]
        except TypeError as e:
            print(e, 'Failed to create layout items from args -- bad type')

        for item in items:
            try:  # default validation takes place using the item attributes below
                self.validate_item(item, ITEM_ATTRIBUTES[item.type])
            except KeyError:
                pass  # if the type is not in ITEM_TYPES, just pass over it by default

            self.add_item(item)

        # turn names into attributes
        for k, v in self.names.items():
            if k:
                if hasattr(self, k):
                    raise ValueError(
                        """Attribute '{}' already exists for this object -- please pick a different name.""".format(k))
                else:
                    setattr(self, k, v)

    def validate_item(self, item, attributes):  # type: (AutoLayoutItem, dict) -> None
        """Used to validate the presence and types of attributes provided in layout items"""
        for k, t in attributes.items():
            try:
                if not isinstance(getattr(item, k), attributes[k]):
                    err = """Invalid type provided for attribute '{}' in {}; expected {}, got {}""" \
                        .format(k, self.__class__, t, type(getattr(item, k)))
                    raise ValueError(err)
            except KeyError:
                """Missing attribute '{}' for type '{}' in {}""".format(k, item.type, self.__class__)

    def add_item(self, item, *args, **kwargs):  # type: (AutoLayoutItem) -> None

        if isinstance(item, dict):
            self._populate(self.item_type, item)

        # work by item type
        if item.type == 'stretch':
            self.addStretch(1, *args, **kwargs)
            return
        elif item.type == 'widget':
            # set get/set/changed attributes
            # getter
            if hasattr(item, 'get'):
                setattr(item.item, 'get_', lambda *a, **kw: item.get(item.item, *a, *kw))
            elif hasattr(item.item, 'get'):
                setattr(item.item, 'get_', item.item.get)
            elif type(item.item) in PROPERTIES and 'get' in PROPERTIES[type(item.item)]:
                setattr(item.item, 'get_',
                        lambda *a, **kw: PROPERTIES[type(item.item)]['get'](item.item, *a, **kw))

            # setter
            if hasattr(item, 'set'):
                setattr(item.item, 'set_', lambda *a, **kw: item.set(item.item, *a, *kw))
            elif hasattr(item.item, 'set'):
                setattr(item.item, 'set_', item.item.set)
            elif type(item.item) in PROPERTIES and 'set' in PROPERTIES[type(item.item)]:
                setattr(item.item, 'set_',
                        lambda *a, **kw: PROPERTIES[type(item.item)]['set'](item.item, *a, **kw))

            # changed signal
            if hasattr(item, 'changed'):
                setattr(item.item, 'changed_', item.changed)
            elif hasattr(item.item, 'changed'):
                setattr(item.item, 'changed_', item.item.changed)
            elif type(item.item) in PROPERTIES and 'changed' in PROPERTIES[type(item.item)]:
                setattr(item.item, 'changed_', getattr(item.item, PROPERTIES[type(item.item)]['changed']))

            self.addWidget(item.item, *args, **kwargs)
        elif 'layout' in item.type:
            if item.type == 'vboxlayout':
                item.item = AutoVBoxLayout(*item.item)
            elif item.type == 'hboxlayout':
                item.item = AutoHBoxLayout(*item.item)
            elif item.type == 'formlayout':
                item.item = AutoFormLayout(*item.item)
            elif item.type == 'gridlayout':
                item.item = AutoGridLayout(*item.item)
            elif item.type == 'layout':
                pass

            self.addLayout(item.item, *args, **kwargs)

        # call item's init method, if applicable
        if item.init:
            item.init(item.item)

        # get name or item's names as dict so they can be merged into this layout's names dict
        if item.name:
            new_names = {item.name: item.item}
        else:
            try:
                new_names = item.item.names
            except AttributeError:
                new_names = {}

        # ensure no duplicates exist and add only the ones that aren't None
        for k, v in new_names.items():
            if k and k in self.names.keys():
                raise DuplicateNameError("""Duplicate item name entered: '{}'""".format(k))
            elif k:
                self.names[k] = v

    def get_(self):  # type: () -> dict
        values = dict()
        for field, element in self.names.items():
            try:
                values[field] = element.get_()
            except AttributeError:
                continue

        return values

    def set_(self, **values):  # type: (dict) -> None
        for field, value in values.items():
            try:
                self.names[field].set_(value)
            except (KeyError, AttributeError):
                continue

    # these methods will be overridden by those of QLayout; they're just here as placeholders to prevent
    # some basic runtime exceptions

    @staticmethod
    def addWidget(*args, **kwargs):
        pass

    @staticmethod
    def addLayout(*args, **kwargs):
        pass

    @staticmethod
    def addStretch(*args, **kwargs):
        pass


class AutoBoxLayout(gui.QBoxLayout, AutoLayout):
    """Class for autoboxlayouts -- shouldn't really be initialized but can be if need be"""

    def __init__(self, layout_type, *args):
        gui.QBoxLayout.__init__(self, layout_type().direction())
        AutoLayout.__init__(self)
        self._populate(AutoLayoutItem, *args)

    def add_item(self, item, *args, **kwargs):  # type: (AutoLayoutItem) -> None
        # add the item with alignment and stretch args from the item
        call_args = list()
        if hasattr(item, 'stretch'): call_args.append(item.stretch)
        if item.type == 'widget':
            if hasattr(item, 'align'): call_args.append(item.align)

        AutoLayout.add_item(self, item, *call_args)


class AutoVBoxLayout(AutoBoxLayout):
    def __init__(self, *args):
        AutoBoxLayout.__init__(self, gui.QVBoxLayout, *args)


class AutoHBoxLayout(AutoBoxLayout):
    def __init__(self, *args):
        AutoBoxLayout.__init__(self, gui.QHBoxLayout, *args)


class AutoGridLayout(gui.QGridLayout, AutoLayout):
    """Class for autogridlayouts, both forms and regular"""

    def __init__(self, *args, **kwargs):

        kwargs.setdefault('form', False)
        self.form = kwargs['form']

        gui.QGridLayout.__init__(self)
        AutoLayout.__init__(self)
        self._populate(AutoGridLayoutItem, *args)
        self.setVerticalSpacing(10)

    def add_item(self, item, *args, **kwargs):  # type: (AutoGridLayoutItem) -> None

        if self.form:
            self.validate_item(item, ITEM_ATTRIBUTES['form_element'])
            label = AutoLayoutItem(item.label)
            row = self.rowCount()
            AutoLayout.add_item(self, label, row, 0, core.Qt.AlignRight | core.Qt.AlignTop)
            AutoLayout.add_item(self, item, row, 1)
        else:
            self.validate_item(item, ITEM_ATTRIBUTES['grid_element'])
            call_args = [item.row, item.col]
            if item.align is not None: call_args.append(item.align)
            AutoLayout.add_item(self, item, *call_args)


class AutoFormLayout(AutoGridLayout):
    def __init__(self, *args):
        AutoGridLayout.__init__(self, *args, form=True)


# dict of dicts detailing the necessary attribute for each item type

ITEM_ATTRIBUTES = dict(
    stretch=dict(),
    widget=dict(item=gui.QWidget),
    vboxlayout=dict(item=list),
    hboxlayout=dict(item=list),
    formlayout=dict(item=list),
    gridlayout=dict(item=list),
    form_element=dict(label=str),
    grid_element=dict(row=int, col=int)
)

if __name__ == '__main__':
    app = gui.QApplication(sys.argv)

    w = gui.QWidget()

    layout = AutoVBoxLayout(
        dict(FORMLAYOUT=[
            dict(label='enter input: ', WIDGET=gui.QLineEdit(), name='input')
        ]),
        dict(HBOXLAYOUT=[
            None, dict(WIDGET=gui.QPushButton('Okay'), init=lambda d: d.clicked.connect(w.accept)), None
        ])
    )

    w.setLayout(layout)
    w.exec_()

    print(layout.input.text())

    sys.exit(app.exec_())
