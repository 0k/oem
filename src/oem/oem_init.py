# -*- coding: utf-8 -*-

import os
import re
from collections import OrderedDict

import sact.epoch
from cookiecutter import main as cc

import kids.cfg
from kids.cmd import cmd, msg
from kids.data.mdict import mdict
from kids.vcs import GitConfig
from kids.sh import ShellError


from . import common


DEFAULT_TEMPLATE = os.environ.get("OEM_INIT_TEMPLATE",
                                  'gh:0k/cookiecutter-odoo')
AUTHOR_REGEX = re.compile(r'^(?P<name>[^<]+)<(?P<email>[^> ]+)>$')


def get_git_author(path=None):
    ## try git in last resort
    try:
        git_cfg = GitConfig(path)
        email = git_cfg.get('user.email')
        author = git_cfg.get('user.name')
    except ShellError as e:
        email = None
        author = None
    if email and author:
        return "%s <%s>" % (author, email)
    return None


@cmd
def Command(path=None, template=None, flavor=None, prompt=False,
            author=None, license_years=None, module_version=None,
            website=None):
    """Initialise a module by populating a directory

    Will populate specified path (or current path if not
    specified) with OpenERP/Odoo modules files and directory
    structure.

    Usage:
      %(std_usage)s
      %(surcmd)s [PATH] [--template=TEMPLATE] [--flavor=FLAVOR]
          [--prompt|-p] [--author=AUTHOREMAIL] [--license-years=YEARS]
          [--module-version VERSION] [--website WEBSITE]

    Options:
      %(std_options)s
      PATH                If not specified, equivalent to "."
      --template TEMPLATE      Advanced cookiecutter template.
      --flavor FLAVOR          Target template version (ie: 8.0, 7.0)
                               (default: master)
      --prompt, -p             Prompt for all values, except those provided on
                               the command line. And values from config files.
      --author AUTHOREMAIL     Author name and email. Default taken in config.
                               (ie: 'Robert Dubois <robert.dubois@mail.com>')
      --license-years YEARS    License applicable years. (ie: 2010-2012, 2013)
                               (defaults to current year)
      --module-version VERSION Starting version number
      --website WEBSITE        Website of the module.

    """

    cfg = kids.cfg.load()

    path = os.getcwd() if path is None else os.path.abspath(path)
    root = common.find_root(path)

    if root:
        msg.die("Module %r already initialized." % root)

    name = os.path.basename(path)
    output_dir = os.path.dirname(path)

    if not os.path.isdir(output_dir):
        msg.die("Destination directory %r doesn't exists." % (output_dir, ))

    if template is None:
        template = mdict(cfg).get("init.template", DEFAULT_TEMPLATE)

    ## Command line provided values
    cli_values = {"name": name}
    default_values = {}

    dct = default_values if author is None else cli_values
    if author is None:
        author = mdict(cfg).get("author")
        if author is None and not os.environ.get("NO_GIT_CONFIG", ""):
            author = get_git_author(path)
        if author is None:
            msg.die(
                "No author found on command line nor in config files.\n"
                "Please provide an author with '--author=', for instance:\n\n"
                "  oem init --author='Robert Dubois <robert.dubois@mail.com>'"
                "\n\nor set a default author in your config file before "
                "running this command:\n\n"
                "  oem config set author 'Robert Dubois <robert.dubois@mail.com>'"
                "\n\nor set a default author in your git config like this:"
                "\n\n"
                "  git config --global user.name 'Robert Dubois'\n"
                "  git config --global user.email 'robert.dubois@mail.com'\n")

    match = AUTHOR_REGEX.search(author)
    if not match:
        msg.die(
            "Your value %r for 'author' doesn't match specs.\n"
            "You should try to match this example:\n\n"
            "    Robert Dubois <robert.dubois@mail.com>"
            % (author, ))
    match = match.groupdict()
    dct["author"] = match["name"].strip()
    dct["email"] = match["email"]

    if license_years is None:
        license_years = sact.epoch.Time.now().strftime('%Y')
        default_values["license_years"] = license_years
    else:
        cli_values["license_years"] = license_years

    if module_version is None:
        module_version = '0.1'
        default_values["version"] = module_version
    else:
        cli_values["version"] = module_version

    if website is not None:
        cli_values["website"] = website

    ## A big part of the following code comes directly from
    ## cookiecutter, and I would be glad that some of the
    ## functionality I implemented would come in a way or another
    ## in cookiecutter itslef.

    # Get user config from ~/.cookiecutterrc or equivalent
    # If no config file, sensible defaults from config.DEFAULT_CONFIG are used
    config_dict = cc.get_user_config()

    template = cc.expand_abbreviations(template, config_dict)

    # TODO: find a better way to tell if it's a repo URL
    if 'git@' in template or 'https://' in template:
        repo_dir = cc.clone(
            repo_url=template,
            checkout=flavor,
            clone_to_dir=config_dict['cookiecutters_dir'],
            no_input=True
        )
    else:
        # If it's a local repo, no need to clone or copy to your
        # cookiecutters_dir
        repo_dir = template

    context_file = cc.find_cfg_file(repo_dir)

    default_context = config_dict.get('default_context', {})
    if default_values:
        default_context.update(default_values)
    context = cc.generate_context(
        context_file=context_file,
        default_context=default_context,
        extra_context=config_dict,
    )

    context = cc.prompt_for_config(
        context,
        no_input=False,
        values=cli_values,
        only_missing=not prompt,
        with_optional=prompt)

    ## XXXvlab: missing no-overwrite mode
    # Create project from local context and project template.
    if not os.environ.get("OEM_DRY_RUN", ""):
        cc.generate_files(
            repo_dir=repo_dir,
            context=context,
            output_dir=output_dir)
