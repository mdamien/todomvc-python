import micropip
from js import document

STATE = {
    'todos': [],
    'filter': 'all',
}

def render(*args):
    remaining = 4
    completed = 2

    from lys import L, render as lys_render
    document.getElementById('app').innerHTML = lys_render((
        L.header('.header') / (
            L.h1 / 'todos',
            L.input('.new-todo', placeholder="What needs to be done?", autofocus=''),
        ),
        L.section('.main') / (
            L.input('.toggle-all', type="checkbox"),
            L.label(**{'for':"toggle-all"}) / 'Mark all as complete',
        ),
        L.ul('.todo-list') / (
            L.li / (
                L.input('.toggle', type="checkbox"),
                L.label / "<title>",
                L.button('.destroy'),
            ),
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
    ))

micropip.install('lys').then(render)