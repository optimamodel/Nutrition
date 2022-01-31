"""
Manage Project versions and migration

Migration refers to updating old instances so that they
can be run with more recent versions of the code. This module defines

- A set of 'migration functions' that each transform an instance from one
  version to another
- An entry-point that sequentially calls the migration functions to update a project to
  the latest version

"""

import sys
import io
from distutils.version import LooseVersion

import nutrition.settings
from .version import version, gitinfo
import sciris as sc
import types
import numpy as np
import pandas as pd
from collections import defaultdict
import pathlib
import os
from . import logger
from .utils import get_translator

__all__ = ["migration", "migrate", "register_migration"]

SKIP_MIGRATION = False  # Global migration flag to disable migration

# MODULE MIGRATION
#
# If any modules have been removed, or if any classes need remapping, that can be done here.
# See `migration.py` in Atomica for examples

# On Windows, pathlib.PosixPath is not implemented which can cause problems when unpickling
# Therefore, we need to turn PosixPath into WindowsPath on loading. The reverse is true on
# Unix systems
if os.name == "nt":
    pathlib.PosixPath = pathlib.WindowsPath
else:
    pathlib.WindowsPath = pathlib.PosixPath


class _Placeholder:
    pass


# MIGRATIONS
#
# The remaining code manages upgrading Project objects and their contents after they
# have been unpickled and instantiated


class Migration:
    """Class representation of a migration

    This class stores a migration function together with all required metadata. It would
    normally be instantiated using the `migration` decorator, which also registers the
    migration by adding it to the `migrations` list

    """

    def __init__(self, classname, original_version, new_version, description, fcn, date=None, update_required=False):
        """

        :param original_version:
        :param new_version:
        :param description:
        :param fcn:
        :param date:
        :param update_required: Flag if dependent content in the object might change e.g. if redoing a calculation might produce different results
        """
        self.classname = classname
        self.original_version = original_version
        self.new_version = new_version
        self.description = description
        self.update_required = update_required
        self.date = date
        self.fcn = fcn

    def upgrade(self, obj):
        logger.debug("MIGRATION: Upgrading %s %s -> %s (%s)" % (self.classname, self.original_version, self.new_version, self.description))
        obj = self.fcn(obj)  # Run the migration function
        if obj is None:
            raise Exception("%s returned None, it is likely missing a return statement" % (str(self)))
        obj.version = self.new_version  # Update the version
        if self.update_required:
            obj._update_required = True
        return obj

    def __repr__(self):
        return f"Migration({self.classname}, {self.original_version}->{self.new_version})"


def register_migration(registry, classname, original_version, new_version, description, date=None, update_required=False):
    """Decorator to register migration functions

    This decorator constructs a `Migration` object from a decorated migration function, and registers it
    in the module's list of migrations to be run when calling migrate()

    :param registry: Dictionary storing {classname:[migrations]}
    :param original_version: Version string for the start version. Function will only run on projects whose version is <= this
    :param new_version: The resulting project is assigned this version
    :param description: A brief overview of the purpose of this migration
    :param date: Optionally specify the date when this migration was written
    :param update_required: Optionally flag that changes to model output may occur - the flag is stored in the object's `_update_required` attribute.
                            Objects can optionally contain this attribute, so it's not necessary if the object is planned not to require
                            such a flag.
    :return: None

    Example usage::

        @migration('Project','1.0.0', '1.0.1', 'Upgrade project', update_required=True)
        def _update_project(proj):
            ...
            return proj

    The migration function (update_project()) takes a single argument which is a project object, and returns
    a project object. Decorating the function registers the migration and it will automatically be used by
    migrate() and therefore Project.load()

    """

    def register(f):
        if classname not in registry:
            registry[classname] = []
        registry[classname].append(Migration(classname, original_version, new_version, description, fcn=f, date=date, update_required=update_required))
        return f

    return register


migrations = dict()  # Registry of migrations in Optima Nutrition


def migration(*args, **kwargs):
    # Wrapper decorator to bind register_migration to the migration registry in this module
    return register_migration(migrations, *args, **kwargs)


