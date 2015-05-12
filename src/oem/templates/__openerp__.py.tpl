# -*- coding: utf-8 -*-
\
# -*- coding: utf-8 -*-

{
    "name": ${repr(name)},
% if description:
    "description": u"""${description}""",
% endif
    "version": "${version}",
% if depends:
    "depends": [
    % for file in depends:
        ${repr(file)},
    % endfor
    ],
% endif
    "author": "${author}",
% if category:
    "category": "${category}",
% endif
% if url:
    "url": "${url}",
% endif
    "installable": ${installable},
% if active:
    "active": ${repr(active)},
% endif
    "data": [
% if data:
    % for file in data:
        ${repr(file)},
    % endfor
% endif
    ],
% if test:
    "test": [
    % for file in test:
        ${repr(file)},
    % endfor
    ],
% endif
% if qweb:
    "qweb": [
    % for file in qweb:
        ${repr(file)},
    % endfor
    ],
% endif
% if js:
    "js": [
    % for file in js:
        ${repr(file)},
    % endfor
    ],
% endif
% if css:
    "css": [
    % for file in css:
        ${repr(file)},
    % endfor
    ],
% endif
% if img:
    "img": [
    % for file in img:
        ${repr(file)},
    % endfor
    ],
% endif
}
