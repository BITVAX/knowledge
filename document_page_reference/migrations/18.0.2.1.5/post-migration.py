# Copyright 2026 TRIVAX INNOVA SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # The stored index of a category did not follow its children until
    # 18.0.2.1.5: rebuild it for every existing category.
    categories = env["document.page"].search([("type", "=", "category")])
    categories._compute_content_parsed()
    categories.flush_recordset(["content_parsed"])
