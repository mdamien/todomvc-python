### lys (templating engine) ###
from js import React, ReactDOM
import html, types, keyword


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
        return None
    elif type(node) is LysRawNode:
        return React.createElement('span', {
            'dangerouslySetInnerHTML': {
                '__html': node.content
            }
        })
    elif type(node) in (tuple, list, types.GeneratorType):
        return React.createElement('span', None, [lys_render(child) for child in node])
    elif type(node) is str:
        return React.createElement('span', None, node)
    else:
        return React.createElement(node.tag, node.attrs, lys_render(node.children))


class LysNode:
    """An HTML node"""
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = attrs
        self.children = children

    def __call__(self, _shortcut=None, **attrs):
        """Return a new node with the same tag but new attributes"""
        def clean(k, v):
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
                attrs['className'] = ' '.join(new_classes)

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
import js
from js import document, localStorage, location, window

import json


STATE = {
    'todos': [],
}


def _remaining():
    return len([todo for todo in STATE['todos'] if not todo['completed']])


def _get_todo_by_id(id):
    return [todo for todo in STATE['todos'] if todo['id'] == id][0]


def new_todo(evt):
    if evt.key != "Enter":
        return
    if not evt.target.value:
        return
    STATE['todos'] = [{
        'title': evt.target.value,
        'completed': False,
        'editing': False,
    }] + STATE['todos']
    evt.target.value = ''
    save_and_render()


def toggle_all(evt):
    for todo in STATE['todos']:
        todo['completed'] = evt.target.checked
    save_and_render()


def toggle(todo):
    todo['completed'] = not todo['completed']
    save_and_render()


def destroy(removed_todo):
    STATE['todos'] = [todo for todo in STATE['todos'] if todo is not removed_todo]
    save_and_render()


def enter_editing_mode(todo):
    todo['editing'] = True
    save_and_render()


def exit_editing_mode(evt, todo):
    if evt.key != "Enter":
        return
    if not todo['title']:
        destroy(todo)
        return
    todo['editing'] = False
    save_and_render()


def update_title(evt, todo):
    todo['title'] = evt.target.value
    save_and_render()


def clear_completed(evt):
    STATE['todos'] = [todo for todo in STATE['todos'] if not todo['completed']]
    save_and_render()


def render_todo(todo):
    return L.li('.editing' if todo['editing'] else '' + '.completed' if todo['completed'] else '') / (
        L.div('.view') / (
            L.input('.toggle', type="checkbox", checked=todo['completed'],
                onChange=lambda evt: toggle(todo)),
            L.label(onClick=lambda evt: enter_editing_mode(todo)) / todo['title'], # TODO: double click
            L.button('.destroy', onClick=lambda evt: destroy(todo)),
        ),
        L.input('.edit', value=todo['title'],
            onChange=lambda evt: update_title(evt, todo),
            onKeyUp=lambda evt: exit_editing_mode(evt, todo))
    )


def save_and_render():
    localStorage.setItem('app', json.dumps(STATE))
    render()


def render():
    total = len(STATE['todos'])
    remaining = _remaining()
    completed = total - remaining

    filter = location.hash.replace('#', '')
    if not filter:
        filter = 'all'

    if filter == 'active':
        todos_to_render = [todo for todo in STATE['todos'] if not todo['completed']]
    elif filter == 'completed':
        todos_to_render = [todo for todo in STATE['todos'] if todo['completed']]
    else:
        todos_to_render = STATE['todos']

    todos = []
    for todo in todos_to_render:
        todos.append(render_todo(todo))

    rendered = lys_render((
        L.header('.header') / (
            L.h1 / 'todos',
            L.input('.new-todo', placeholder="What needs to be done?", autoFocus='', onKeyUp=new_todo),
        ),
        L.section('.main') / (
            L.input('#toggle-all.toggle-all', type="checkbox", onChange=toggle_all,
                checked=remaining == 0 and total > 0),
            L.label(htmlFor="toggle-all") / 'Mark all as complete',
        ),
        L.ul('.todo-list') / todos,
        L.footer('.footer') / (
            L.span('.todo-count') / (
                L.strong / f"{remaining} ",
                f"{'item' if remaining == 1 else 'items'} left",
            ),
            L.ul('.filters') / (
                L.li / L.a('.selected' if filter == 'all' else '', href="#") / 'All',
                L.li / L.a('.selected' if filter == 'active' else '', href="#active") / 'Active',
                L.li / L.a('.selected' if filter == 'completed' else '', href="#completed") / 'Completed',
            ),
            (L.button('.clear-completed', onClick=clear_completed) / 'Clear completed') if completed else None,
        ),
    ))

    ReactDOM.render(
      rendered,
      document.getElementById('app')
    );


if localStorage.getItem('app'):
    STATE = json.loads(localStorage.getItem('app'))

render()
window.addEventListener('hashchange', lambda *args: render())