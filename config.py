from CTFd.plugins.challenges import CTFdStandardChallenge
from CTFd.plugins.CTFd_DynamicValueChallenge import DynamicValueChallenge


def config(app):

    app.config["PLUGIN_FIRSTBLOOD_CHALLENGES"] = [
        CTFdStandardChallenge,
        DynamicValueChallenge,
    ]

    app.config["PLUGIN_FIRSTBLOOD_AWARD_DESCRIPTION"] = \
        """The first blood award, is given to the first team that solves a given
        challenge."""

    app.config["PLUGIN_FIRSTBLOOD_AWARD_VALUE"] = 1

    app.config["PLUGIN_FIRSTBLOOD_AWARD_ICON"] = \
        "http://icons.iconarchive.com/icons/custom-icon-design/pretty-office-11/64/number-1-icon.png"
