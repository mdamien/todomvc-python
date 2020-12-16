### lys (templating engine) ###
from js import document
import html, types, keyword, sys, re


VOID_TAGS = [
    'area', 'base', 'br', 'col', 'embed', 'hr',
    'img', 'input', 'keygen', 'link', 'meta',
    'param', 'source', 'track', 'wbr'
]


class LysException(Exception):
    """Base exception class for all Lys related errors"""


def lys_render(node):
    """Render a node or a node list to an HTML node"""
    if node is None:
        return document.createTextNode('')
    elif type(node) is LysRawNode:
        span = document.createElement('span')
        span.innerHTML = node.content
        return span
    elif type(node) in (tuple, list, types.GeneratorType):
        span = document.createElement('span')
        for child in node:
            span.appendChild(lys_render(child))
        return span
    elif type(node) is str:
        span = document.createElement('span')
        span.innerHTML = html.escape(node)
        return span
    else:
        node_rendered = document.createElement(node.tag)
        if node.attrs:
            for k, v in node.attrs.items():
                if k.startswith('on') and callable(v):
                    node_rendered.addEventListener(k[2:].lower(), v)
                else:
                    node_rendered.setAttribute(k, v)
        if node.children:
            node_rendered.appendChild(lys_render(node.children))
        return node_rendered


class LysNode:
    """An HTML node"""
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = attrs
        self.children = children

    def __call__(self, _shortcut=None, **attrs):
        """Return a new node with the same tag but new attributes"""
        def clean(k, v):
            if v and type(v) not in (str, LysRawNode) and not callable(v):
                raise LysException('Invalid attribute value "{}"'
                    ' for key "{}"'.format(v, k))
            # allow to use reserved keywords as: class_, for_,..
            if k[-1] == '_' and k[:-1] in keyword.kwlist:
                k = k[:-1]
            # replace all '_' with '-'
            return k.replace('_', '-')
        attrs = {clean(k, v): v for k, v in attrs.items()}

        # process given shorcut strings like '#my_id.a_class.another_class'
        if _shortcut:
            def raise_if_bad_name(name, type='class'):
                # TODO: regex to verify if valid class name
                if ' ' in name or '.' in name or ',' in name:
                    raise LysException('"{}" is an invalid {} name'.format(name, type))
                return name
            classes = _shortcut.split('.')
            # add #id if there is one
            if classes[0] and classes[0][0] == '#':
                attrs['id'] = raise_if_bad_name(classes[0][1:], 'id')
                classes = classes[1:]
            # add classes to the current class
            current_classes = attrs.get('class', '').split(' ')
            new_classes = [raise_if_bad_name(klass) for klass in current_classes + classes if klass]
            if new_classes:
                attrs['class'] = ' '.join(new_classes)

        return LysNode(self.tag, attrs)

    def __truediv__(self, children):
        """Mark a list or one node as the children of this node"""
        if self.tag in VOID_TAGS:
            raise LysException('<{}> can\'t have children nodes'.format(self.tag))
        if self.children and len(self.children) == 1:
            self.children = (self.children[0] / children,)
        else:
            if type(children) not in (tuple, list):
                children = (children,)
            self.children = children
        return self

    def __str__(self):
        return lys_render(self)

    def __repr__(self):
        return 'Node(tag={}, attrs={}, children={})'.format(self.tag,
                    self.attrs, self.children)


class LysRawNode(object):
    """Node marked as already escaped"""
    def __init__(self, content):
        self.content = content

    def __str__(self):
        return self.content


def lys_raw(content):
    """Mark a string as already escaped"""
    return LysRawNode(content)


class _L:
    def __getattr__(self, tag):
        return LysNode(tag)
L = _L()


### app ###

STATE = {
    'todos': [],
    'filter': 'all',
}


ID_COUNTER = 0
def generate_id():
    global ID_COUNTER
    ID_COUNTER += 1
    return ID_COUNTER


def new_todo(evt):
    if evt.key != "Enter":
        return
    STATE['todos'] = [{
        'id': generate_id(),
        'title': evt.target.value,
        'completed': False,
    }] + STATE['todos']
    render()


def render():
    remaining = len([todo for todo in STATE['todos'] if not todo['completed']])
    completed = len([todo for todo in STATE['todos'] ifss todo['completed']])

    document.getElementById('app').innerHTML = ''
    document.getElementById('app').appendChild(lys_render((
        L.header('.header') / (
            L.h1 / 'todos',
            L.input('.new-todo', placeholder="What needs to be done?", autofocus='', onkeyup=new_todo),
        ),
        L.section('.main') / (
            L.input('.toggle-all', type="checkbox"),
            L.label(**{'for':"toggle-all"}) / 'Mark all as complete',
        ),
        L.ul('.todo-list') / (
            (
                L.li / (
                    L.input('.toggle', type="checkbox"),
                    L.label / todo['title'],
                    L.button('.destroy'),
                )
            ) for todo in STATE['todos']
        ),
        L.footer('.footer') / (
            L.span('.todo-count') / (
                L.strong / f"{remaining} ",
                f"{'item' if remaining == 1 else 'items'} left",
            ),
            L.ul('.filters') / (
                L.li / L.a('.selected', href="#/") / 'All',
                L.li / L.a(href="#/active") / 'Active',
                L.li / L.a(href="#/completed") / 'Completed',
            ),
            (L.button('.clear-completed') / 'Clear completed') if completed else None,
        ),
    )))

render()