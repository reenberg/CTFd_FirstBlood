import os
import sys
from flask import current_app as app, session
from sqlalchemy import select, exists, func, literal
from CTFd.models import db, Awards, Challenges
from CTFd import utils

from config import config


PLUGIN_FOLDER = os.path.basename(os.path.dirname(__file__))


def on_challenge_pre_solve(ns):
    """Event handler for all configured challenges 'challenge.onPreSolve'.  This
    will try and award first blood, if no one else have solved the assignment
    yet.

    """
    # SQLite3 can easily do SELECT ... WHERE, without a FROM clause[1], and
    # PostgreSQL seems to also easily handle this[3].  However in MySQL you
    # can't have a WHERE clause without also having a FROM[2]!  In this case you
    # have to select from the dummy DUAL table (or any other table, with the
    # issues that bring): "FROM DUAL could be used when you only SELECT computed
    # values, but require a WHERE clause, [...]"[4].  The DUAL table is a
    # concept introduced by ORACLE, where you _always_ need to have a FROM
    # clause[5].
    #
    #
    # [1]: https://sqlite.org/syntax/select-core.html
    # [2]: https://mariadb.com/kb/en/library/select/
    # [3]: https://www.postgresql.org/docs/current/static/sql-select.html
    # [4]: https://mariadb.com/kb/en/library/dual/
    # [5]: https://en.wikipedia.org/wiki/DUAL_table#Example_use

    # Get the core Table version of the ORM Awards model.
    awards = Awards.__table__

    award_name = "First Blood for {}/{}".format(ns.chal.category, ns.chal.name)
    award_category = "FirstBlood"

    # Column to value mapping.  This makes the SQL below easier to read.
    data = [
        (awards.c.teamid,   session['id']),
        (awards.c.name,     award_name),
        (awards.c.description, app.config["PLUGIN_FIRSTBLOOD_AWARD_DESCRIPTION"]),
        # (awards.c.date, ),  # It will automatically set the date to now()
        (awards.c.value,    app.config["PLUGIN_FIRSTBLOOD_AWARD_VALUE"]),
        (awards.c.category, award_category),
        (awards.c.icon,     app.config["PLUGIN_FIRSTBLOOD_AWARD_ICON"]),
    ]

    a = awards.insert().from_select(
        names=[col for col, _ in data],
        # Select the scalar values we want to insert, instead of just inserting
        # them directly.  This allows us to return an empty set of values if our
        # condition is false (i.e., we have already awarded first blood for this
        # challenge).
        select=select([literal(value) for _, value in data])
        # Mysql _needs_ a FROM clause when we also use a WHERE clause :( Thus we
        # select the literals from the challenges table (with a limit of 1 --
        # any table that we know has at least one row could be used), as we know
        # that this table must have at least one row, since we are trying to
        # solve a challenge.
        .select_from(Challenges.__table__).limit(1)
        .where(~exists(
            # Only select the scalar value, if there previously is no 'First
            # Blood' awards for this challenge
            awards.select()
            .where((awards.c.name == award_name) & (awards.c.category == award_category))
        ))
    )

    # Session.execute is executed within the current transactional context of
    # the `Session` and thus also the connection (as this is where the
    # transaction is managed -- `Session` is basically a wrapper around the
    # `Connection` and transaction in the "ORM realm").  flask-sqlalchemy runs
    # every request in a transaction, and we really _want_ this query to be
    # executed and persistent instantly, before some other connection make the
    # same query.  So we need to go directly down to the engine, and execute our
    # query, in order to get a new connection without a transaction.
    res = db.session.connection().engine.execute(a)
    if res.rowcount:
        # We inserted columns into the db.

        # XXX: We could returns "First-Blood" as the status of the solve,
        # instead of "Correct".
        pass


def load(app):
    """Plugin initialisation code.

    Called by `CTFd.plugins.init_plugins()` when iterating over all available
    plugins.

    """
    print(" * Loading module, %s" % PLUGIN_FOLDER)
    config(app)

    print >> sys.stderr, "   - Classes:", app.config["PLUGIN_FIRSTBLOOD_CHALLENGES"]
    for chal_cls in app.config["PLUGIN_FIRSTBLOOD_CHALLENGES"]:
        # Register an event listener on the desired classes
        print >> sys.stderr, "   - Registering FirstBlood event handlers for %s" % chal_cls
        chal_cls.ee.on("challenge.onPreSolve", on_challenge_pre_solve)