def migrate(obj, registry=migrations, version=version, gitinfo=gitinfo):
    """Update a object to the latest version

    Run all of the migrations in the list of available migrations. The migrations are run in ascending order, as long
    as the version is <= the migration's original version. This way, migrations don't need to be added if a version number
    change takes place without actually needing a migration - instead, when adding a migration, just use whatever version
    numbers are appropriate at the time the change is introduced, it will behave sensibly.

    Typically, this function would not be called manually - it happens automatically as part of `Project.load()`.

    Note that this function returns the updated object. Typically the migration functions will update a
    object in-place, but this syntax allows migrations to replace parts of the object (or the entire object)
    if that is ever necessary in the future. So do not rely on `migrate` having side-effects, make sure the
    returned object is retained. In principle we could dcp() the object to ensure that only the
    copy gets migrated, but at this point it does not appear worth the performance overhead (since migration at the
    moment is only ever called automatically).

    :param proj: object to migrate
    :param version: The current version
    :param gitinfo: The current gitinfo (usually corresponds to the result of `sc.gitinfo()`)
    :return: Updated object

    """

    if type(obj).__name__ not in registry:
        return obj  # If there are no migrations for the object, then return immediately

    elif not hasattr(obj, "version"):
        # If the object has no version attribute, then add one with version 0. This is presumably
        # because the original object didn't have a version, but now migrations for it are required.
        # In that case, any object that doesn't have a version would require all migrations to be run.
        # New objects would all have a version already. After any migrations are run, these values will
        # then be updated to the current version
        obj.version = "0.0.0"
        obj.gitinfo = None

    if SKIP_MIGRATION:
        print("Skipping migration")
        return obj  # If migration is disabled then don't make any changes EXCEPT to add in version and gitinfo which may otherwise be hard to catch

    migrations_to_run = sorted(registry[type(obj).__name__], key=lambda m: LooseVersion(m.original_version))
    if sc.compareversions(obj.version, version) >= 0:
        return obj
    else:
        if hasattr(obj, "name"):
            logger.info('Migrating %s "%s" from %s->%s', type(obj).__name__, obj.name, obj.version, version)
        else:
            logger.info("Migrating %s from %s->%s", type(obj).__name__, obj.version, version)

    for m in migrations_to_run:  # Run the migrations in increasing version order
        if sc.compareversions(obj.version, m.new_version) < 0:
            obj = m.upgrade(obj)

    obj.version = version  # Set object version to the current Atomica version
    obj.gitinfo = gitinfo  # Update gitinfo to current version
    if hasattr(obj, "_update_required") and obj._update_required:
        logger.warning("Caution: due to migration, object may behave different if re-run.")
    return obj


@migration("Project", "1.7.2", "1.7.6", "Add locale")
def _add_project_locale(proj):
    if not hasattr(proj, "locale"):
        proj.locale = "en"
    return proj


@migration("InputData", "1.7.2", "1.7.6", "Add locale")
def _add_inputdata_locale(inputdata):
    if not hasattr(inputdata, "locale"):
        inputdata.locale = "en"
    return inputdata


@migration("ProgData", "1.7.2", "1.7.6", "Add locale")
def _add_progdata_locale(progdata):
    if not hasattr(progdata, "locale"):
        progdata.locale = "en"
    return progdata


@migration("Settings", "1.7.6", "1.7.7", "Add cost types")
def _add_cost_types(settings):
    if not hasattr(settings, "cost_types"):
        new = nutrition.settings.Settings(settings.locale)
        settings.cost_types = new.cost_types
    return settings


@migration("Optim", "1.7.9", "1.7.10", "Add optim UUID")
def _add_optim_uid(optim):
    if not hasattr(optim, "uid"):
        optim.uid = sc.uuid()
    return optim


@migration("Scen", "1.7.9", "1.7.10", "Add optim UUID to scen")
def _add_scen_optim_uid(scen):
    if not hasattr(scen, "_optim_uid"):
        scen._optim_uid = None
    return scen


@migration("Scen", "1.7.10", "1.7.11", "Remove active")
def _scen_remove_active(scen):
    if hasattr(scen, "active"):
        delattr(scen, "active")
    return scen


@migration("Optim", "1.7.10", "1.7.11", "Remove active")
def _optim_remove_active(optim):
    if hasattr(optim, "active"):
        delattr(optim, "active")
    return optim

@migration("Project", "1.7.12", "1.7.14", "Clear WB cache")
def _clear_workbook_cache(proj):
    for ss in proj.spreadsheets.values():
        ss.wb = None
    return proj